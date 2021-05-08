from django.conf import settings
import pika
import logging
import simplejson
import random
import time
from collections import defaultdict

# This simple queuing library doesn't expose much of the power of
# rabbitmq/pika's queuing system; its purpose is to just provide an
# interface for external files to put things into queues and take them
# out from bots without having to import pika code all over our codebase.
class SimpleQueueClient(object):
    def __init__(self):
        self.log = logging.getLogger('humbug.queue')
        self.queues = set()
        self.channel = None
        self.consumers = defaultdict(set)
        self._connect()

    def _connect(self):
        self.connection = pika.BlockingConnection(self._get_parameters())
        self.channel    = self.connection.channel()
        self.log.info('SimpleQueueClient connected')

    def _reconnect(self):
        self.connection = None
        self.channel = None
        self.queues = set()
        self._connect()

    def _get_parameters(self):
        return pika.ConnectionParameters('localhost',
            credentials = pika.PlainCredentials(
                'humbug', settings.RABBITMQ_PASSWORD))

    def _generate_ctag(self, queue_name):
        return "%s_%s" % (queue_name, str(random.getrandbits(16)))

    def _reconnect_callbacks(self):
        for queue, consumers in list(self.consumers.items()):
            for consumer in consumers:
                self.ensure_queue(queue, lambda: self.channel.basic_consume(
                                                        consumer,
                                                        queue=queue,
                                                        consumer_tag=self._generate_ctag(queue)))

    def ready(self):
        return self.channel is not None

    def ensure_queue(self, queue_name, callback):
        '''Ensure that a given queue has been declared, and then call
           the callback with no arguments.'''
        if not self.connection.is_open:
            self._connect()

        if queue_name not in self.queues:
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.queues.add(queue_name)
        callback()

    def publish(self, queue_name, body):
        self.ensure_queue(queue_name,
            lambda: self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                properties=pika.BasicProperties(delivery_mode=2),
                body=body))

    def json_publish(self, queue_name, body):
        try:
            return self.publish(queue_name, simplejson.dumps(body))
        except (AttributeError, pika.exceptions.AMQPConnectionError):
            self.log.warning("Failed to send to rabbitmq, trying to reconnect and send again")
            self._reconnect()

            return self.publish(queue_name, simplejson.dumps(body))

    def register_consumer(self, queue_name, consumer):
        def wrapped_consumer(ch, method, properties, body):
            consumer(ch, method, properties, body)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.consumers[queue_name].add(wrapped_consumer)
        self.ensure_queue(queue_name,
            lambda: self.channel.basic_consume(wrapped_consumer, queue=queue_name,
                consumer_tag=self._generate_ctag(queue_name)))

    def register_json_consumer(self, queue_name, callback):
        def wrapped_callback(ch, method, properties, body):
            return callback(ch, method, properties, simplejson.loads(body))
        return self.register_consumer(queue_name, wrapped_callback)

    def start_consuming(self):
        self.channel.start_consuming()

    def stop_consuming(self):
        self.channel.stop_consuming()

class TornadoQueueClient(SimpleQueueClient):
    # Based on:
    # https://pika.readthedocs.org/en/0.9.8/examples/asynchronous_consumer_example.html

    def _connect(self, on_open_cb = None):
        self.log.info("Beginning TornadoQueueClient connection")
        self._on_open_cb = on_open_cb
        self.connection = pika.adapters.TornadoConnection(
            self._get_parameters(),
            on_open_callback = self._on_open,
            stop_ioloop_on_close = False)

    def _reconnect(self, on_open_cb = None):
        self.connection = None
        self.channel = None
        self.queues = set()
        self._connect(on_open_cb)

    def _on_open(self, connection):
        self.connection.add_on_close_callback(self._on_connection_closed)
        self.connection.channel(
            on_open_callback = self._on_channel_open)

    def _on_channel_open(self, channel):
        self.channel = channel
        if self._on_open_cb:
            self._on_open_cb()
        self.log.info('TornadoQueueClient connected')

    def _on_connection_closed(self, method_frame):
        self.log.warning("TornadoQueueClient lost connection to RabbitMQ, reconnecting...")
        from tornado import ioloop

        # Try to reconnect in two seconds
        retry_seconds = 2
        def on_timeout():
            try:
                self._reconnect(self._reconnect_callbacks)
            except pika.exceptions.AMQPConnectionError:
                self.log.critical("Failed to reconnect to RabbitMQ, retrying...")
                ioloop.IOLoop.instance().add_timeout(time.time() + retry_seconds, on_timeout)

        ioloop.IOLoop.instance().add_timeout(time.time() + retry_seconds, on_timeout)

    def ensure_queue(self, queue_name, callback):
        def finish(frame):
            self.queues.add(queue_name)
            callback()

        if queue_name not in self.queues:
            self.channel.queue_declare(queue=queue_name, durable=True,
                callback=finish)
        else:
            callback()
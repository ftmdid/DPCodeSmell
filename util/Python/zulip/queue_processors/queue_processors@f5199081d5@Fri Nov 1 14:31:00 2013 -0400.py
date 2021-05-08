

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.core.handlers.base import BaseHandler
from postmonkey import PostMonkey, MailChimpException
from zerver.models import get_user_profile_by_email, \
    get_user_profile_by_id, get_prereg_user_by_email, get_client
from zerver.lib.context_managers import lockfile
from zerver.lib.queue import SimpleQueueClient, queue_json_publish
from zerver.lib.timestamp import timestamp_to_datetime
from zerver.lib.actions import handle_missedmessage_emails, do_send_confirmation_email, \
    do_update_user_activity, do_update_user_activity_interval, do_update_user_presence, \
    internal_send_message, send_local_email_template_with_delay, clear_followup_emails_queue, \
    check_send_message, extract_recipients
from zerver.lib.digest import handle_digest_email
from zerver.decorator import JsonableError
from zerver.lib.socket import req_redis_key
from confirmation.models import Confirmation

import os
import sys
import ujson
from collections import defaultdict
import time
import datetime
import logging
import simplejson
import redis
import io

def assign_queue(queue_name, enabled=True):
    def decorate(clazz):
        clazz.queue_name = queue_name
        if enabled:
            register_worker(queue_name, clazz)
        return clazz
    return decorate

worker_classes = {}
def register_worker(queue_name, clazz):
    worker_classes[queue_name] = clazz

def get_worker(queue_name):
    return worker_classes[queue_name]()

def get_active_worker_queues():
    return iter(worker_classes.keys())

class QueueProcessingWorker(object):
    def __init__(self):
        self.q = SimpleQueueClient()

    def consume_wrapper(self, data):
        try:
            self.consume(data)
        except Exception:
            self._log_problem()
            if not os.path.exists(settings.QUEUE_ERROR_DIR):
                os.mkdir(settings.QUEUE_ERROR_DIR)
            fname = '%s.errors' % (self.queue_name,)
            fn = os.path.join(settings.QUEUE_ERROR_DIR, fname)
            line = '%s\t%s\n' % (time.asctime(), ujson.dumps(data))
            lock_fn = fn + '.lock'
            with lockfile(lock_fn):
                with open(fn, 'a') as f:
                    f.write(line)

    def _log_problem(self):
        logging.exception("Problem handling data on queue %s" % (self.queue_name,))

    def start(self):
        self.q.register_json_consumer(self.queue_name, self.consume_wrapper)
        self.q.start_consuming()

    def stop(self):
        self.q.stop_consuming()

@assign_queue('signups')
class SignupWorker(QueueProcessingWorker):
    def __init__(self):
        super(SignupWorker, self).__init__()
        if settings.MAILCHIMP_API_KEY != '':
            self.pm = PostMonkey(settings.MAILCHIMP_API_KEY, timeout=10)

    # Changes to this should also be reflected in
    # zerver/management/commands/enqueue_followup_emails.py:queue()
    def consume(self, data):
        merge_vars=data['merge_vars']
        # This should clear out any invitation reminder emails
        clear_followup_emails_queue(data["EMAIL"], from_email="zulip@zulip.com")
        if settings.MAILCHIMP_API_KEY != '' and settings.DEPLOYED:
            try:
                self.pm.listSubscribe(
                        id=settings.ZULIP_FRIENDS_LIST_ID,
                        email_address=data['EMAIL'],
                        merge_vars=merge_vars,
                        double_optin=False,
                        send_welcome=False)
            except MailChimpException as e:
                if e.code == 214:
                    logging.warning("Attempted to sign up already existing email to list: %s" % (data['EMAIL'],))
                else:
                    raise e
        email = data.get("EMAIL")
        name = merge_vars.get("NAME")
        #Send day 1 email
        send_local_email_template_with_delay([{'email': email, 'name': name}],
                                             "zerver/emails/followup/day1",
                                             {'name': name},
                                             datetime.timedelta(hours=1),
                                             tags=["followup-emails"],
                                             sender={'email': 'wdaher@zulip.com', 'name': 'Waseem Daher'})
        #Send day 2 email
        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        # 11 AM EDT
        tomorrow_morning = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 15, 0)
        assert(datetime.datetime.utcnow() < tomorrow_morning)
        send_local_email_template_with_delay([{'email': email, 'name': name}],
                                             "zerver/emails/followup/day2",
                                             {'name': name},
                                             tomorrow_morning - datetime.datetime.utcnow(),
                                             tags=["followup-emails"],
                                             sender={'email': 'wdaher@zulip.com', 'name': 'Waseem Daher'})

@assign_queue('invites')
class ConfirmationEmailWorker(QueueProcessingWorker):
    def consume(self, data):
        invitee = get_prereg_user_by_email(data["email"])
        referrer = get_user_profile_by_email(data["referrer_email"])
        do_send_confirmation_email(invitee, referrer)

        # queue invitation reminder for two days from now.
        link = Confirmation.objects.get_link_for_object(invitee)
        send_local_email_template_with_delay([{'email': data["email"], 'name': ""}],
                                             "zerver/emails/invitation/invitation_reminder_email",
                                             {'activate_url': link, 'referrer': referrer},
                                             datetime.timedelta(days=2),
                                             tags=["invitation-reminders"],
                                             sender={'email': 'zulip@zulip.com', 'name': 'Zulip'})

@assign_queue('user_activity')
class UserActivityWorker(QueueProcessingWorker):
    def consume(self, event):
        user_profile = get_user_profile_by_id(event["user_profile_id"])
        client = get_client(event["client"])
        log_time = timestamp_to_datetime(event["time"])
        query = event["query"]
        do_update_user_activity(user_profile, client, query, log_time)

@assign_queue('user_activity_interval')
class UserActivityIntervalWorker(QueueProcessingWorker):
    def consume(self, event):
        user_profile = get_user_profile_by_id(event["user_profile_id"])
        log_time = timestamp_to_datetime(event["time"])
        do_update_user_activity_interval(user_profile, log_time)

@assign_queue('user_presence')
class UserPresenceWorker(QueueProcessingWorker):
    def consume(self, event):
        logging.info("Received event: %s" % (event),)
        user_profile = get_user_profile_by_id(event["user_profile_id"])
        client = get_client(event["client"])
        log_time = timestamp_to_datetime(event["time"])
        status = event["status"]
        do_update_user_presence(user_profile, client, log_time, status)

@assign_queue('missedmessage_emails')
class MissedMessageWorker(QueueProcessingWorker):
    def start(self):
        while True:
            missed_events = self.q.drain_queue("missedmessage_emails", json=True)
            by_recipient = defaultdict(list)

            for event in missed_events:
                logging.info("Received event: %s" % (event,))
                by_recipient[event['user_profile_id']].append(event)

            for user_profile_id, events in list(by_recipient.items()):
                handle_missedmessage_emails(user_profile_id, events)

            # Aggregate all messages received every 2 minutes to let someone finish sending a batch
            # of messages
            time.sleep(2 * 60)

def make_feedback_client():
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../api'))
    import zulip
    return zulip.Client(
        email=settings.DEPLOYMENT_ROLE_NAME,
        api_key=settings.DEPLOYMENT_ROLE_KEY,
        verbose=True,
        site=settings.FEEDBACK_TARGET)

@assign_queue('feedback_messages')
class FeedbackBot(QueueProcessingWorker):
    def start(self):
        self.staging_client = make_feedback_client()
        self.staging_client._register(
                'forward_feedback',
                method='POST',
                url='deployments/feedback',
                make_request=(lambda request: {'message': simplejson.dumps(request)}),
        )
        QueueProcessingWorker.start(self)

    def consume(self, event):
        self.staging_client.forward_feedback(event)

@assign_queue('error_reports')
class ErrorReporter(QueueProcessingWorker):
    def start(self):
        self.staging_client = make_feedback_client()
        self.staging_client._register(
                'forward_error',
                method='POST',
                url='deployments/report_error',
                make_request=(lambda type, report: {'type': type, 'report': simplejson.dumps(report)}),
        )
        QueueProcessingWorker.start(self)

    def consume(self, event):
        self.staging_client.forward_error(event['type'], event['report'])

@assign_queue('slow_queries')
class SlowQueryWorker(QueueProcessingWorker):
    def start(self):
        while True:
            self.process_one_batch()
            # Aggregate all slow query messages in 1-minute chunks to avoid message spam
            time.sleep(1 * 60)

    def process_one_batch(self):
        slow_queries = self.q.drain_queue("slow_queries", json=True)

        if settings.ERROR_BOT is None:
            return

        if len(slow_queries) > 0:
            topic = "%s: slow queries" % (settings.STATSD_PREFIX,)

            content = ""
            for query in slow_queries:
                content += "    %s\n" % (query,)

            internal_send_message(settings.ERROR_BOT, "stream", "logs", topic, content)

@assign_queue("message_sender")
class MessageSenderWorker(QueueProcessingWorker):
    def __init__(self):
        super(MessageSenderWorker, self).__init__()
        self.redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        self.handler = BaseHandler()
        self.handler.load_middleware()

    def consume(self, event):
        server_meta = event['server_meta']

        environ = {'REQUEST_METHOD': 'SOCKET',
                   'SCRIPT_NAME': '',
                   'PATH_INFO': '/json/send_message',
                   'SERVER_NAME': 'localhost',
                   'SERVER_PORT': 9993,
                   'SERVER_PROTOCOL': 'ZULIP_SOCKET/1.0',
                   'wsgi.version': (1, 0),
                   'wsgi.input': io.StringIO(),
                   'wsgi.errors': sys.stderr,
                   'wsgi.multithread': False,
                   'wsgi.multiprocess': True,
                   'wsgi.run_once': False,
                   'zulip.emulated_method': 'POST'}
        # We're mostly using a WSGIRequest for convenience
        environ.update(server_meta['request_environ'])
        request = WSGIRequest(environ)
        request._request = event['request']
        request.csrf_processing_done = True

        user_profile = get_user_profile_by_id(server_meta['user_id'])
        request._cached_user = user_profile

        resp = self.handler.get_response(request)
        server_meta['time_request_finished'] = time.time()
        server_meta['worker_log_data'] = request._log_data

        resp_content = resp.content
        result = {'response': ujson.loads(resp_content), 'req_id': event['req_id'],
                  'server_meta': server_meta}

        redis_key = req_redis_key(server_meta['client_id'], event['req_id'])
        self.redis_client.hmset(redis_key, {'status': 'complete',
                                            'response': resp_content});

        queue_json_publish(server_meta['return_queue'], result, lambda e: None)

@assign_queue('digest_emails')
class DigestWorker(QueueProcessingWorker):
    # Who gets a digest is entirely determined by the enqueue_digest_emails
    # management command, not here.
    def consume(self, event):
        logging.info("Received digest event: %s" % (event,))
        handle_digest_email(event["user_profile_id"], event["cutoff"])

@assign_queue('test')
class TestWorker(QueueProcessingWorker):
    # This worker allows you to test the queue worker infrastructure without
    # creating significant side effects.  It can be useful in development or
    # for troubleshooting prod/staging.  It pulls a message off the test queue
    # and appends it to a file in /tmp.
    def consume(self, event):
        fn = settings.ZULIP_WORKER_TEST_FILE
        message = ujson.dumps(event)
        logging.info("TestWorker should append this message to %s: %s" % (fn, message))
        with open(fn, 'a') as f:
            f.write(message + '\n')
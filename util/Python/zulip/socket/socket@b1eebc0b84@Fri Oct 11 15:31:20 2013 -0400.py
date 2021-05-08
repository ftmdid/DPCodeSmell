

from django.conf import settings
from django.utils.importlib import import_module
from django.utils import timezone
from django.contrib.sessions.models import Session as djSession

import sockjs.tornado
import tornado.ioloop
import ujson
import logging
import time

from zerver.models import UserProfile, get_user_profile_by_id, get_client
from zerver.lib.queue import queue_json_publish
from zerver.lib.actions import check_send_message, extract_recipients
from zerver.decorator import JsonableError

djsession_engine = import_module(settings.SESSION_ENGINE)
def get_user_profile(session_id):
    if session_id is None:
        return None

    try:
        djsession = djSession.objects.get(expire_date__gt=timezone.now(),
                                          session_key=session_id)
    except djSession.DoesNotExist:
        return None

    session_store = djsession_engine.SessionStore(djsession.session_key)

    try:
        return UserProfile.objects.get(pk=session_store['_auth_user_id'])
    except UserProfile.DoesNotExist:
        return None

connections = dict()
next_connection_seq = 0

def get_connection(id):
    return connections.get(id)

def register_connection(conn):
    global next_connection_seq
    conn.connection_id = "%s:%s" % (settings.SERVER_GENERATION, next_connection_seq)
    next_connection_seq = next_connection_seq + 1
    connections[conn.connection_id] = conn

def deregister_connection(conn):
    del connections[conn.connection_id]

def fake_log_line(conn_info, time, ret_code, path, email):
    # These two functions are copied from our middleware.  At some
    # point we will just run the middleware directly.
    def timedelta_ms(timedelta):
        return timedelta * 1000

    def format_timedelta(timedelta):
        if (timedelta >= 1):
            return "%.1fs" % (timedelta)
        return "%.0fms" % (timedelta_ms(timedelta),)

    logging.info('%-15s %-7s %3d %5s %s (%s)' %
                 (conn_info.ip, 'SOCKET', ret_code, format_timedelta(time),
                  path, email))

class SocketConnection(sockjs.tornado.SockJSConnection):
    def on_open(self, info):
        self.authenticated = False
        self.session.user_profile = None
        self.browser_session_id = info.get_cookie(settings.SESSION_COOKIE_NAME).value
        self.csrf_token = info.get_cookie(settings.CSRF_COOKIE_NAME).value

        ioloop = tornado.ioloop.IOLoop.instance()
        self.timeout_handle = ioloop.add_timeout(time.time() + 10, self.close)

        register_connection(self)
        fake_log_line(info, 0, 200, 'Connection opened using %s' % (self.session.transport_name,), 'unknown')

    def authenticate_client(self, msg):
        if self.authenticated:
            self.session.send_message({'client_meta': msg['client_meta'],
                                       'response': {'result': 'error', 'msg': 'Already authenticated'}})
            return

        user_profile = get_user_profile(self.browser_session_id)
        if user_profile is None:
            error_msg = 'Unknown or missing session'
            fake_log_line(self.session.conn_info, 0, 403, error_msg, 'unknown')
            self.session.send_message({'client_meta': msg['client_meta'],
                                       'response': {'result': 'error', 'msg': error_msg}})
            return
        self.session.user_profile = user_profile

        if msg['request']['csrf_token'] != self.csrf_token:
            error_msg = 'CSRF token does not match that in cookie'
            fake_log_line(self.session.conn_info, 0, 403, error_msg, 'unknown')
            self.session.send_message({'client_meta': msg['client_meta'],
                                       'response': {'result': 'error', 'msg': error_msg}})
            return

        self.session.send_message({'client_meta': msg['client_meta'],
                                   'response': {'result': 'success', 'msg': ''}})
        self.authenticated = True
        fake_log_line(self.session.conn_info, 0, 200, "Authenticated", user_profile.email)
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.remove_timeout(self.timeout_handle)

    def on_message(self, msg):
        start_time = time.time()
        msg = ujson.loads(msg)

        if msg['type'] == 'auth':
            self.authenticate_client(msg)
            return
        else:
            if not self.authenticated:
                error_msg = 'Not yet authenticated'
                fake_log_line(self.session.conn_info, 0, 403, error_msg, 'unknown')
                self.session.send_message({'client_meta': msg['client_meta'],
                                           'response': {'result': 'error', 'msg': error_msg}})
                return

        req = msg['request']
        req['sender_id'] = self.session.user_profile.id
        req['client_name'] = req['client']
        queue_json_publish("message_sender", dict(request=req,
                                                  client_meta=msg['client_meta'],
                                                  server_meta=dict(connection_id=self.connection_id,
                                                                   return_queue="tornado_return",
                                                                   start_time=start_time)),
                           fake_message_sender)

    def on_close(self):
        deregister_connection(self)
        if self.session.user_profile is None:
            fake_log_line(self.session.conn_info, 0, 408,
                          'Timeout while waiting for authentication', 'unknown')
        else:
            fake_log_line(self.session.conn_info, 0, 200,
                          'Connection closed', 'unknown')

def fake_message_sender(event):
    req = event['request']
    try:
        sender = get_user_profile_by_id(req['sender_id'])
        client = get_client(req['client_name'])

        msg_id = check_send_message(sender, client, req['type'],
                                    extract_recipients(req['to']),
                                    req['subject'], req['content'])
        resp = {"result": "success", "msg": "", "id": msg_id}
    except JsonableError as e:
        resp = {"result": "error", "msg": str(e)}

    result = {'response': resp, 'client_meta': event['client_meta'],
              'server_meta': event['server_meta']}
    respond_send_message(None, None, None, result)

def respond_send_message(chan, method, props, data):
    connection = get_connection(data['server_meta']['connection_id'])
    if connection is not None:
        connection.session.send_message({'client_meta': data['client_meta'], 'response': data['response']})
        fake_log_line(connection.session.conn_info,
                      time.time() - data['server_meta']['start_time'],
                      200, 'send_message', connection.session.user_profile.email)

sockjs_router = sockjs.tornado.SockJSRouter(SocketConnection, "/sockjs",
                                            {'sockjs_url': 'https://%s/static/third/sockjs/sockjs-0.3.4.js' % (settings.EXTERNAL_HOST,),
                                             'disabled_transports': ['eventsource', 'htmlfile']})
def get_sockjs_router():
    return sockjs_router
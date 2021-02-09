from __future__ import absolute_import

from django.conf import settings
from zerver.lib.response import json_error
from django.db import connection
from zerver.lib.utils import statsd
from zerver.lib.queue import queue_json_publish
from zerver.lib.cache import get_memcached_time, get_memcached_requests
from zerver.lib.bugdown import get_bugdown_time, get_bugdown_requests
from zerver.models import flush_per_process_display_recipient_cache
from zerver.exceptions import RateLimited

import logging
import time

logger = logging.getLogger('zulip.requests')

def record_request_stop_data(log_data):
    log_data['time_stopped'] = time.time()
    log_data['memcached_time_stopped'] = get_memcached_time()
    log_data['memcached_requests_stopped'] = get_memcached_requests()
    log_data['bugdown_time_stopped'] = get_bugdown_time()
    log_data['bugdown_requests_stopped'] = get_bugdown_requests()

def async_request_stop(request):
    record_request_stop_data(request._log_data)

def record_request_restart_data(log_data):
    log_data['time_restarted'] = time.time()
    log_data['memcached_time_restarted'] = get_memcached_time()
    log_data['memcached_requests_restarted'] = get_memcached_requests()
    log_data['bugdown_time_restarted'] = get_bugdown_time()
    log_data['bugdown_requests_restarted'] = get_bugdown_requests()

def async_request_restart(request):
    record_request_restart_data(request._log_data)

def record_request_start_data(log_data):
    log_data['time_started'] = time.time()
    log_data['memcached_time_start'] = get_memcached_time()
    log_data['memcached_requests_start'] = get_memcached_requests()
    log_data['bugdown_time_start'] = get_bugdown_time()
    log_data['bugdown_requests_start'] = get_bugdown_requests()

def write_log_line(log_data, path, method, remote_ip, email, client_name,
                   status_code=200, error_content=''):
    def timedelta_ms(timedelta):
        return timedelta * 1000

    def format_timedelta(timedelta):
        if (timedelta >= 1):
            return "%.1fs" % (timedelta)
        return "%.0fms" % (timedelta_ms(timedelta),)

    # For statsd timer name
    if path == '/':
        statsd_path = 'webreq'
    else:
        statsd_path = u"webreq.%s" % (path[1:].replace('/', '.'),)
        # Remove non-ascii chars from path (there should be none, if there are it's
        # because someone manually entered a nonexistant path), as UTF-8 chars make
        # statsd sad when it sends the key name over the socket
        statsd_path = statsd_path.encode('ascii', errors='ignore')
    blacklisted_requests = ['do_confirm', 'accounts.login.openid', 'send_confirm',
                            'eventslast_event_id', 'webreq.content']
    suppress_statsd = any((blacklisted in statsd_path for blacklisted in blacklisted_requests))

    time_delta = -1
    # A time duration of -1 means the StartLogRequests middleware
    # didn't run for some reason
    optional_orig_delta = ""
    if 'time_started' in log_data:
        time_delta = time.time() - log_data['time_started']
    if 'time_stopped' in log_data:
        orig_time_delta = time_delta
        time_delta = ((log_data['time_stopped'] - log_data['time_started']) +
                      (time.time() - log_data['time_restarted']))
        optional_orig_delta = " (lp: %s)" % (format_timedelta(orig_time_delta),)
    memcached_output = ""
    if 'memcached_time_start' in log_data:
        memcached_time_delta = get_memcached_time() - log_data['memcached_time_start']
        memcached_count_delta = get_memcached_requests() - log_data['memcached_requests_start']
        if 'memcached_requests_stopped' in log_data:
            # (now - restarted) + (stopped - start) = (now - start) + (stopped - restarted)
            memcached_time_delta += (log_data['memcached_time_stopped'] -
                                     log_data['memcached_time_restarted'])
            memcached_count_delta += (log_data['memcached_requests_stopped'] -
                                      log_data['memcached_requests_restarted'])

        if (memcached_time_delta > 0.005):
            memcached_output = " (mem: %s/%s)" % (format_timedelta(memcached_time_delta),
                                                  memcached_count_delta)

        if not suppress_statsd:
            statsd.timing("%s.memcached.time" % (statsd_path,), timedelta_ms(memcached_time_delta))
            statsd.incr("%s.memcached.querycount" % (statsd_path,), memcached_count_delta)

    bugdown_output = ""
    if 'bugdown_time_start' in log_data:
        bugdown_time_delta = get_bugdown_time() - log_data['bugdown_time_start']
        bugdown_count_delta = get_bugdown_requests() - log_data['bugdown_requests_start']
        if 'bugdown_requests_stopped' in log_data:
            # (now - restarted) + (stopped - start) = (now - start) + (stopped - restarted)
            bugdown_time_delta += (log_data['bugdown_time_stopped'] -
                                   log_data['bugdown_time_restarted'])
            bugdown_count_delta += (log_data['bugdown_requests_stopped'] -
                                    log_data['bugdown_requests_restarted'])

        if (bugdown_time_delta > 0.005):
            bugdown_output = " (md: %s/%s)" % (format_timedelta(bugdown_time_delta),
                                               bugdown_count_delta)

            if not suppress_statsd:
                statsd.timing("%s.markdown.time" % (statsd_path,), timedelta_ms(bugdown_time_delta))
                statsd.incr("%s.markdown.count" % (statsd_path,), bugdown_count_delta)

    # Get the amount of time spent doing database queries
    db_time_output = ""
    if len(connection.queries) > 0:
        query_time = sum(float(query.get('time', 0)) for query in connection.queries)
        db_time_output = " (db: %s/%sq)" % (format_timedelta(query_time),
                                            len(connection.queries))

        if not suppress_statsd:
            # Log ms, db ms, and num queries to statsd
            statsd.timing("%s.dbtime" % (statsd_path,), timedelta_ms(query_time))
            statsd.incr("%s.dbq" % (statsd_path, ), len(connection.queries))
            statsd.timing("%s.total" % (statsd_path,), timedelta_ms(time_delta))

    if 'extra' in log_data:
        extra_request_data = " %s" % (log_data['extra'],)
    else:
        extra_request_data = ""
    logger_client = "(%s via %s)" % (email, client_name)
    logger_timing = '%5s%s%s%s%s %s' % \
                     (format_timedelta(time_delta), optional_orig_delta,
                      memcached_output, bugdown_output,
                      db_time_output, path)
    logger_line = '%-15s %-7s %3d %s%s %s' % \
                    (remote_ip, method, status_code,
                     logger_timing, extra_request_data, logger_client)
    logger.info(logger_line)

    if time_delta >= 1:
        queue_json_publish("slow_queries", "%s (%s)" % (logger_timing, email), lambda e: None)

    # Log some additional data whenever we return certain 40x errors
    if 400 <= status_code < 500 and status_code not in [401, 404, 405]:
        if len(error_content) > 100:
            error_content = "[content more than 100 characters]"
        logger.info('status=%3d, data=%s, uid=%s' % (status_code, error_content, email))

class LogRequests(object):
    def process_request(self, request):
        request._log_data = dict()
        record_request_start_data(request._log_data)
        connection.queries = []

    def process_response(self, request, response):
        # The reverse proxy might have sent us the real external IP
        remote_ip = request.META.get('HTTP_X_REAL_IP')
        if remote_ip is None:
            remote_ip = request.META['REMOTE_ADDR']

        # Get the requestor's email address and client, if available.
        try:
            email = request._email
        except Exception:
            email = "unauth"
        try:
            client = request.client.name
        except Exception:
            client = "?"

        write_log_line(request._log_data, request.path, request.method,
                       remote_ip, email, client, response.status_code,
                       response.content)
        return response

class JsonErrorHandler(object):
    def process_exception(self, request, exception):
        if hasattr(exception, 'to_json_error_msg') and callable(exception.to_json_error_msg):
            return json_error(exception.to_json_error_msg())
        return None

# Monkeypatch in time tracking to the Django non-debug cursor
# Code comes from CursorDebugWrapper
def wrapper_execute(self, action, sql, params=()):
    start = time.time()
    try:
        return action(sql, params)
    finally:
        stop = time.time()
        duration = stop - start
        self.db.queries.append({
                'time': "%.3f" % duration,
                })

from django.db.backends.util import CursorWrapper
def cursor_execute(self, sql, params=()):
    return wrapper_execute(self, self.cursor.execute, sql, params)
CursorWrapper.execute = cursor_execute

def cursor_executemany(self, sql, params=()):
    return wrapper_execute(self, self.cursor.executemany, sql, params)
CursorWrapper.executemany = cursor_executemany

class RateLimitMiddleware(object):
    def process_response(self, request, response):
        if not settings.RATE_LIMITING:
            return response

        from zerver.lib.rate_limiter import max_api_calls
        # Add X-RateLimit-*** headers
        if hasattr(request, '_ratelimit_applied_limits'):
            response['X-RateLimit-Limit'] = max_api_calls(request.user)
            if hasattr(request, '_ratelimit_secs_to_freedom'):
                response['X-RateLimit-Reset'] = int(time.time() + request._ratelimit_secs_to_freedom)
            if hasattr(request, '_ratelimit_remaining'):
                response['X-RateLimit-Remaining'] = request._ratelimit_remaining
        return response

    def process_exception(self, request, exception):
        if type(exception) == RateLimited:
            resp = json_error("API usage exceeded rate limit, try again in %s secs" % (request._ratelimit_secs_to_freedom,), status=403)
            return resp

class FlushDisplayRecipientCache(object):
    def process_response(self, request, response):
        # We flush the recipient cache after every request, so it is
        # not shared at all between requests. We do this so all users
        # have a consistent view of stream name changes.
        flush_per_process_display_recipient_cache()
        return response
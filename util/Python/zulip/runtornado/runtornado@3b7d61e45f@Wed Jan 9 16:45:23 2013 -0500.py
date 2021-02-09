from django.conf import settings
settings.RUNNING_INSIDE_TORNADO = True
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os
import sys
import tornado.web
import logging
import time
from tornado import ioloop

# A hack to keep track of how much time we spend working, versus sleeping in
# the event loop.
#
# Creating a new event loop instance with a custom impl object fails (events
# don't get processed), so instead we modify the ioloop module variable holding
# the default poll implementation.  We need to do this before any Tornado code
# runs that might instantiate the default event loop.

orig_poll_impl = ioloop._poll

class InstrumentedPoll(object):
    def __init__(self):
        self._underlying = orig_poll_impl()
        self._times = []
        self._last_print = 0

    # Python won't let us subclass e.g. select.epoll, so instead
    # we proxy every method.  __getattr__ handles anything we
    # don't define elsewhere.
    def __getattr__(self, name):
        return getattr(self._underlying, name)

    # Call the underlying poll method, and report timing data.
    def poll(self, timeout):
        # Avoid accumulating a bunch of insignificant data points
        # from short timeouts.
        if timeout < 1e-3:
            return self._underlying.poll(timeout)

        # Record start and end times for the underlying poll
        t0 = time.time()
        result = self._underlying.poll(timeout)
        t1 = time.time()

        # Log this datapoint and restrict our log to the past minute
        self._times.append((t0, t1))
        while self._times and self._times[0][0] < t1 - 60:
            self._times.pop(0)

        # Report (at most once every 5s) the percentage of time spent
        # outside poll
        if self._times and t1 - self._last_print >= 5:
            total = t1 - self._times[0][0]
            in_poll = sum(b-a for a,b in self._times)
            if total > 0:
                logging.info('Tornado %5.1f%% busy over the past %4.1f seconds'
                    % (100 * (1 - in_poll/total), total))
                self._last_print = t1

        return result

ioloop._poll = InstrumentedPoll

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--nokeepalive', action='store_true',
            dest='no_keep_alive', default=False,
            help="Tells Tornado to NOT keep alive http connections."),
        make_option('--noxheaders', action='store_false',
            dest='xheaders', default=True,
            help="Tells Tornado to NOT override remote IP with X-Real-IP."),
    )
    help = "Starts a Tornado Web server wrapping Django."
    args = '[optional port number or ipaddr:port]\n  (use multiple ports to start multiple servers)'

    def handle(self, addrport, **options):
        # setup unbuffered I/O
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
        sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

        import django
        from django.core.handlers.wsgi import WSGIHandler
        from tornado import httpserver, wsgi, web

        try:
            addr, port = addrport.split(':')
        except ValueError:
            addr, port = '', addrport

        if not addr:
            addr = '127.0.0.1'

        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)

        xheaders = options.get('xheaders', True)
        no_keep_alive = options.get('no_keep_alive', False)
        quit_command = 'CTRL-C'

        if settings.DEBUG:
            logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(levelname)-8s %(message)s')

        def inner_run():
            from django.conf import settings
            from django.utils import translation
            translation.activate(settings.LANGUAGE_CODE)

            print "Validating Django models.py..."
            self.validate(display_num_errors=True)
            print "\nDjango version %s" % (django.get_version())
            print "Tornado server is running at http://%s:%s/" % (addr, port)
            print "Quit the server with %s." % quit_command

            try:
                # Application is an instance of Django's standard wsgi handler.
                application = web.Application([(r"/json/get_updates", AsyncDjangoHandler),
                                               (r"/api/v1/get_messages", AsyncDjangoHandler),
                                               (r"/notify_new_message", AsyncDjangoHandler),
                                               (r"/notify_pointer_update", AsyncDjangoHandler),

                                               ], debug=django.conf.settings.DEBUG)

                # start tornado web server in single-threaded mode
                http_server = httpserver.HTTPServer(application,
                                                    xheaders=xheaders,
                                                    no_keep_alive=no_keep_alive)
                http_server.listen(int(port), address=addr)

                if django.conf.settings.DEBUG:
                    ioloop.IOLoop.instance().set_blocking_log_threshold(5)

                ioloop.IOLoop.instance().start()
            except KeyboardInterrupt:
                sys.exit(0)

        inner_run()

#
#  Modify the base Tornado handler for Django
#
from threading import Lock
from django.core.handlers import base
from django.core.urlresolvers import set_script_prefix
from django.core import signals

class AsyncDjangoHandler(tornado.web.RequestHandler, base.BaseHandler):
    initLock = Lock()

    def __init__(self, *args, **kwargs):
        super(AsyncDjangoHandler, self).__init__(*args, **kwargs)

        # Set up middleware if needed. We couldn't do this earlier, because
        # settings weren't available.
        self._request_middleware = None
        self.initLock.acquire()
        # Check that middleware is still uninitialised.
        if self._request_middleware is None:
            self.load_middleware()
        self.initLock.release()
        self._auto_finish = False

    def get(self):
        from tornado.wsgi import WSGIContainer
        from django.core.handlers.wsgi import WSGIRequest
        import urllib

        environ  = WSGIContainer.environ(self.request)
        environ['PATH_INFO'] = urllib.unquote(environ['PATH_INFO'])
        request  = WSGIRequest(environ)
        request._tornado_handler     = self

        set_script_prefix(base.get_script_name(environ))
        signals.request_started.send(sender=self.__class__)
        try:
            response = self.get_response(request)

            if not response:
                return
        finally:
            signals.request_finished.send(sender=self.__class__)

        self.set_status(response.status_code)
        for h in response.items():
            self.set_header(h[0], h[1])

        if not hasattr(self, "_new_cookies"):
            self._new_cookies = []
        self._new_cookies.append(response.cookies)

        self.write(response.content)
        self.finish()


    def head(self):
        self.get()

    def post(self):
        self.get()

    # Based on django.core.handlers.base: get_response
    def get_response(self, request):
        "Returns an HttpResponse object for the given HttpRequest"
        from django import http
        from django.core import exceptions, urlresolvers
        from django.conf import settings

        try:
            try:
                # Setup default url resolver for this thread.
                urlconf = settings.ROOT_URLCONF
                urlresolvers.set_urlconf(urlconf)
                resolver = urlresolvers.RegexURLResolver(r'^/', urlconf)

                response = None

                # Apply request middleware
                for middleware_method in self._request_middleware:
                    response = middleware_method(request)
                    if response:
                        break

                if hasattr(request, "urlconf"):
                    # Reset url resolver with a custom urlconf.
                    urlconf = request.urlconf
                    urlresolvers.set_urlconf(urlconf)
                    resolver = urlresolvers.RegexURLResolver(r'^/', urlconf)

                callback, callback_args, callback_kwargs = resolver.resolve(
                        request.path_info)

                # Apply view middleware
                if response is None:
                    for middleware_method in self._view_middleware:
                        response = middleware_method(request, callback, callback_args, callback_kwargs)
                        if response:
                            break

                if response is None:
                    from ...decorator import RespondAsynchronously

                    try:
                        response = callback(request, *callback_args, **callback_kwargs)
                        if response is RespondAsynchronously:
                            return
                    except Exception, e:
                        # If the view raised an exception, run it through exception
                        # middleware, and if the exception middleware returns a
                        # response, use that. Otherwise, reraise the exception.
                        for middleware_method in self._exception_middleware:
                            response = middleware_method(request, e)
                            if response:
                                break
                        if response is None:
                            raise

                if response is None:
                    try:
                        view_name = callback.func_name
                    except AttributeError:
                        view_name = callback.__class__.__name__ + '.__call__'
                    raise ValueError("The view %s.%s returned None." %
                                     (callback.__module__, view_name))

                # If the response supports deferred rendering, apply template
                # response middleware and the render the response
                if hasattr(response, 'render') and callable(response.render):
                    for middleware_method in self._template_response_middleware:
                        response = middleware_method(request, response)
                    response = response.render()


            except http.Http404, e:
                if settings.DEBUG:
                    from django.views import debug
                    response = debug.technical_404_response(request, e)
                else:
                    try:
                        callback, param_dict = resolver.resolve404()
                        response = callback(request, **param_dict)
                    except:
                        try:
                            response = self.handle_uncaught_exception(request, resolver, sys.exc_info())
                        finally:
                            signals.got_request_exception.send(sender=self.__class__, request=request)
            except exceptions.PermissionDenied:
                logging.warning(
                    'Forbidden (Permission denied): %s', request.path,
                    extra={
                        'status_code': 403,
                        'request': request
                    })
                try:
                    callback, param_dict = resolver.resolve403()
                    response = callback(request, **param_dict)
                except:
                    try:
                        response = self.handle_uncaught_exception(request,
                            resolver, sys.exc_info())
                    finally:
                        signals.got_request_exception.send(
                            sender=self.__class__, request=request)
            except SystemExit:
                # See https://code.djangoproject.com/ticket/4701
                raise
            except Exception, e:
                exc_info = sys.exc_info()
                signals.got_request_exception.send(sender=self.__class__, request=request)
                return self.handle_uncaught_exception(request, resolver, exc_info)
        finally:
            # Reset urlconf on the way out for isolation
            urlresolvers.set_urlconf(None)

        try:
            # Apply response middleware, regardless of the response
            for middleware_method in self._response_middleware:
                response = middleware_method(request, response)
            response = self.apply_response_fixes(request, response)
        except: # Any exception should be gathered and handled
            signals.got_request_exception.send(sender=self.__class__, request=request)
            response = self.handle_uncaught_exception(request, resolver, sys.exc_info())

        return response
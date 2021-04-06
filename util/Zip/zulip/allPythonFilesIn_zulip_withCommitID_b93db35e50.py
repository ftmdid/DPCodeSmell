#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "humbug.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


import traceback
from hashlib import sha256
from datetime import datetime, timedelta

# Adapted http://djangosnippets.org/snippets/2242/ by user s29 (October 25, 2010)

class _RateLimitFilter(object):
    last_error = datetime.min

    def filter(self, record):
        from django.conf import settings
        from django.core.cache import cache

        # Track duplicate errors
        duplicate = False
        rate = getattr(settings, '%s_LIMIT' %  self.__class__.__name__.upper(),
               600)  # seconds
        if rate > 0:
            # Test if the cache works
            try:
                cache.set('RLF_TEST_KEY', 1, 1)
                use_cache = cache.get('RLF_TEST_KEY') == 1
            except:
                use_cache = False

            if use_cache:
                key = self.__class__.__name__.upper()
                duplicate = cache.get(key) == 1
                cache.set(key, 1, rate)
            else:
                min_date = datetime.now() - timedelta(seconds=rate)
                duplicate = (self.last_error >= min_date)
                if not duplicate:
                    self.last_error = datetime.now()

        return not duplicate

class HumbugLimiter(_RateLimitFilter):
    pass

class EmailLimiter(_RateLimitFilter):
    pass

from django.contrib.auth.models import User

class EmailAuthBackend(object):
    """
    Email Authentication Backend

    Allows a user to sign in using an email/password pair rather than
    a username/password pair.
    """

    def authenticate(self, username=None, password=None):
        """ Authenticate a user based on email address as the user name. """
        if username is None or password is None:
            # Return immediately.  Otherwise we will look for a SQL row with
            # NULL username.  While that's probably harmless, it's needless
            # exposure.
            return None

        try:
            user = User.objects.get(email__iexact=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        """ Get a User object from the user_id. """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

# Django settings for humbug project.
import os
import platform

DEPLOYED = (('humbughq.com' in platform.node())
            or os.path.exists('/etc/humbug-server'))
STAGING_DEPLOYED = (platform.node() == 'staging.humbughq.com')

DEBUG = not DEPLOYED
TEMPLATE_DEBUG = DEBUG

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

ADMINS = (
    ('Devel', 'devel@humbughq.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'zephyrdb',
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {
            'timeout': 20,
        },
    },
}

if DEPLOYED:
    DATABASES["default"] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'humbug',
        'USER': 'humbug',
        'PASSWORD': '', # Authentication done via certificates
        'HOST': '10.254.4.99',
        'OPTIONS': {
            # Note that 'verify-ca' only checks that the server certificate was
            # signed by a trusted root.  You need 'verify-full' if you want to
            # check that the server's hostname in the certificate matches the
            # host you connect to.
            #
            # We don't currently do 'verify-full' because the web servers
            # connect to the database using its AWS internal IP address, which
            # doesn't reverse-resolve to its hostname.  And because the
            # database's certificate is for its hostname instead of its internal
            # IP address, the frontend can't verify that the certificate is for
            # the correct machine.  This can be solved by running DNS
            # internally.  For now, 'verify-ca' is probably sufficient because
            # the certificates are signed by our own CA.
            'sslmode': 'verify-ca',
            },
        }
elif False:
    DATABASES["default"] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'humbug',
        'USER': 'humbug',
        'PASSWORD': 'yuHavmefbek5',
        'HOST': 'localhost'
        }

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# The ID, as an integer, of the current site in the django_site database table.
# This is used so that application data can hook into specific site(s) and a
# single database can manage content for multiple sites.
#
# We set this site's domain to 'humbughq.com' in populate_db.
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
TEMPLATE_DIRS = ( os.path.join(SITE_ROOT, '..', 'templates'),)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# A fixed salt used for hashing in certain places, e.g. email-based
# username generation.
HASH_SALT = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Tell the browser to never send our cookies without encryption, e.g.
# when executing the initial http -> https redirect.
#
# Turn it off for local testing because we don't have SSL.
if DEPLOYED:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE    = True

# Prevent Javascript from reading the CSRF token from cookies.  Our code gets
# the token from the DOM, which means malicious code could too.  But hiding the
# cookie will slow down some attackers.
CSRF_COOKIE_PATH = '/;HttpOnly'

# Used just for generating initial passwords and API keys.
INITIAL_PASSWORD_SALT = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
INITIAL_API_KEY_SALT  = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# A shared secret, used to authenticate different parts of the app to each other.
# FIXME: store this password more securely
SHARED_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Base URL of the Tornado server
# We set it to None when running backend tests or populate_db.
# We override the port number when running frontend tests.
TORNADO_SERVER = 'http://localhost:9993'

# Make redirects work properly behind a reverse proxy
USE_X_FORWARDED_HOST = True

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    # Our logging middleware should be the first middleware item.
    'zephyr.middleware.LogRequests',
    'zephyr.middleware.JsonErrorHandler',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

AUTHENTICATION_BACKENDS = ('humbug.backends.EmailAuthBackend',)

TEST_RUNNER = 'zephyr.tests.Runner'

ROOT_URLCONF = 'humbug.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'humbug.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'south',
    'jstemplate',
    'confirmation',
    'zephyr',
)

# Caching
if DEPLOYED:
    CACHES = { 'default': {
        'BACKEND':  'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT':  3600
    } }
else:
    CACHES = { 'default': {
        'BACKEND':  'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'humbug-default-local-cache',
        'TIMEOUT':  3600,
        'OPTIONS': {
            'MAX_ENTRIES': 100000
        }
    } }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)-8s %(message)s'
        }
    },
    'filters': {
        'HumbugLimiter': {
            '()': 'humbug.ratelimit.HumbugLimiter',
        },
        'EmailLimiter': {
            '()': 'humbug.ratelimit.EmailLimiter',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'inapp': {
            'level':     'ERROR',
            'class':     'zephyr.handlers.AdminHumbugHandler',
            'filters':   ['HumbugLimiter', 'require_debug_false'],
            'formatter': 'default'
        },
        'console': {
            'level':     'DEBUG',
            'class':     'logging.StreamHandler',
            'formatter': 'default'
        },
        'file': {
            'level':     'DEBUG',
            'class':     'logging.FileHandler',
            'formatter': 'default',
            'filename':  'server.log'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['EmailLimiter', 'require_debug_false'],
        },
    },
    'loggers': {
        '': {
            'handlers': ['inapp', 'console', 'file', 'mail_admins'],
            'level':    'INFO'
        }
    }
}

TEMPLATE_CONTEXT_PROCESSORS = (
    'zephyr.context_processors.add_settings',
)

ACCOUNT_ACTIVATION_DAYS=7
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'humbug@humbughq.com'
EMAIL_HOST_PASSWORD = 'xxxxxxxxxxxxxxxx'
EMAIL_PORT = 587

DEFAULT_FROM_EMAIL = "Humbug <humbug@humbughq.com>"

LOGIN_REDIRECT_URL='/'

MESSAGE_LOG="all_messages_log." + platform.node()

# Polling timeout for get_updates, in milliseconds.
# We configure this here so that the client test suite can override it.
# The default is 55 seconds, to deal with crappy home wireless routers that
# kill "inactive" http connections.
POLL_TIMEOUT = 55 * 1000

if DEPLOYED:
    ALLOW_REGISTER = False
    FULL_NAVBAR    = False
    HOME_NOT_LOGGED_IN = '/accounts/login'
else:
    ALLOW_REGISTER = True
    FULL_NAVBAR    = True
    HOME_NOT_LOGGED_IN = '/accounts/home'

# For testing, you may want to have emails be printed to the console.
if not DEPLOYED:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

    # Use fast password hashing for creating testing users when not
    # DEPLOYED
    PASSWORD_HASHERS = (
                'django.contrib.auth.hashers.SHA1PasswordHasher',
                'django.contrib.auth.hashers.PBKDF2PasswordHasher'
            )

if DEPLOYED:
    # Filter out user data
    DEFAULT_EXCEPTION_REPORTER_FILTER = 'zephyr.filters.HumbugExceptionReporterFilter'

from django.conf import settings
from django.conf.urls import patterns, url
import os.path
import zephyr.forms

urlpatterns = patterns('',
    url(r'^$', 'zephyr.views.home'),
    # We have two entries for accounts/login to allow reverses on the Django
    # view we're wrapping to continue to function.
    url(r'^accounts/login/',  'zephyr.views.login_page',         {'template_name': 'zephyr/login.html'}),
    url(r'^accounts/login/',  'django.contrib.auth.views.login', {'template_name': 'zephyr/login.html'}),
    url(r'^accounts/logout/', 'django.contrib.auth.views.logout_then_login'),

    url(r'^accounts/password/reset/$', 'django.contrib.auth.views.password_reset',
        {'post_reset_redirect' : '/accounts/password/reset/done/',
            'template_name': 'zephyr/reset.html',
            'email_template_name': 'registration/password_reset_email.txt',
            }),
    url(r'^accounts/password/reset/done/$', 'django.contrib.auth.views.password_reset_done',
        {'template_name': 'zephyr/reset_emailed.html'}),
    url(r'^accounts/password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm',
        {'post_reset_redirect' : '/accounts/password/done/', 'template_name': 'zephyr/reset_confirm.html',
         'set_password_form' : zephyr.forms.LoggingSetPasswordForm}),
    url(r'^accounts/password/done/$', 'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'zephyr/reset_done.html'}),


    url(r'^activity$', 'zephyr.views.get_activity'),

    # Registration views, require a confirmation ID.
    url(r'^accounts/home/', 'zephyr.views.accounts_home'),
    url(r'^accounts/send_confirm/(?P<email>[\S]+)?', 'django.views.generic.simple.direct_to_template',
        {'template': 'zephyr/accounts_send_confirm.html'}, name='send_confirm'),
    url(r'^accounts/register/', 'zephyr.views.accounts_register'),
    url(r'^accounts/do_confirm/(?P<confirmation_key>[\w]+)', 'confirmation.views.confirm'),

    # Portico-styled page used to provide email confirmation of terms acceptance.
    url(r'^accounts/accept_terms', 'zephyr.views.accounts_accept_terms'),

    # Terms of service and privacy policy
    url(r'^terms$',   'django.views.generic.simple.direct_to_template', {'template': 'zephyr/terms.html'}),
    url(r'^privacy$', 'django.views.generic.simple.direct_to_template', {'template': 'zephyr/privacy.html'}),

    # New user "tutorial"
    url(r'^new-user$', 'django.views.generic.simple.direct_to_template', {'template': 'zephyr/new-user.html'}),

    # These are json format views used by the web client.  They require a logged in browser.
    url(r'^json/get_updates$',              'zephyr.tornadoviews.json_get_updates'),
    url(r'^json/update_pointer$',           'zephyr.views.json_update_pointer'),
    url(r'^json/get_old_messages$',         'zephyr.views.json_get_old_messages'),
    url(r'^json/send_message$',             'zephyr.views.json_send_message'),
    url(r'^json/settings/change$',          'zephyr.views.json_change_settings'),
    url(r'^json/subscriptions/list$',       'zephyr.views.json_list_subscriptions'),
    url(r'^json/subscriptions/remove$',     'zephyr.views.json_remove_subscriptions'),
    url(r'^json/subscriptions/add$',        'zephyr.views.json_add_subscriptions'),
    url(r'^json/subscriptions/exists$',     'zephyr.views.json_stream_exists'),
    url(r'^json/subscriptions/property$',   'zephyr.views.json_subscription_property'),
    url(r'^json/fetch_api_key$',            'zephyr.views.json_fetch_api_key'),

    # These are json format views used by the API.  They require an API key.
    url(r'^api/v1/get_messages$',           'zephyr.tornadoviews.api_get_messages'),
    url(r'^api/v1/get_profile$',            'zephyr.views.api_get_profile'),
    url(r'^api/v1/get_old_messages$',       'zephyr.views.api_get_old_messages'),
    url(r'^api/v1/get_public_streams$',     'zephyr.views.api_get_public_streams'),
    url(r'^api/v1/subscriptions/list$',     'zephyr.views.api_list_subscriptions'),
    url(r'^api/v1/subscriptions/add$',      'zephyr.views.api_add_subscriptions'),
    url(r'^api/v1/subscriptions/remove$',   'zephyr.views.api_remove_subscriptions'),
    url(r'^api/v1/send_message$',           'zephyr.views.api_send_message'),
    url(r'^api/v1/update_pointer$',         'zephyr.views.api_update_pointer'),
    url(r'^api/v1/external/github$',        'zephyr.views.api_github_landing'),

    # This json format view used by the API accepts a username password/pair and returns an API key.
    url(r'^api/v1/fetch_api_key$',          'zephyr.views.api_fetch_api_key'),

    url(r'^robots\.txt$', 'django.views.generic.simple.redirect_to', {'url': '/static/public/robots.txt'}),

    # Used internally for communication between Django and Tornado processes
    url(r'^notify_new_message$',            'zephyr.tornadoviews.notify_new_message'),
    url(r'^notify_pointer_update$',         'zephyr.tornadoviews.notify_pointer_update'),
)

if not settings.DEPLOYED:
    urlpatterns += patterns('',
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(settings.SITE_ROOT, '../zephyr/static-access-control')}))

"""
WSGI config for humbug project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "humbug.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

#!/usr/bin/env python
import optparse
import subprocess
import signal
import traceback
import os
from os import path

from twisted.internet import reactor
from twisted.web      import proxy, server, resource

parser = optparse.OptionParser(r"""

Starts the app listening on localhost, for local development.

This script launches the Django and Tornado servers, then runs a reverse proxy
which serves to both of them.  After it's all up and running, browse to

    http://localhost:9991/

Note that, while runserver and runtornado have the usual auto-restarting
behavior, the reverse proxy itself does *not* automatically restart on changes
to this file.
""")

parser.add_option('--test',
    action='store_true', dest='test',
    help='Use the testing database and ports')

(options, args) = parser.parse_args()

base_port   = 9991
manage_args = ''
if options.test:
    base_port   = 9981
    manage_args = '--settings=humbug.test_settings'

proxy_port   = base_port
django_port  = base_port+1
tornado_port = base_port+2
proxy_host = 'localhost:%d' % (proxy_port,)

os.chdir(path.join(path.dirname(__file__), '..'))

# Set up a new process group, so that we can later kill run{server,tornado}
# and all of the processes they spawn.
os.setpgrp()

for cmd in ['python manage.py runserver  %s localhost:%d' % (manage_args, django_port),
            'python manage.py runtornado %s localhost:%d' % (manage_args, tornado_port)]:
    subprocess.Popen(cmd, shell=True)

class Resource(resource.Resource):
    def getChild(self, name, request):
        request.requestHeaders.setRawHeaders('X-Forwarded-Host', [proxy_host])

        if request.uri in ['/json/get_updates', '/api/v1/get_messages']:
            return proxy.ReverseProxyResource('localhost', tornado_port, '/'+name)

        return proxy.ReverseProxyResource('localhost', django_port, '/'+name)

try:
    reactor.listenTCP(proxy_port, server.Site(Resource()), interface='127.0.0.1')
    reactor.run()
except:
    # Print the traceback before we get SIGTERM and die.
    traceback.print_exc()
    raise
finally:
    # Kill everything in our process group.
    os.killpg(0, signal.SIGTERM)

# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: models.py 28 2009-10-22 15:03:02Z jarek.zgoda $'

import os
import re
from hashlib import sha1

from django.db import models
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader, Context
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

from confirmation.util import get_status_field

try:
    import mailer
    send_mail = mailer.send_mail
except ImportError:
    # no mailer app present, stick with default
    pass


SHA1_RE = re.compile('^[a-f0-9]{40}$')


class ConfirmationManager(models.Manager):

    def confirm(self, confirmation_key):
        if SHA1_RE.search(confirmation_key):
            try:
                confirmation = self.get(confirmation_key=confirmation_key)
            except self.model.DoesNotExist:
                return False
            obj = confirmation.content_object
            status_field = get_status_field(obj._meta.app_label, obj._meta.module_name)
            setattr(obj, status_field, getattr(settings, 'STATUS_ACTIVE', 1))
            obj.save()
            return obj
        return False

    def send_confirmation(self, obj, email_address):
        confirmation_key = sha1(str(os.urandom(20)) + str(email_address)).hexdigest()
        current_site = Site.objects.get_current()
        activate_url = u'https://%s%s' % (current_site.domain,
            reverse('confirmation.views.confirm', kwargs={'confirmation_key': confirmation_key}))
        context = Context({
            'activate_url': activate_url,
            'current_site': current_site,
            'confirmation_key': confirmation_key,
            'target': obj,
            'days': getattr(settings, 'EMAIL_CONFIRMATION_DAYS', 10),
        })
        templates = [
            'confirmation/%s_confirmation_email_subject.txt' % obj._meta.module_name,
            'confirmation/confirmation_email_subject.txt',
        ]
        template = loader.select_template(templates)
        subject = template.render(context).strip().replace(u'\n', u' ') # no newlines, please
        templates = [
            'confirmation/%s_confirmation_email_body.txt' % obj._meta.module_name,
            'confirmation/confirmation_email_body.txt',
        ]
        template = loader.select_template(templates)
        body = template.render(context)
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email_address])
        return self.create(content_object=obj, date_sent=now(), confirmation_key=confirmation_key)


class Confirmation(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    date_sent = models.DateTimeField(_('sent'))
    confirmation_key = models.CharField(_('activation key'), max_length=40)

    objects = ConfirmationManager()

    class Meta:
        verbose_name = _('confirmation email')
        verbose_name_plural = _('confirmation emails')

    def __unicode__(self):
        return _('confirmation email for %s') % self.content_object

# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: util.py 3 2008-11-18 07:33:52Z jarek.zgoda $'

from django.conf import settings

def get_status_field(app_label, model_name):
    model = '%s.%s' % (app_label, model_name)
    mapping = getattr(settings, 'STATUS_FIELDS', {})
    return mapping.get(model, 'status')
# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a                                                       
# copy of this software and associated documentation files (the                                                                 
# "Software"), to deal in the Software without restriction, including                                                           
# without limitation the rights to use, copy, modify, merge, publish, dis-                                                      
# tribute, sublicense, and/or sell copies of the Software, and to permit                                                        
# persons to whom the Software is furnished to do so, subject to the fol-                                                       
# lowing conditions:                                                                                                            
#                                                                                                                               
# The above copyright notice and this permission notice shall be included                                                       
# in all copies or substantial portions of the Software.                                                                        
#                                                                                                                               
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS                                                       
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-                                                      
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT                                                        
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,                                                         
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,                                                            
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS                                                        
# IN THE SOFTWARE.

VERSION = (0, 9, 'pre')

# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: settings.py 12 2008-11-23 19:38:52Z jarek.zgoda $'

STATUS_ACTIVE = 1

STATUS_FIELDS = {
}

# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: views.py 21 2008-12-05 09:21:03Z jarek.zgoda $'


from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings

from confirmation.models import Confirmation


def confirm(request, confirmation_key):
    confirmation_key = confirmation_key.lower()
    obj = Confirmation.objects.confirm(confirmation_key)
    confirmed = True
    if not obj:
        # confirmation failed
        confirmed = False
        try:
            # try to get the object we was supposed to confirm
            obj = Confirmation.objects.get(confirmation_key=confirmation_key)
        except Confirmation.DoesNotExist:
            pass
    ctx = {
        'object': obj,
        'confirmed': confirmed,
        'days': getattr(settings, 'EMAIL_CONFIRMATION_DAYS', 10),
        'key': confirmation_key,
    }
    templates = [
        'confirmation/confirm.html',
    ]
    if obj:
        # if we have an object, we can use specific template
        templates.insert(0, 'confirmation/confirm_%s.html' % obj._meta.module_name)
    return render_to_response(templates, ctx,
        context_instance=RequestContext(request))


# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Confirmation'
        db.create_table('confirmation_confirmation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('date_sent', self.gf('django.db.models.fields.DateTimeField')()),
            ('confirmation_key', self.gf('django.db.models.fields.CharField')(max_length=40)),
        ))
        db.send_create_signal('confirmation', ['Confirmation'])


    def backwards(self, orm):
        # Deleting model 'Confirmation'
        db.delete_table('confirmation_confirmation')


    models = {
        'confirmation.confirmation': {
            'Meta': {'object_name': 'Confirmation'},
            'confirmation_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'date_sent': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['confirmation']


# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: cleanupconfirmation.py 5 2008-11-18 09:10:12Z jarek.zgoda $'


from django.core.management.base import NoArgsCommand

from confirmation.models import Confirmation


class Command(NoArgsCommand):
    help = 'Delete expired confirmations from database'

    def handle_noargs(self, **options):
        Confirmation.objects.delete_expired_confirmations()


#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright Â© 2012 Humbug, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import simplejson
import requests
import time
import traceback
import urlparse
import sys
import os
import optparse

from ConfigParser import SafeConfigParser

# Check that we have a recent enough version
# Older versions don't provide the 'json' attribute on responses.
assert(requests.__version__ > '0.12')
API_VERSTRING = "/api/v1/"

def generate_option_group(parser):
    group = optparse.OptionGroup(parser, 'API configuration')
    group.add_option('--site',
                      default='https://humbughq.com',
                      help=optparse.SUPPRESS_HELP)
    group.add_option('--api-key',
                     action='store')
    group.add_option('--user',
                     dest='email',
                     help='Email address of the calling user.')
    group.add_option('--config-file',
                     action='store',
                     help='Location of an ini file containing the above information.')
    group.add_option('-v', '--verbose',
                     action='store_true',
                     help='Provide detailed output.')

    return group

def init_from_options(options):
    return Client(email=options.email, api_key=options.api_key, config_file=options.config_file,
                  verbose=options.verbose, site=options.site)

class Client(object):
    def __init__(self, email=None, api_key=None, config_file=None,
                 verbose=False, retry_on_errors=True,
                 site="https://humbughq.com", client="API"):
        if None in (api_key, email):
            if config_file is None:
                config_file = os.path.join(os.environ["HOME"], ".humbugrc")
            if not os.path.exists(config_file):
                raise RuntimeError("api_key or email not specified and %s does not exist"
                                   % (config_file,))
            config = SafeConfigParser()
            with file(config_file, 'r') as f:
                config.readfp(f, config_file)
            if api_key is None:
                api_key = config.get("api", "key")
            if email is None:
                email = config.get("api", "email")

        self.api_key = api_key
        self.email = email
        self.verbose = verbose
        self.base_url = site
        self.retry_on_errors = retry_on_errors
        self.client_name = client

    def do_api_query(self, orig_request, url, longpolling = False):
        request = {}
        request["email"] = self.email
        request["api-key"] = self.api_key
        request["client"] = self.client_name

        for (key, val) in orig_request.iteritems():
            if not (isinstance(val, str) or isinstance(val, unicode)):
                request[key] = simplejson.dumps(val)
            else:
                request[key] = val

        query_state = {
            'had_error_retry': False,
            'request': request,
            'failures': 0,
        }

        def error_retry(error_string):
            if not self.retry_on_errors or query_state["failures"] >= 10:
                return False
            if self.verbose:
                if not query_state["had_error_retry"]:
                    sys.stdout.write("humbug API(%s): connection error%s -- retrying." % \
                            (url.split(API_VERSTRING, 2)[1], error_string,))
                    query_state["had_error_retry"] = True
                else:
                    sys.stdout.write(".")
                sys.stdout.flush()
            query_state["request"]["dont_block"] = simplejson.dumps(True)
            time.sleep(1)
            query_state["failures"] += 1
            return True

        def end_error_retry(succeeded):
            if query_state["had_error_retry"] and self.verbose:
                if succeeded:
                    print "Success!"
                else:
                    print "Failed!"

        while True:
            try:
                res = requests.post(urlparse.urljoin(self.base_url, url),
                                    data=query_state["request"],
                                    verify=True, timeout=55)

                # On 50x errors, try again after a short sleep
                if str(res.status_code).startswith('5'):
                    if error_retry(" (server %s)" % (res.status_code,)):
                        continue
                    # Otherwise fall through and process the python-requests error normally
            except (requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
                # Timeouts are either a Timeout or an SSLError; we
                # want the later exception handlers to deal with any
                # non-timeout other SSLErrors
                if (isinstance(e, requests.exceptions.SSLError) and
                    str(e) != "The read operation timed out"):
                    raise
                if longpolling:
                    # When longpolling, we expect the timeout to fire,
                    # and the correct response is to just retry
                    continue
                else:
                    end_error_retry(False)
                    return {'msg': "Connection error:\n%s" % traceback.format_exc(),
                            "result": "connection-error"}
            except requests.exceptions.ConnectionError:
                if error_retry(""):
                    continue
                end_error_retry(False)
                return {'msg': "Connection error:\n%s" % traceback.format_exc(),
                        "result": "connection-error"}
            except Exception:
                # We'll split this out into more cases as we encounter new bugs.
                return {'msg': "Unexpected error:\n%s" % traceback.format_exc(),
                        "result": "unexpected-error"}

            if res.json is not None:
                end_error_retry(True)
                return res.json
            end_error_retry(False)
            return {'msg': res.text, "result": "http-error",
                    "status_code": res.status_code}

    @classmethod
    def _register(cls, name, url=None, make_request=(lambda request={}: request), **query_kwargs):
        if url is None:
            url = name
        def call(self, *args, **kwargs):
            request = make_request(*args, **kwargs)
            return self.do_api_query(request, API_VERSTRING + url, **query_kwargs)
        call.func_name = name
        setattr(cls, name, call)

    def call_on_each_message(self, callback, options = {}):
        max_message_id = None
        while True:
            if max_message_id is not None:
                options["last"] = str(max_message_id)
            res = self.get_messages(options)
            if 'error' in res.get('result'):
                if self.verbose:
                    if res["result"] == "http-error":
                        print "HTTP error fetching messages -- probably a server restart"
                    elif res["result"] == "connection-error":
                        print "Connection error fetching messages -- probably server is temporarily down?"
                    else:
                        print "Server returned error:\n%s" % res["msg"]
                # TODO: Make this back off once it's more reliable
                time.sleep(1)
                continue
            for message in sorted(res['messages'], key=lambda x: int(x["id"])):
                max_message_id = max(max_message_id, int(message["id"]))
                callback(message)

def _mk_subs(streams):
    return {'subscriptions': streams}

Client._register('send_message', make_request=(lambda request: request))
Client._register('get_messages', longpolling=True)
Client._register('get_profile')
Client._register('get_public_streams')
Client._register('list_subscriptions',   url='subscriptions/list')
Client._register('add_subscriptions',    url='subscriptions/add',    make_request=_mk_subs)
Client._register('remove_subscriptions', url='subscriptions/remove', make_request=_mk_subs)

#!/usr/bin/python
# Copyright (C) 2012 Humbug, Inc.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import subprocess
import time
import optparse
import os
import traceback

from zephyr_mirror_backend import parse_args

(options, args) = parse_args()

args = [os.path.join(options.root_path, "user_root", "zephyr_mirror_backend.py")]
args.extend(sys.argv[1:])

if options.sync_subscriptions:
    subprocess.call(args)
    sys.exit(0)

if options.forward_class_messages and not options.noshard:
    sys.path.append("/home/humbug/humbug")
    from zephyr.lib.parallel import run_parallel
    print "Starting parallel zephyr class mirroring bot"
    jobs = list("0123456789abcdef")
    def run_job(shard):
        subprocess.call(args + ["--shard=%s" % (shard,)])
        return 0
    for (status, job) in run_parallel(run_job, jobs, threads=16):
        print "A mirroring shard died!"
        pass
    sys.exit(0)

while True:
    print "Starting zephyr mirroring bot"
    try:
        subprocess.call(args)
    except:
        traceback.print_exc()
    time.sleep(1)


#!/usr/bin/python
# Copyright (C) 2012 Humbug, Inc.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import traceback
import simplejson
import re
import time
import subprocess
import optparse
import os
import datetime
import textwrap
import signal
import logging
import hashlib
import unicodedata
import tempfile

DEFAULT_SITE = "https://humbughq.com"

def to_humbug_username(zephyr_username):
    if "@" in zephyr_username:
        (user, realm) = zephyr_username.split("@")
    else:
        (user, realm) = (zephyr_username, "ATHENA.MIT.EDU")
    if realm.upper() == "ATHENA.MIT.EDU":
        return user.lower() + "@mit.edu"
    return user.lower() + "|" + realm.upper() + "@mit.edu"

def to_zephyr_username(humbug_username):
    (user, realm) = humbug_username.split("@")
    if "|" not in user:
        return user.lower() + "@ATHENA.MIT.EDU"
    match_user = re.match(r'([a-zA-Z0-9_]+)\|(.+)', user)
    if not match_user:
        raise Exception("Could not parse Zephyr realm for cross-realm user %s" % (humbug_username,))
    return match_user.group(1).lower() + "@" + match_user.group(2).upper()

# Checks whether the pair of adjacent lines would have been
# linewrapped together, had they been intended to be parts of the same
# paragraph.  Our check is whether if you move the first word on the
# 2nd line onto the first line, the resulting line is either (1)
# significantly shorter than the following line (which, if they were
# in the same paragraph, should have been wrapped in a way consistent
# with how the previous line was wrapped) or (2) shorter than 60
# characters (our assumed minimum linewrapping threshhold for Zephyr)
# or (3) the first word of the next line is longer than this entire
# line.
def different_paragraph(line, next_line):
    words = next_line.split()
    return (len(line + " " + words[0]) < len(next_line) * 0.8 or
            len(line + " " + words[0]) < 50 or
            len(line) < len(words[0]))

# Linewrapping algorithm based on:
# http://gcbenison.wordpress.com/2011/07/03/a-program-to-intelligently-remove-carriage-returns-so-you-can-paste-text-without-having-it-look-awful/
def unwrap_lines(body):
    lines = body.split("\n")
    result = ""
    previous_line = lines[0]
    for line in lines[1:]:
        line = line.rstrip()
        if (re.match(r'^\W', line, flags=re.UNICODE)
            and re.match(r'^\W', previous_line, flags=re.UNICODE)):
            result += previous_line + "\n"
        elif (line == "" or
            previous_line == "" or
            re.match(r'^\W', line, flags=re.UNICODE) or
            different_paragraph(previous_line, line)):
            # Use 2 newlines to separate sections so that we
            # trigger proper Markdown processing on things like
            # bulleted lists
            result += previous_line + "\n\n"
        else:
            result += previous_line + " "
        previous_line = line
    result += previous_line
    return result

def send_humbug(zeph):
    message = {}
    if options.forward_class_messages:
        message["forged"] = "yes"
    message['type'] = zeph['type']
    message['time'] = zeph['time']
    message['sender'] = to_humbug_username(zeph['sender'])
    if "subject" in zeph:
        # Truncate the subject to the current limit in Humbug.  No
        # need to do this for stream names, since we're only
        # subscribed to valid stream names.
        message["subject"] = zeph["subject"][:60]
    if zeph['type'] == 'stream':
        # Forward messages sent to -c foo -i bar to stream bar subject "instance"
        if zeph["stream"] == "message":
            message['to'] = zeph['subject'].lower()
            message['subject'] = "instance %s" % (zeph['subject'],)
        elif zeph["stream"] == "tabbott-test5":
            message['to'] = zeph['subject'].lower()
            message['subject'] = "test instance %s" % (zeph['subject'],)
        else:
            message["to"] = zeph["stream"]
    else:
        message["to"] = zeph["recipient"]
    message['content'] = unwrap_lines(zeph['content'])

    if options.test_mode and options.site == DEFAULT_SITE:
        logger.debug("Message is: %s" % (str(message),))
        return {'result': "success"}

    return humbug_client.send_message(message)

def send_error_humbug(error_msg):
    message = {"type": "private",
               "sender": humbug_account_email,
               "to": humbug_account_email,
               "content": error_msg,
               }
    humbug_client.send_message(message)

current_zephyr_subs = set()
def zephyr_bulk_subscribe(subs):
    try:
        zephyr._z.subAll(subs)
    except IOError:
        # Since we haven't added the subscription to
        # current_zephyr_subs yet, we can just return (so that we'll
        # continue processing normal messages) and we'll end up
        # retrying the next time the bot checks its subscriptions are
        # up to date.
        logger.exception("Error subscribing to streams (will retry automatically):")
        logging.warning("Streams were: %s" % (list(cls for cls, instance, recipient in subs),))
        return
    try:
        actual_zephyr_subs = [cls for (cls, _, _) in zephyr._z.getSubscriptions()]
    except IOError:
        logging.exception("Error getting current Zephyr subscriptions")
        # Don't add anything to current_zephyr_subs so that we'll
        # retry the next time we check for streams to subscribe to
        # (within 15 seconds).
        return
    for (cls, instance, recipient) in subs:
        if cls not in actual_zephyr_subs:
            logging.error("Zephyr failed to subscribe us to %s; will retry" % (cls,))
            try:
                # We'll retry automatically when we next check for
                # streams to subscribe to (within 15 seconds), but
                # it's worth doing 1 retry immediately to avoid
                # missing 15 seconds of messages on the affected
                # classes
                zephyr._z.sub(cls, instance, recipient)
            except IOError:
                pass
        else:
            current_zephyr_subs.add(cls)

def update_subscriptions_from_humbug():
    try:
        res = humbug_client.get_public_streams()
        if res.get("result") == "success":
            streams = res["streams"]
        else:
            logger.error("Error getting public streams:\n%s" % res)
            return
    except Exception:
        logger.exception("Error getting public streams:")
        return
    classes_to_subscribe = set()
    for stream in streams:
        # Zephyr class names are canonicalized by first applying NFKC
        # normalization and then lower-casing server-side
        canonical_cls = unicodedata.normalize("NFKC", stream).lower().encode("utf-8")
        if canonical_cls in current_zephyr_subs:
            continue
        if canonical_cls in ['security', 'login', 'network', 'ops', 'user_locate',
                             'mit',
                             'hm_ctl', 'hm_stat', 'zephyr_admin', 'zephyr_ctl']:
            # These zephyr classes cannot be subscribed to by us, due
            # to MIT's Zephyr access control settings
            continue
        if (options.shard is not None and
            not hashlib.sha1(canonical_cls).hexdigest().startswith(options.shard)):
            # This stream is being handled by a different zephyr_mirror job.
            continue

        classes_to_subscribe.add((canonical_cls, "*", "*"))
    if len(classes_to_subscribe) > 0:
        zephyr_bulk_subscribe(list(classes_to_subscribe))

def maybe_restart_mirroring_script():
    if os.stat(os.path.join(options.root_path, "stamps", "restart_stamp")).st_mtime > start_time or \
            ((options.user == "tabbott" or options.user == "tabbott/extra") and
             os.stat(os.path.join(options.root_path, "stamps", "tabbott_stamp")).st_mtime > start_time):
        logger.warning("")
        logger.warning("zephyr mirroring script has been updated; restarting...")
        try:
            if child_pid is not None:
                os.kill(child_pid, signal.SIGTERM)
        except OSError:
            # We don't care if the child process no longer exists, so just print the error
            logging.exception("")
        try:
            zephyr._z.cancelSubs()
        except IOError:
            # We don't care whether we failed to cancel subs properly, but we should log it
            logging.exception("")
        while True:
            try:
                os.execvp(os.path.join(options.root_path, "user_root", "zephyr_mirror_backend.py"), sys.argv)
            except Exception:
                logger.exception("Error restarting mirroring script; trying again... Traceback:")
                time.sleep(1)

def process_loop(log):
    sleep_count = 0
    sleep_time = 0.1
    while True:
        try:
            notice = zephyr.receive(block=False)
        except Exception:
            logger.exception("Error checking for new zephyrs:")
            time.sleep(1)
            continue
        if notice is not None:
            try:
                process_notice(notice, log)
            except Exception:
                logger.exception("Error relaying zephyr:")
                time.sleep(2)

        try:
            maybe_restart_mirroring_script()
        except Exception:
            logging.exception("Error checking whether restart is required:")

        time.sleep(sleep_time)
        sleep_count += sleep_time
        if sleep_count > 15:
            sleep_count = 0
            if options.forward_class_messages:
                # Ask the Humbug server about any new classes to subscribe to
                try:
                    update_subscriptions_from_humbug()
                except Exception:
                    logging.exception("Error updating subscriptions from Humbug:")

def parse_zephyr_body(zephyr_data):
    try:
        (zsig, body) = zephyr_data.split("\x00", 1)
    except ValueError:
        (zsig, body) = ("", zephyr_data)
    return (zsig, body)

def process_notice(notice, log):
    (zsig, body) = parse_zephyr_body(notice.message)
    is_personal = False
    is_huddle = False

    if notice.opcode == "PING":
        # skip PING messages
        return

    zephyr_class = notice.cls.lower()

    if notice.recipient != "":
        is_personal = True
    # Drop messages not to the listed subscriptions
    if is_personal and not options.forward_personals:
        return
    if (zephyr_class not in current_zephyr_subs) and not is_personal:
        logger.debug("Skipping ... %s/%s/%s" %
                     (zephyr_class, notice.instance, is_personal))
        return
    if notice.format.endswith("@(@color(blue))"):
        logger.debug("Skipping message we got from Humbug!")
        return

    if is_personal:
        if body.startswith("CC:"):
            is_huddle = True
            # Map "CC: sipbtest espuser" => "starnine@mit.edu,espuser@mit.edu"
            huddle_recipients = [to_humbug_username(x.strip()) for x in
                                 body.split("\n")[0][4:].split()]
            if notice.sender not in huddle_recipients:
                huddle_recipients.append(to_humbug_username(notice.sender))
            body = body.split("\n", 1)[1]

    zeph = { 'time'      : str(notice.time),
             'sender'    : notice.sender,
             'zsig'      : zsig,  # logged here but not used by app
             'content'   : body }
    if is_huddle:
        zeph['type'] = 'private'
        zeph['recipient'] = huddle_recipients
    elif is_personal:
        zeph['type'] = 'private'
        zeph['recipient'] = to_humbug_username(notice.recipient)
    else:
        zeph['type'] = 'stream'
        zeph['stream'] = zephyr_class
        if notice.instance.strip() != "":
            zeph['subject'] = notice.instance
        else:
            zeph["subject"] = '(instance "%s")' % (notice.instance,)

    # Add instances in for instanced personals
    if is_personal:
        if notice.cls.lower() != "message" and notice.instance.lower != "personal":
            heading = "[-c %s -i %s]\n" % (notice.cls, notice.instance)
        elif notice.cls.lower() != "message":
            heading = "[-c %s]\n" % (notice.cls,)
        elif notice.instance.lower() != "personal":
            heading = "[-i %s]\n" % (notice.instance,)
        else:
            heading = ""
        zeph["content"] = heading + zeph["content"]

    zeph = decode_unicode_byte_strings(zeph)

    logger.info("Received a message on %s/%s from %s..." %
                (zephyr_class, notice.instance, notice.sender))
    if log is not None:
        log.write(simplejson.dumps(zeph) + '\n')
        log.flush()

    if os.fork() == 0:
        # Actually send the message in a child process, to avoid blocking.
        try:
            res = send_humbug(zeph)
            if res.get("result") != "success":
                logger.error("Error relaying zephyr:\n%s\n%s" % (zeph, res))
        except Exception:
            logging.exception("Error relaying zephyr:")
        finally:
            os._exit(0)

def decode_unicode_byte_strings(zeph):
    for field in zeph.keys():
        if isinstance(zeph[field], str):
            try:
                decoded = zeph[field].decode("utf-8")
            except Exception:
                decoded = zeph[field].decode("iso-8859-1")
            zeph[field] = decoded
    return zeph

def zephyr_subscribe_autoretry(sub):
    while True:
        try:
            zephyr.Subscriptions().add(sub)
            return
        except IOError:
            # Probably a SERVNAK from the zephyr server, but print the
            # traceback just in case it's something else
            logger.exception("Error subscribing to personals (retrying).  Traceback:")
            time.sleep(1)

def zephyr_to_humbug(options):
    if options.forward_class_messages:
        update_subscriptions_from_humbug()
    if options.forward_personals:
        # Subscribe to personals; we really can't operate without
        # those subscriptions, so just retry until it works.
        zephyr_subscribe_autoretry(("message", "*", "%me%"))
        if subscribed_to_mail_messages():
            zephyr_subscribe_autoretry(("mail", "inbox", "%me%"))

    if options.resend_log_path is not None:
        with open(options.resend_log_path, 'r') as log:
            for ln in log:
                try:
                    zeph = simplejson.loads(ln)
                    # New messages added to the log shouldn't have any
                    # elements of type str (they should already all be
                    # unicode), but older messages in the log are
                    # still of type str, so convert them before we
                    # send the message
                    zeph = decode_unicode_byte_strings(zeph)
                    # Handle importing older zephyrs in the logs
                    # where it isn't called a "stream" yet
                    if "class" in zeph:
                        zeph["stream"] = zeph["class"]
                    if "instance" in zeph:
                        zeph["subject"] = zeph["instance"]
                    logger.info("sending saved message to %s from %s..." %
                                (zeph.get('stream', zeph.get('recipient')),
                                 zeph['sender']))
                    send_humbug(zeph)
                except Exception:
                    logger.exception("Could not send saved zephyr:")
                    time.sleep(2)

    logger.info("Starting receive loop.")

    if options.log_path is not None:
        with open(options.log_path, 'a') as log:
            process_loop(log)
    else:
        process_loop(None)

def send_zephyr(zwrite_args, content):
    p = subprocess.Popen(zwrite_args, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(input=content.encode("utf-8"))
    if p.returncode:
        logging.error("zwrite command '%s' failed with return code %d:" % (
            " ".join(zwrite_args), p.returncode,))
        if stdout:
            logging.info("stdout: " + stdout)
    elif stderr:
        logging.warning("zwrite command '%s' printed the following warning:" % (
            " ".join(zwrite_args),))
    if stderr:
        logging.warning("stderr: " + stderr)
    return (p.returncode, stderr)

def send_authed_zephyr(zwrite_args, content):
    return send_zephyr(zwrite_args, content)

def send_unauthed_zephyr(zwrite_args, content):
    return send_zephyr(zwrite_args + ["-d"], content)

def forward_to_zephyr(message):
    wrapper = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)
    wrapped_content = "\n".join("\n".join(wrapper.wrap(line))
            for line in message["content"].split("\n"))

    zwrite_args = ["zwrite", "-n", "-s", zsig_fullname, "-F", "http://zephyr.1ts.org/wiki/df @(@color(blue))"]
    if message['type'] == "stream":
        zephyr_class = message["display_recipient"]
        instance = message["subject"]

        match_whitespace_instance = re.match(r'^\(instance "(\s*)"\)$', instance)
        if match_whitespace_instance:
            # Forward messages sent to '(instance "WHITESPACE")' back to the
            # appropriate WHITESPACE instance for bidirectional mirroring
            instance = match_whitespace_instance.group(1)
        elif (instance == "instance %s" % (zephyr_class,) or
            instance == "test instance %s" % (zephyr_class,)):
            # Forward messages to e.g. -c -i white-magic back from the
            # place we forward them to
            if instance.startswith("test"):
                instance = zephyr_class
                zephyr_class = "tabbott-test5"
            else:
                instance = zephyr_class
                zephyr_class = "message"
        zwrite_args.extend(["-c", zephyr_class, "-i", instance])
        logger.info("Forwarding message to class %s, instance %s" % (zephyr_class, instance))
    elif message['type'] == "private":
        if len(message['display_recipient']) == 1:
            recipient = to_zephyr_username(message["display_recipient"][0]["email"])
            recipients = [recipient]
        elif len(message['display_recipient']) == 2:
            recipient = ""
            for r in message["display_recipient"]:
                if r["email"].lower() != humbug_account_email.lower():
                    recipient = to_zephyr_username(r["email"])
                    break
            recipients = [recipient]
        else:
            zwrite_args.extend(["-C"])
            # We drop the @ATHENA.MIT.EDU here because otherwise the
            # "CC: user1 user2 ..." output will be unnecessarily verbose.
            recipients = [to_zephyr_username(user["email"]).replace("@ATHENA.MIT.EDU", "")
                          for user in message["display_recipient"]]
        logger.info("Forwarding message to %s" % (recipients,))
        zwrite_args.extend(recipients)

    if options.test_mode:
        logger.debug("Would have forwarded: %s\n%s" %
                     (zwrite_args, wrapped_content.encode("utf-8")))
        return

    heading = "Hi there! This is an automated message from Humbug."
    support_closing = """If you have any questions, please be in touch through the \
Feedback tab or at support@humbughq.com."""

    (code, stderr) = send_authed_zephyr(zwrite_args, wrapped_content)
    if code == 0 and stderr == "":
        return
    elif code == 0:
        return send_error_humbug("""%s

Your last message was successfully mirrored to zephyr, but zwrite \
returned the following warning:

%s

%s""" % (heading, stderr, support_closing))
    elif code != 0 and (stderr.startswith("zwrite: Ticket expired while sending notice to ") or
                        stderr.startswith("zwrite: No credentials cache found while sending notice to ")):
        # Retry sending the message unauthenticated; if that works,
        # just notify the user that they need to renew their tickets
        (code, stderr) = send_unauthed_zephyr(zwrite_args, wrapped_content)
        if code == 0:
            return send_error_humbug("""%s

Your last message was forwarded from Humbug to Zephyr unauthenticated, \
because your Kerberos tickets have expired. It was sent successfully, \
but please renew your Kerberos tickets in the screen session where you \
are running the Humbug-Zephyr mirroring bot, so we can send \
authenticated Zephyr messages for you again.

%s""" % (heading, support_closing))

    # zwrite failed and it wasn't because of expired tickets: This is
    # probably because the recipient isn't subscribed to personals,
    # but regardless, we should just notify the user.
    return send_error_humbug("""%s

Your Humbug-Zephyr mirror bot was unable to forward that last message \
from Humbug to Zephyr. That means that while Humbug users (like you) \
received it, Zephyr users did not.  The error message from zwrite was:

%s

%s""" % (heading, stderr, support_closing))

def maybe_forward_to_zephyr(message):
    if (message["sender_email"] == humbug_account_email):
        if not ((message["type"] == "stream") or
                (message["type"] == "private" and
                 False not in [u["email"].lower().endswith("mit.edu") for u in
                               message["display_recipient"]])):
            # Don't try forward private messages with non-MIT users
            # to MIT Zephyr.
            return
        timestamp_now = datetime.datetime.now().strftime("%s")
        if float(message["timestamp"]) < float(timestamp_now) - 15:
            logger.warning("Skipping out of order message: %s < %s" %
                           (message["timestamp"], timestamp_now))
            return
        try:
            forward_to_zephyr(message)
        except Exception:
            # Don't let an exception forwarding one message crash the
            # whole process
            logger.exception("Error forwarding message:")

def humbug_to_zephyr(options):
    # Sync messages from zephyr to humbug
    logger.info("Starting syncing messages.")
    while True:
        try:
            humbug_client.call_on_each_message(maybe_forward_to_zephyr)
        except Exception:
            logger.exception("Error syncing messages:")
            time.sleep(1)

def subscribed_to_mail_messages():
    # In case we have lost our AFS tokens and those won't be able to
    # parse the Zephyr subs file, first try reading in result of this
    # query from the environment so we can avoid the filesystem read.
    stored_result = os.environ.get("HUMBUG_FORWARD_MAIL_ZEPHYRS")
    if stored_result is not None:
        return stored_result == "True"
    for (cls, instance, recipient) in parse_zephyr_subs(verbose=False):
        if (cls.lower() == "mail" and instance.lower() == "inbox"):
            os.environ["HUMBUG_FORWARD_MAIL_ZEPHYRS"] = "True"
            return True
    os.environ["HUMBUG_FORWARD_MAIL_ZEPHYRS"] = "False"
    return False

def add_humbug_subscriptions(verbose):
    zephyr_subscriptions = set()
    skipped = set()
    for (cls, instance, recipient) in parse_zephyr_subs(verbose=verbose):
        if cls.lower() == "message":
            if recipient != "*":
                # We already have a (message, *, you) subscription, so
                # these are redundant
                continue
            # We don't support subscribing to (message, *)
            if instance == "*":
                if recipient == "*":
                    skipped.add((cls, instance, recipient, "subscribing to all of class message is not supported."))
                continue
            # If you're on -i white-magic on zephyr, get on stream white-magic on humbug
            # instead of subscribing to stream "message" on humbug
            zephyr_subscriptions.add(instance)
            continue
        elif cls.lower() == "mail" and instance.lower() == "inbox":
            # We forward mail zephyrs, so no need to print a warning.
            continue
        elif len(cls) > 30:
            skipped.add((cls, instance, recipient, "Class longer than 30 characters"))
            continue
        elif instance != "*":
            skipped.add((cls, instance, recipient, "Unsupported non-* instance"))
            continue
        elif recipient != "*":
            skipped.add((cls, instance, recipient, "Unsupported non-* recipient."))
            continue
        zephyr_subscriptions.add(cls)

    if len(zephyr_subscriptions) != 0:
        res = humbug_client.add_subscriptions(list(zephyr_subscriptions))
        if res.get("result") != "success":
            print "Error subscribing to streams:"
            print res["msg"]
            return

        already = res.get("already_subscribed")
        new = res.get("subscribed")
        if verbose:
            if already is not None and len(already) > 0:
                print
                print "Already subscribed to:", ", ".join(already)
            if new is not None and len(new) > 0:
                print
                print "Successfully subscribed to:",  ", ".join(new)

    if len(skipped) > 0:
        if verbose:
            print
            print "\n".join(textwrap.wrap("""\
You have some lines in ~/.zephyr.subs that could not be
synced to your Humbug subscriptions because they do not
use "*" as both the instance and recipient and not one of
the special cases (e.g. personals and mail zephyrs) that
Humbug has a mechanism for forwarding.  Humbug does not
allow subscribing to only some subjects on a Humbug
stream, so this tool has not created a corresponding
Humbug subscription to these lines in ~/.zephyr.subs:
"""))
            print

    for (cls, instance, recipient, reason) in skipped:
        if verbose:
            if reason != "":
                print "  [%s,%s,%s] (%s)" % (cls, instance, recipient, reason)
            else:
                print "  [%s,%s,%s]" % (cls, instance, recipient, reason)
    if len(skipped) > 0:
        if verbose:
            print
            print "\n".join(textwrap.wrap("""\
If you wish to be subscribed to any Humbug streams related
to these .zephyrs.subs lines, please do so via the Humbug
web interface.
"""))
            print
    if verbose:
        print
        print "IMPORTANT: Please reload the Humbug app for these changes to take effect."

def valid_stream_name(name):
    return name != ""

def parse_zephyr_subs(verbose=False):
    zephyr_subscriptions = set()
    subs_file = os.path.join(os.environ["HOME"], ".zephyr.subs")
    if not os.path.exists(subs_file):
        if verbose:
            print >>sys.stderr, "Couldn't find ~/.zephyr.subs!"
        return []

    for line in file(subs_file, "r").readlines():
        line = line.strip()
        if len(line) == 0:
            continue
        try:
            (cls, instance, recipient) = line.split(",")
            cls = cls.replace("%me%", options.user)
            instance = instance.replace("%me%", options.user)
            recipient = recipient.replace("%me%", options.user)
            if not valid_stream_name(cls):
                if verbose:
                    print >>sys.stderr, "Skipping subscription to unsupported class name: [%s]" % (line,)
                continue
        except Exception:
            if verbose:
                print >>sys.stderr, "Couldn't parse ~/.zephyr.subs line: [%s]" % (line,)
            continue
        zephyr_subscriptions.add((cls.strip(), instance.strip(), recipient.strip()))
    return zephyr_subscriptions

def fetch_fullname(username):
    try:
        proc = subprocess.Popen(['hesinfo', username, 'passwd'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, _err_unused = proc.communicate()
        if proc.returncode == 0:
            return out.split(':')[4].split(',')[0]
    except Exception:
        logger.exception("Error getting fullname for %s:" % (username,))

    return username

def configure_logger(direction_name):
    if options.forward_class_messages:
        if options.test_mode:
            log_file = "/home/humbug/test-mirror-log"
        else:
            log_file = "/home/humbug/mirror-log"
    else:
        f = tempfile.NamedTemporaryFile(prefix="humbug-log.%s." % (options.user,),
                                        delete=False)
        log_file = f.name
        # Close the file descriptor, since the logging system will
        # reopen it anyway.
        f.close()
    logger = logging.getLogger(__name__)
    log_format = "%(asctime)s " + direction_name + ": %(message)s"
    formatter = logging.Formatter(log_format)
    logging.basicConfig(format=log_format)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

def parse_args():
    parser = optparse.OptionParser()
    parser.add_option('--forward-class-messages',
                      default=False,
                      help=optparse.SUPPRESS_HELP,
                      action='store_true')
    parser.add_option('--shard',
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--noshard',
                      default=False,
                      help=optparse.SUPPRESS_HELP,
                      action='store_true')
    parser.add_option('--resend-log',
                      dest='resend_log_path',
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--enable-log',
                      dest='log_path',
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--no-forward-personals',
                      dest='forward_personals',
                      help=optparse.SUPPRESS_HELP,
                      default=True,
                      action='store_false')
    parser.add_option('--no-forward-from-humbug',
                      default=True,
                      dest='forward_from_humbug',
                      help=optparse.SUPPRESS_HELP,
                      action='store_false')
    parser.add_option('--verbose',
                      default=False,
                      help=optparse.SUPPRESS_HELP,
                      action='store_true')
    parser.add_option('--sync-subscriptions',
                      default=False,
                      action='store_true')
    parser.add_option('--site',
                      default=DEFAULT_SITE,
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--user',
                      default=os.environ["USER"],
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--root-path',
                      default="/afs/athena.mit.edu/user/t/a/tabbott/for_friends",
                      help=optparse.SUPPRESS_HELP)
    parser.add_option('--test-mode',
                      default=False,
                      help=optparse.SUPPRESS_HELP,
                      action='store_true')
    parser.add_option('--api-key-file',
                      default=os.path.join(os.environ["HOME"], "Private", ".humbug-api-key"))
    return parser.parse_args()

if __name__ == "__main__":
    # Set the SIGCHLD handler back to SIG_DFL to prevent these errors
    # when importing the "requests" module after being restarted using
    # the restart_stamp functionality:
    #
    # close failed in file object destructor:
    # IOError: [Errno 10] No child processes
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)

    (options, args) = parse_args()

    # The 'api' directory needs to go first, so that 'import humbug' won't pick
    # up some other directory named 'humbug'.
    pyzephyr_lib_path = "python-zephyr/build/lib.linux-" + os.uname()[4] + "-2.6/"
    sys.path[:0] = [os.path.join(options.root_path, 'api'),
                    options.root_path,
                    os.path.join(options.root_path, "python-zephyr"),
                    os.path.join(options.root_path, pyzephyr_lib_path)]

    # In case this is an automated restart of the mirroring script,
    # and we have lost AFS tokens, first try reading the API key from
    # the environment so that we can skip doing a filesystem read.
    if os.environ.get("HUMBUG_API_KEY") is not None:
        api_key = os.environ.get("HUMBUG_API_KEY")
    else:
        if not os.path.exists(options.api_key_file):
            print "\n".join(textwrap.wrap("""\
Could not find API key file.
You need to either place your api key file at %s,
or specify the --api-key-file option.""" % (options.api_key_file,)))
            sys.exit(1)
        api_key = file(options.api_key_file).read().strip()
        # Store the API key in the environment so that our children
        # don't need to read it in
        os.environ["HUMBUG_API_KEY"] = api_key

    humbug_account_email = options.user + "@mit.edu"
    import humbug
    humbug_client = humbug.Client(
        email=humbug_account_email,
        api_key=api_key,
        verbose=True,
        client="zephyr_mirror",
        site=options.site)

    start_time = time.time()

    if options.sync_subscriptions:
        print "Syncing your ~/.zephyr.subs to your Humbug Subscriptions!"
        add_humbug_subscriptions(True)
        sys.exit(0)

    # Kill all zephyr_mirror processes other than this one and its parent.
    if not options.test_mode:
        pgrep_query = "/usr/bin/python.*zephyr_mirror"
        if options.shard is not None:
            pgrep_query = "%s.*--shard=%s" % (pgrep_query, options.shard)
        proc = subprocess.Popen(['pgrep', '-U', os.environ["USER"], "-f", pgrep_query],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, _err_unused = proc.communicate()
        for pid in map(int, out.split()):
            if pid == os.getpid() or pid == os.getppid():
                continue

            # Another copy of zephyr_mirror.py!  Kill it.
            print "Killing duplicate zephyr_mirror process %s" % (pid,)
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                # We don't care if the target process no longer exists, so just print the error
                traceback.print_exc()

    if options.shard is not None and set(options.shard) != set("a"):
        # The shard that is all "a"s is the one that handles personals
        # forwarding and humbug => zephyr forwarding
        options.forward_personals = False
        options.forward_from_humbug = False

    if options.forward_from_humbug:
        child_pid = os.fork()
        if child_pid == 0:
            # Run the humbug => zephyr mirror in the child
            logger = configure_logger("humbug=>zephyr")
            zsig_fullname = fetch_fullname(options.user)
            humbug_to_zephyr(options)
            sys.exit(0)
    else:
        child_pid = None

    import zephyr
    while True:
        try:
            # zephyr.init() tries to clear old subscriptions, and thus
            # sometimes gets a SERVNAK from the server
            zephyr.init()
            break
        except IOError:
            traceback.print_exc()
            time.sleep(1)
    logger_name = "zephyr=>humbug"
    if options.shard is not None:
        logger_name += "(%s)" % (options.shard,)
    logger = configure_logger(logger_name)
    # Have the kernel reap children for when we fork off processes to send Humbugs
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    zephyr_to_humbug(options)

#!/usr/bin/python
#
# Humbug trac plugin -- sends humbugs when tickets change.
#
# Install by placing in the plugins/ subdirectory and then adding
# "humbug_trac" to the [components] section of the conf/trac.ini file,
# like so:
#
# [components]
# humbug_trac = enabled
#
# You may then need to restart trac (or restart Apache) for the bot
# (or changes to the bot) to actually be loaded by trac.
#
# Our install is trac.humbughq.com:/home/humbug/trac/

from trac.core import Component, implements
from trac.ticket import ITicketChangeListener
import sys

sys.path.append("/home/humbug/humbug/api")
import humbug
client = humbug.Client(
    email="humbug+trac@humbughq.com",
    site="https://staging.humbughq.com",
    api_key="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

def markdown_ticket_url(ticket, heading="ticket"):
    return "[%s #%s](https://trac.humbughq.com/ticket/%s)" % (heading, ticket.id, ticket.id)

def markdown_block(desc):
    return "\n\n>" + "\n> ".join(desc.split("\n")) + "\n"

def truncate(string, length):
    if len(string) <= length:
        return string
    return string[:length - 3] + "..."

def trac_subject(ticket):
    return truncate("#%s: %s" % (ticket.id, ticket.values.get("summary")), 60)

def send_update(ticket, content):
    client.send_message({
            "type": "stream",
            "to": "trac",
            "content": content,
            "subject": trac_subject(ticket)
            })

class HumbugPlugin(Component):
    implements(ITicketChangeListener)

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        content = "%s created %s in component **%s**, priority **%s**:\n" % \
            (ticket.values.get("reporter"), markdown_ticket_url(ticket),
             ticket.values.get("component"), ticket.values.get("priority"))
        if ticket.values.get("description") != "":
            content += "%s" % markdown_block(ticket.values.get("description"))
        send_update(ticket, content)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.

        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        if not comment and set(old_values.keys()) <= set(["priority", "milestone",
                                                          "cc", "keywords",
                                                          "component"]):
            # This is probably someone going through trac and updating
            # the priorities; this can result in a lot of messages
            # nobody wants to read, so don't send them without a comment.
            return

        content = "%s updated %s" % (author, markdown_ticket_url(ticket))
        if comment:
            content += ' with comment: %s\n\n' % (markdown_block(comment,))
        else:
            content += ":\n\n"
        field_changes = []
        for key in old_values.keys():
            if key == "description":
                content += '- Changed %s from %s to %s' % (key, markdown_block(old_values.get(key)),
                                                           markdown_block(ticket.values.get(key)))
            elif old_values.get(key) == "":
                field_changes.append('%s: => **%s**' % (key, ticket.values.get(key)))
            elif ticket.values.get(key) == "":
                field_changes.append('%s: **%s** => ""' % (key, old_values.get(key)))
            else:
                field_changes.append('%s: **%s** => **%s**' % (key, old_values.get(key),
                                                               ticket.values.get(key)))
        content += ", ".join(field_changes)

        send_update(ticket, content)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        content = "%s was deleted." % markdown_ticket_url(ticket, heading="Ticket")
        send_update(ticket, content)

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import hashlib
import base64
from zephyr.lib.cache import cache_with_key
from zephyr.lib.initial_password import initial_password, initial_api_key
import os
import simplejson
from django.db import transaction, IntegrityError
from zephyr.lib import bugdown
from zephyr.lib.bulk_create import batch_bulk_create
from zephyr.lib.avatar import gravatar_hash
from zephyr.lib.context_managers import lockfile
import requests
from django.contrib.auth.models import UserManager
from django.utils import timezone
from django.contrib.sessions.models import Session
import time
import subprocess
import traceback
import re
from django.utils.html import escape
from zephyr.lib.time import datetime_to_timestamp

MAX_SUBJECT_LENGTH = 60
MAX_MESSAGE_LENGTH = 10000

@cache_with_key(lambda self: 'display_recipient_dict:%d' % (self.id,))
def get_display_recipient(recipient):
    """
    recipient: an instance of Recipient.

    returns: an appropriate object describing the recipient.  For a
    stream this will be the stream name as a string.  For a huddle or
    personal, it will be an array of dicts about each recipient.
    """
    if recipient.type == Recipient.STREAM:
        stream = Stream.objects.get(id=recipient.type_id)
        return stream.name

    # We don't really care what the ordering is, just that it's deterministic.
    user_profile_list = (UserProfile.objects.filter(subscription__recipient=recipient)
                                            .select_related()
                                            .order_by('user__email'))
    return [{'email': user_profile.user.email,
             'full_name': user_profile.full_name,
             'short_name': user_profile.short_name} for user_profile in user_profile_list]

class Callbacks(object):
    TYPE_RECEIVE = 0
    TYPE_POINTER_UPDATE = 1
    TYPE_MAX = 2

    def __init__(self):
        self.table = {}

    def add(self, key, cb_type, callback):
        if not self.table.has_key(key):
            self.create_key(key)
        self.table[key][cb_type].append(callback)

    def call(self, key, cb_type, **kwargs):
        if not self.table.has_key(key):
            self.create_key(key)

        for cb in self.table[key][cb_type]:
            cb(**kwargs)

        self.table[key][cb_type] = []

    def create_key(self, key):
        self.table[key] = [[] for i in range(0, Callbacks.TYPE_MAX)]


class Realm(models.Model):
    domain = models.CharField(max_length=40, db_index=True, unique=True)

    def __repr__(self):
        return "<Realm: %s %s>" % (self.domain, self.id)
    def __str__(self):
        return self.__repr__()

def bulk_create_realms(realm_list):
    existing_realms = set(r.domain for r in Realm.objects.select_related().all())

    realms_to_create = []
    for domain in realm_list:
        if domain not in existing_realms:
            realms_to_create.append(Realm(domain=domain))
            existing_realms.add(domain)
    batch_bulk_create(Realm, realms_to_create)

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    full_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100)
    pointer = models.IntegerField()
    last_pointer_updater = models.CharField(max_length=64)
    realm = models.ForeignKey(Realm)
    api_key = models.CharField(max_length=32)
    enable_desktop_notifications = models.BooleanField(default=True)

    # This is class data, not instance data!
    # There is one callbacks_table for the whole process.
    callbacks_table = Callbacks()

    # The user receives this message
    # Called in the Tornado process
    def receive(self, message):
        self.callbacks_table.call(self.user.id, Callbacks.TYPE_RECEIVE,
            messages=[message], update_types=["new_messages"])

    def update_pointer(self, new_pointer, pointer_updater):
        self.callbacks_table.call(self.user.id, Callbacks.TYPE_POINTER_UPDATE,
                                  new_pointer=new_pointer,
                                  update_types=["pointer_update"])

    def add_receive_callback(self, cb):
        self.callbacks_table.add(self.user.id, Callbacks.TYPE_RECEIVE, cb)

    def add_pointer_update_callback(self, cb):
        self.callbacks_table.add(self.user.id, Callbacks.TYPE_POINTER_UPDATE, cb)

    def __repr__(self):
        return "<UserProfile: %s %s>" % (self.user.email, self.realm)
    def __str__(self):
        return self.__repr__()

    @classmethod
    def create(cls, user, realm, full_name, short_name):
        """When creating a new user, make a profile for him or her."""
        if not cls.objects.filter(user=user):
            profile = cls(user=user, pointer=-1, realm=realm,
                          full_name=full_name, short_name=short_name)
            profile.api_key = initial_api_key(user.email)
            profile.save()
            # Auto-sub to the ability to receive personals.
            recipient = Recipient.objects.create(type_id=profile.id, type=Recipient.PERSONAL)
            Subscription.objects.create(user_profile=profile, recipient=recipient)
            return profile

class PreregistrationUser(models.Model):
    email = models.EmailField(unique=True)
    # status: whether an object has been confirmed.
    #   if confirmed, set to confirmation.settings.STATUS_ACTIVE
    status = models.IntegerField(default=0)

class MitUser(models.Model):
    email = models.EmailField(unique=True)
    # status: whether an object has been confirmed.
    #   if confirmed, set to confirmation.settings.STATUS_ACTIVE
    status = models.IntegerField(default=0)

# create_user_hack is the same as Django's User.objects.create_user,
# except that we don't save to the database so it can used in
# bulk_creates
def create_user_hack(username, password, email, active):
    now = timezone.now()
    email = UserManager.normalize_email(email)
    user = User(username=username, email=email,
                is_staff=False, is_active=active, is_superuser=False,
                last_login=now, date_joined=now)

    if active:
        user.set_password(password)
    else:
        user.set_unusable_password()
    return user

def set_default_streams(realm, stream_names):
    DefaultStream.objects.filter(realm=realm).delete()
    for stream_name in stream_names:
        stream = create_stream_if_needed(realm, stream_name)
        DefaultStream.objects.create(stream=stream, realm=realm)

def add_default_subs(user_profile):
    for default in DefaultStream.objects.filter(realm=user_profile.realm):
        do_add_subscription(user_profile, default.stream)

def create_user_base(email, password, active=True):
    # NB: the result of Base32 + truncation is not a valid Base32 encoding.
    # It's just a unique alphanumeric string.
    # Use base32 instead of base64 so we don't have to worry about mixed case.
    # Django imposes a limit of 30 characters on usernames.
    email_hash = hashlib.sha256(settings.HASH_SALT + email).digest()
    username = base64.b32encode(email_hash)[:30]
    return create_user_hack(username, password, email, active)

def create_user(email, password, realm, full_name, short_name,
                active=True):
    user = create_user_base(email=email, password=password,
                            active=active)
    user.save()
    return UserProfile.create(user, realm, full_name, short_name)

def do_create_user(email, password, realm, full_name, short_name,
                   active=True):
    log_event({'type': 'user_created',
               'timestamp': time.time(),
               'full_name': full_name,
               'short_name': short_name,
               'user': email})
    return create_user(email, password, realm, full_name, short_name, active)

def compute_mit_user_fullname(email):
    try:
        # Input is either e.g. starnine@mit.edu or user|CROSSREALM.INVALID@mit.edu
        match_user = re.match(r'^([a-zA-Z0-9_.-]+)(\|.+)?@mit\.edu$', email.lower())
        if match_user and match_user.group(2) is None:
            dns_query = "%s.passwd.ns.athena.mit.edu" % (match_user.group(1),)
            proc = subprocess.Popen(['host', '-t', 'TXT', dns_query],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            out, _err_unused = proc.communicate()
            if proc.returncode == 0:
                # Parse e.g. 'starnine:*:84233:101:Athena Consulting Exchange User,,,:/mit/starnine:/bin/bash'
                # for the 4th passwd entry field, aka the person's name.
                hesiod_name = out.split(':')[4].split(',')[0].strip()
                if hesiod_name == "":
                    return email
                return hesiod_name
        elif match_user:
            return match_user.group(1).lower() + "@" + match_user.group(2).upper()[1:]
    except:
        print ("Error getting fullname for %s:" % (email,))
        traceback.print_exc()
    return email.lower()

def create_mit_user_if_needed(realm, email):
    try:
        return UserProfile.objects.get(user__email=email)
    except UserProfile.DoesNotExist:
        try:
            # Forge a user for this person
            return create_user(email, initial_password(email), realm,
                               compute_mit_user_fullname(email), email.split("@")[0],
                               active=False)
        except IntegrityError:
            # Unless we raced with another thread doing the same
            # thing, in which case we should get the user they made
            transaction.commit()
            return UserProfile.objects.get(user__email=email)

def bulk_create_users(realms, users_raw):
    """
    Creates and saves a User with the given email.
    Has some code based off of UserManage.create_user, but doesn't .save()
    """
    users = []
    existing_users = set(u.email for u in User.objects.all())
    for (email, full_name, short_name, active) in users_raw:
        if email in existing_users:
            continue
        users.append((email, full_name, short_name, active))
        existing_users.add(email)

    users_to_create = []
    for (email, full_name, short_name, active) in users:
        users_to_create.append(create_user_base(email, initial_password(email),
                                                active=active))
    batch_bulk_create(User, users_to_create, 30)

    users_by_email = {}
    for user in User.objects.all():
        users_by_email[user.email] = user

    # Now create user_profiles
    profiles_to_create = []
    for (email, full_name, short_name, active) in users:
        domain = email.split('@')[1]
        profile = UserProfile(user=users_by_email[email], pointer=-1,
                              realm=realms[domain],
                              full_name=full_name, short_name=short_name)
        profile.api_key = initial_api_key(email)
        profiles_to_create.append(profile)
    batch_bulk_create(UserProfile, profiles_to_create, 50)

    profiles_by_email = {}
    profiles_by_id = {}
    for profile in UserProfile.objects.select_related().all():
        profiles_by_email[profile.user.email] = profile
        profiles_by_id[profile.user.id] = profile

    recipients_to_create = []
    for (email, _, _, _) in users:
        recipients_to_create.append(Recipient(type_id=profiles_by_email[email].id,
                                              type=Recipient.PERSONAL))
    batch_bulk_create(Recipient, recipients_to_create)

    recipients_by_email = {}
    for recipient in Recipient.objects.filter(type=Recipient.PERSONAL):
        recipients_by_email[profiles_by_id[recipient.type_id].user.email] = recipient

    subscriptions_to_create = []
    for (email, _, _, _) in users:
        subscriptions_to_create.append(
            Subscription(user_profile_id=profiles_by_email[email].id,
                         recipient=recipients_by_email[email]))
    batch_bulk_create(Subscription, subscriptions_to_create)

def create_stream_if_needed(realm, stream_name):
    (stream, created) = Stream.objects.get_or_create(
        realm=realm, name__iexact=stream_name,
        defaults={'name': stream_name})
    if created:
        Recipient.objects.create(type_id=stream.id, type=Recipient.STREAM)
    return stream

def bulk_create_streams(realms, stream_list):
    existing_streams = set((stream.realm.domain, stream.name.lower())
                           for stream in Stream.objects.select_related().all())
    streams_to_create = []
    for (domain, name) in stream_list:
        if (domain, name.lower()) not in existing_streams:
            streams_to_create.append(Stream(realm=realms[domain], name=name))
    batch_bulk_create(Stream, streams_to_create)

    recipients_to_create = []
    for stream in Stream.objects.select_related().all():
        if (stream.realm.domain, stream.name.lower()) not in existing_streams:
            recipients_to_create.append(Recipient(type_id=stream.id,
                                                  type=Recipient.STREAM))
    batch_bulk_create(Recipient, recipients_to_create)

class Stream(models.Model):
    name = models.CharField(max_length=30, db_index=True)
    realm = models.ForeignKey(Realm, db_index=True)

    def __repr__(self):
        return "<Stream: %s>" % (self.name,)
    def __str__(self):
        return self.__repr__()

    class Meta:
        unique_together = ("name", "realm")

    @classmethod
    def create(cls, name, realm):
        stream = cls(name=name, realm=realm)
        stream.save()

        recipient = Recipient.objects.create(type_id=stream.id,
                                             type=Recipient.STREAM)
        return (stream, recipient)

class Recipient(models.Model):
    type_id = models.IntegerField(db_index=True)
    type = models.PositiveSmallIntegerField(db_index=True)
    # Valid types are {personal, stream, huddle}
    PERSONAL = 1
    STREAM = 2
    HUDDLE = 3

    class Meta:
        unique_together = ("type", "type_id")

    # N.B. If we used Django's choice=... we would get this for free (kinda)
    _type_names = {
        PERSONAL: 'personal',
        STREAM:   'stream',
        HUDDLE:   'huddle' }

    def type_name(self):
        # Raises KeyError if invalid
        return self._type_names[self.type]

    def __repr__(self):
        display_recipient = get_display_recipient(self)
        return "<Recipient: %s (%d, %s)>" % (display_recipient, self.type_id, self.type)

class Client(models.Model):
    name = models.CharField(max_length=30, db_index=True, unique=True)

@transaction.commit_on_success
def get_client(name):
    try:
        (client, _) = Client.objects.get_or_create(name=name)
    except IntegrityError:
        # If we're racing with other threads trying to create this
        # client, get_or_create will throw IntegrityError (because our
        # database is enforcing the no-duplicate-objects constraint);
        # in this case one should just re-fetch the object.  This race
        # actually happens with populate_db.
        #
        # Much of the rest of our code that writes to the database
        # doesn't handle this duplicate object on race issue correctly :(
        transaction.commit()
        return Client.objects.get(name=name)
    return client

def bulk_create_clients(client_list):
    existing_clients = set(client.name for client in Client.objects.select_related().all())

    clients_to_create = []
    for name in client_list:
        if name not in existing_clients:
            clients_to_create.append(Client(name=name))
            existing_clients.add(name)
    batch_bulk_create(Client, clients_to_create)

def linebreak(string):
    return string.replace('\n\n', '<p/>').replace('\n', '<br/>')

class Message(models.Model):
    sender = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    subject = models.CharField(max_length=MAX_SUBJECT_LENGTH, db_index=True)
    content = models.TextField()
    pub_date = models.DateTimeField('date published', db_index=True)
    sending_client = models.ForeignKey(Client)

    def __repr__(self):
        display_recipient = get_display_recipient(self.recipient)
        return "<Message: %s / %s / %r>" % (display_recipient, self.subject, self.sender)
    def __str__(self):
        return self.__repr__()

    @cache_with_key(lambda self, apply_markdown: 'message_dict:%d:%d' % (self.id, apply_markdown))
    def to_dict(self, apply_markdown):
        # Messages arrive in the Tornado process with the dicts already rendered.
        # This avoids running the Markdown parser and some database queries in the single-threaded
        # Tornado server.
        #
        # This field is not persisted to the database and will disappear if the object is re-fetched.
        if hasattr(self, 'precomputed_dicts'):
            return self.precomputed_dicts['text/html' if apply_markdown else 'text/x-markdown']

        display_recipient = get_display_recipient(self.recipient)
        if self.recipient.type == Recipient.STREAM:
            display_type = "stream"
        elif self.recipient.type in (Recipient.HUDDLE, Recipient.PERSONAL):
            display_type = "private"
            if len(display_recipient) == 1:
                # add the sender in if this isn't a message between
                # someone and his self, preserving ordering
                recip = {'email': self.sender.user.email,
                         'full_name': self.sender.full_name,
                         'short_name': self.sender.short_name};
                if recip['email'] < display_recipient[0]['email']:
                    display_recipient = [recip, display_recipient[0]]
                elif recip['email'] > display_recipient[0]['email']:
                    display_recipient = [display_recipient[0], recip]
        else:
            display_type = self.recipient.type_name()

        obj = dict(
            id                = self.id,
            sender_email      = self.sender.user.email,
            sender_full_name  = self.sender.full_name,
            sender_short_name = self.sender.short_name,
            type              = display_type,
            display_recipient = display_recipient,
            recipient_id      = self.recipient.id,
            subject           = self.subject,
            timestamp         = datetime_to_timestamp(self.pub_date),
            gravatar_hash     = gravatar_hash(self.sender.user.email))

        if apply_markdown:
            if (self.sender.realm.domain != "customer1.invalid" or
                self.sending_client.name in ('API', 'github_bot')):
                obj['content'] = bugdown.convert(self.content)
            else:
                obj['content'] = linebreak(escape(self.content))
            obj['content_type'] = 'text/html'
        else:
            obj['content'] = self.content
            obj['content_type'] = 'text/x-markdown'

        return obj

    def to_log_dict(self):
        return dict(
            id                = self.id,
            sender_email      = self.sender.user.email,
            sender_full_name  = self.sender.full_name,
            sender_short_name = self.sender.short_name,
            sending_client    = self.sending_client.name,
            type              = self.recipient.type_name(),
            recipient         = get_display_recipient(self.recipient),
            subject           = self.subject,
            content           = self.content,
            timestamp         = datetime_to_timestamp(self.pub_date))

    @classmethod
    def remove_unreachable(cls):
        """Remove all Messages that are not referred to by any UserMessage."""
        cls.objects.exclude(id__in = UserMessage.objects.values('message_id')).delete()

class UserMessage(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    message = models.ForeignKey(Message)
    # We're not using the archived field for now, but create it anyway
    # since this table will be an unpleasant one to do schema changes
    # on later
    archived = models.BooleanField()

    class Meta:
        unique_together = ("user_profile", "message")

    def __repr__(self):
        display_recipient = get_display_recipient(self.message.recipient)
        return "<UserMessage: %s / %s>" % (display_recipient, self.user_profile.user.email)

user_hash = {}
def get_user_profile_by_id(uid):
    if uid in user_hash:
        return user_hash[uid]
    return UserProfile.objects.select_related().get(id=uid)

# Store an event in the log for re-importing messages
def log_event(event):
    if "timestamp" not in event:
        event["timestamp"] = time.time()
    with lockfile(settings.MESSAGE_LOG + '.lock'):
        with open(settings.MESSAGE_LOG, 'a') as log:
            log.write(simplejson.dumps(event) + '\n')

def log_message(message):
    if not message.sending_client.name.startswith("test:"):
        log_event(message.to_log_dict())

def do_send_message(message, no_log=False):
    # Log the message to our message log for populate_db to refill
    if not no_log:
        log_message(message)

    if message.recipient.type == Recipient.PERSONAL:
        recipients = list(set([get_user_profile_by_id(message.recipient.type_id),
                               get_user_profile_by_id(message.sender_id)]))
        # For personals, you send out either 1 or 2 copies of the message, for
        # personals to yourself or to someone else, respectively.
        assert((len(recipients) == 1) or (len(recipients) == 2))
    elif (message.recipient.type == Recipient.STREAM or
          message.recipient.type == Recipient.HUDDLE):
        recipients = [s.user_profile for
                      s in Subscription.objects.select_related().filter(recipient=message.recipient, active=True)]
    else:
        raise ValueError('Bad recipient type')

    # Save the message receipts in the database
    # TODO: Use bulk_create here
    with transaction.commit_on_success():
        message.save()
        for user_profile in recipients:
            # Only deliver messages to "active" user accounts
            if user_profile.user.is_active:
                UserMessage(user_profile=user_profile, message=message).save()

    # We can only publish messages to longpolling clients if the Tornado server is running.
    if settings.TORNADO_SERVER:
        # Render Markdown etc. here, so that the single-threaded Tornado server doesn't have to.
        # TODO: Reduce duplication in what we send.
        rendered = { 'text/html':       message.to_dict(apply_markdown=True),
                     'text/x-markdown': message.to_dict(apply_markdown=False) }
        requests.post(settings.TORNADO_SERVER + '/notify_new_message', data=dict(
            secret   = settings.SHARED_SECRET,
            message  = message.id,
            rendered = simplejson.dumps(rendered),
            users    = simplejson.dumps([str(user.id) for user in recipients])))

def internal_send_message(sender_email, recipient_type, recipient_name,
                          subject, content):
    if len(content) > MAX_MESSAGE_LENGTH:
        content = content[0:3900] + "\n\n[message was too long and has been truncated]"
    message = Message()
    message.sender = UserProfile.objects.get(user__email=sender_email)
    message.recipient = Recipient.objects.get(type_id=create_stream_if_needed(
        message.sender.realm, recipient_name).id, type=recipient_type)
    message.subject = subject
    message.content = content
    message.pub_date = timezone.now()
    message.sending_client = get_client("Internal")

    do_send_message(message)

class Subscription(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user_profile", "recipient")

    def __repr__(self):
        return "<Subscription: %r -> %r>" % (self.user_profile, self.recipient)
    def __str__(self):
        return self.__repr__()

def do_add_subscription(user_profile, stream, no_log=False):
    recipient = Recipient.objects.get(type_id=stream.id,
                                      type=Recipient.STREAM)
    (subscription, created) = Subscription.objects.get_or_create(
        user_profile=user_profile, recipient=recipient,
        defaults={'active': True})
    did_subscribe = created
    if not subscription.active:
        did_subscribe = True
        subscription.active = True
        subscription.save()
    if did_subscribe and not no_log:
        log_event({'type': 'subscription_added',
                   'user': user_profile.user.email,
                   'name': stream.name,
                   'domain': stream.realm.domain})
    return did_subscribe

def do_remove_subscription(user_profile, stream, no_log=False):
    recipient = Recipient.objects.get(type_id=stream.id,
                                      type=Recipient.STREAM)
    maybe_sub = Subscription.objects.filter(user_profile=user_profile,
                                    recipient=recipient)
    if len(maybe_sub) == 0:
        return False
    subscription = maybe_sub[0]
    did_remove = subscription.active
    subscription.active = False
    subscription.save()
    if did_remove and not no_log:
        log_event({'type': 'subscription_removed',
                   'user': user_profile.user.email,
                   'name': stream.name,
                   'domain': stream.realm.domain})
    return did_remove

def log_subscription_property_change(user_email, property, property_dict):
    event = {'type': 'subscription_property',
             'property': property,
             'user': user_email}
    event.update(property_dict)
    log_event(event)

def do_activate_user(user, log=True, join_date=timezone.now()):
    user.is_active = True
    user.set_password(initial_password(user.email))
    user.date_joined = join_date
    user.save()
    if log:
        log_event({'type': 'user_activated',
                   'user': user.email})

def do_change_password(user, password, log=True, commit=True):
    user.set_password(password)
    if commit:
        user.save()
    if log:
        log_event({'type': 'user_change_password',
                   'user': user.email,
                   'pwhash': user.password})

def do_change_full_name(user_profile, full_name, log=True):
    user_profile.full_name = full_name
    user_profile.save()
    if log:
        log_event({'type': 'user_change_full_name',
                   'user': user_profile.user.email,
                   'full_name': full_name})

def do_create_realm(domain, replay=False):
    realm, created = Realm.objects.get_or_create(domain=domain)
    if created and not replay:
        # Log the event
        log_event({"type": "realm_created",
                   "domain": domain})

        # Sent a notification message
        message = Message()
        message.sender = UserProfile.objects.get(user__email="humbug+signups@humbughq.com")
        message.recipient = Recipient.objects.get(type_id=create_stream_if_needed(
                message.sender.realm, "signups").id, type=Recipient.STREAM)
        message.subject = domain
        message.content = "Signups enabled."
        message.pub_date = timezone.now()
        message.sending_client = get_client("Internal")

        do_send_message(message)
    return (realm, created)

def do_change_enable_desktop_notifications(user_profile, enable_desktop_notifications, log=True):
    user_profile.enable_desktop_notifications = enable_desktop_notifications
    user_profile.save()
    if log:
        log_event({'type': 'enable_desktop_notifications_changed',
                   'user': user_profile.user.email,
                   'enable_desktop_notifications': enable_desktop_notifications})

class Huddle(models.Model):
    # TODO: We should consider whether using
    # CommaSeparatedIntegerField would be better.
    huddle_hash = models.CharField(max_length=40, db_index=True, unique=True)

def get_huddle_hash(id_list):
    id_list = sorted(set(id_list))
    hash_key = ",".join(str(x) for x in id_list)
    return hashlib.sha1(hash_key).hexdigest()

def get_huddle(id_list):
    huddle_hash = get_huddle_hash(id_list)
    (huddle, created) = Huddle.objects.get_or_create(huddle_hash=huddle_hash)
    if created:
        recipient = Recipient.objects.create(type_id=huddle.id,
                                             type=Recipient.HUDDLE)
        # Add subscriptions
        for uid in id_list:
            Subscription.objects.create(recipient = recipient,
                                        user_profile = UserProfile.objects.get(id=uid))
    return huddle

def bulk_create_huddles(users, huddle_user_list):
    huddles = {}
    huddles_by_id = {}
    huddle_set = set()
    existing_huddles = set()
    for huddle in Huddle.objects.all():
        existing_huddles.add(huddle.huddle_hash)
    for huddle_users in huddle_user_list:
        user_ids = [users[email].id for email in huddle_users]
        huddle_hash = get_huddle_hash(user_ids)
        if huddle_hash in existing_huddles:
            continue
        huddle_set.add((huddle_hash, tuple(sorted(user_ids))))

    huddles_to_create = []
    for (huddle_hash, _) in huddle_set:
        huddles_to_create.append(Huddle(huddle_hash=huddle_hash))
    batch_bulk_create(Huddle, huddles_to_create)

    for huddle in Huddle.objects.all():
        huddles[huddle.huddle_hash] = huddle
        huddles_by_id[huddle.id] = huddle

    recipients_to_create = []
    for (huddle_hash, _) in huddle_set:
        recipients_to_create.append(Recipient(type_id=huddles[huddle_hash].id, type=Recipient.HUDDLE))
    batch_bulk_create(Recipient, recipients_to_create)

    huddle_recipients = {}
    for recipient in Recipient.objects.filter(type=Recipient.HUDDLE):
        huddle_recipients[huddles_by_id[recipient.type_id].huddle_hash] = recipient

    subscriptions_to_create = []
    for (huddle_hash, huddle_user_ids) in huddle_set:
        for user_id in huddle_user_ids:
            subscriptions_to_create.append(Subscription(active=True, user_profile_id=user_id,
                                                        recipient=huddle_recipients[huddle_hash]))
    batch_bulk_create(Subscription, subscriptions_to_create)

# This function is used only by tests.
# We have faster implementations within the app itself.
def filter_by_subscriptions(messages, user):
    user_profile = UserProfile.objects.get(user=user)
    user_messages = []
    subscriptions = [sub.recipient for sub in
                     Subscription.objects.filter(user_profile=user_profile, active=True)]
    for message in messages:
        # If you are subscribed to the personal or stream, or if you
        # sent the personal, you can see the message.
        if (message.recipient in subscriptions) or \
                (message.recipient.type == Recipient.PERSONAL and
                 message.sender == user_profile):
            user_messages.append(message)

    return user_messages

def clear_database():
    for model in [Message, Stream, UserProfile, User, Recipient,
                  Realm, Subscription, Huddle, UserMessage, Client,
                  DefaultStream]:
        model.objects.all().delete()
    Session.objects.all().delete()

class UserActivity(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    client = models.ForeignKey(Client)
    query = models.CharField(max_length=50, db_index=True)

    count = models.IntegerField()
    last_visit = models.DateTimeField('last visit')

    class Meta:
        unique_together = ("user_profile", "client", "query")

class DefaultStream(models.Model):
    realm = models.ForeignKey(Realm)
    stream = models.ForeignKey(Stream)

    class Meta:
        unique_together = ("realm", "stream")

# FIXME: The foreign key relationship here is backwards.
#
# We can't easily get a list of streams and their associated colors (if any) in
# a single query.  See zephyr.views.gather_subscriptions for an example.
#
# We should change things around so that is possible.  Probably this should
# just be a column on Subscription.
class StreamColor(models.Model):
    subscription = models.ForeignKey(Subscription)
    color = models.CharField(max_length=10)

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from zephyr.models import UserProfile, UserActivity, get_client
from zephyr.lib.response import json_success, json_error
from django.utils.timezone import now
from django.db import transaction, IntegrityError
from django.conf import settings
import simplejson

from functools import wraps

class _RespondAsynchronously(object):
    pass

# Return RespondAsynchronously from an @asynchronous view if the
# response will be provided later by calling handler.finish(), or has
# already been provided this way. We use this for longpolling mode.
RespondAsynchronously = _RespondAsynchronously()

def asynchronous(method):
    @wraps(method)
    def wrapper(request, *args, **kwargs):
        return method(request, handler=request._tornado_handler, *args, **kwargs)
    if getattr(method, 'csrf_exempt', False):
        wrapper.csrf_exempt = True
    return wrapper

# I like the all-lowercase name better
require_post = require_POST

@transaction.commit_on_success
def update_user_activity(request, user_profile, client):
    current_time = now()
    try:
        (activity, created) = UserActivity.objects.get_or_create(
            user_profile = user_profile,
            client = client,
            query = request.META["PATH_INFO"],
            defaults={'last_visit': current_time, 'count': 0})
    except IntegrityError:
        transaction.commit()
        activity = UserActivity.objects.get(user_profile = user_profile,
                                            client = client,
                                            query = request.META["PATH_INFO"])
    activity.count += 1
    activity.last_visit = current_time
    activity.save()

# authenticated_api_view will add the authenticated user's user_profile to
# the view function's arguments list, since we have to look it up
# anyway.
def authenticated_api_view(view_func):
    @csrf_exempt
    @require_post
    @has_request_variables
    @wraps(view_func)
    def _wrapped_view_func(request, email=POST, api_key=POST('api-key'),
                           client=POST(default=get_client("API"), converter=get_client),
                           *args, **kwargs):
        try:
            user_profile = UserProfile.objects.get(user__email=email)
        except UserProfile.DoesNotExist:
            return json_error("Invalid user: %s" % (email,))
        if api_key != user_profile.api_key:
            return json_error("Invalid API key for user '%s'" % (email,))
        request._client = client
        update_user_activity(request, user_profile, client)
        return view_func(request, user_profile, *args, **kwargs)
    return _wrapped_view_func

def authenticate_log_and_execute_json(request, client, view_func, *args, **kwargs):
    if not request.user.is_authenticated():
        return json_error("Not logged in", status=401)
    request._client = client
    user_profile = request.user.userprofile
    update_user_activity(request, user_profile, client)
    return view_func(request, user_profile, *args, **kwargs)

# Checks if the request is a POST request and that the user is logged
# in.  If not, return an error (the @login_required behavior of
# redirecting to a login page doesn't make sense for json views)
def authenticated_json_post_view(view_func):
    @require_post
    @has_request_variables
    @wraps(view_func)
    def _wrapped_view_func(request,
                           client=POST(default=get_client("website"), converter=get_client),
                           *args, **kwargs):
        return authenticate_log_and_execute_json(request, client, view_func, *args, **kwargs)
    return _wrapped_view_func

def authenticated_json_view(view_func):
    @wraps(view_func)
    def _wrapped_view_func(request,
                           client=get_client("website"),
                           *args, **kwargs):
        return authenticate_log_and_execute_json(request, client, view_func, *args, **kwargs)
    return _wrapped_view_func

# These views are used by the main Django server to notify the Tornado server
# of events.  We protect them from the outside world by checking a shared
# secret, and also the originating IP (for now).
def authenticate_notify(request):
    return (request.META['REMOTE_ADDR'] in ('127.0.0.1', '::1')
            and request.POST.get('secret') == settings.SHARED_SECRET)

def internal_notify_view(view_func):
    @csrf_exempt
    @require_post
    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        if not authenticate_notify(request):
            return json_error('Access denied', status=403)
        if not hasattr(request, '_tornado_handler'):
            # We got called through the non-Tornado server somehow.
            # This is not a security check; it's an internal assertion
            # to help us find bugs.
            raise RuntimeError, 'notify view called with no Tornado handler'
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

class RequestVariableMissingError(Exception):
    def __init__(self, var_name):
        self.var_name = var_name

    def to_json_error_msg(self):
        return "Missing '%s' argument" % (self.var_name,)

    def __str__(self):
        return self.to_json_error_msg()

class RequestVariableConversionError(Exception):
    def __init__(self, var_name, bad_value):
        self.var_name = var_name
        self.bad_value = bad_value

    def to_json_error_msg(self):
        return "Bad value for '%s': %s" % (self.var_name, self.bad_value)

    def __str__(self):
        return self.to_json_error_msg()

# Used in conjunction with @has_request_variables, below
class POST(object):
    # NotSpecified is a sentinel value for determining whether a
    # default value was specified for a request variable.  We can't
    # use None because that could be a valid, user-specified default
    class _NotSpecified(object):
        pass
    NotSpecified = _NotSpecified()

    def __init__(self, whence=None, converter=None, default=NotSpecified):
        """
        whence: the name of the request variable that should be used
        for this parameter.  Defaults to a request variable of the
        same name as the parameter.

        converter: a function that takes a string and returns a new
        value.  If specified, this will be called on the request
        variable value before passing to the function

        default: a value to be used for the argument if the parameter
        is missing in the request
        """

        self.post_var_name = whence
        self.func_var_name = None
        self.converter = converter
        self.default = default

# Extracts variables from the request object and passes them as
# named function arguments.  The request object must be the first
# argument to the function.
#
# To use, assign a function parameter a default value that is an
# instance of the POST class.  That paramter will then be
# automatically populated from the HTTP request.  The request object
# must be the first argument to the decorated function.
#
# This should generally be the innermost (syntactically bottommost)
# decorator applied to a view, since other decorators won't preserve
# the default parameter values used by has_request_variables.
#
# Note that this can't be used in helper functions which are not
# expected to call json_error or json_success, as it uses json_error
# internally when it encounters an error
def has_request_variables(view_func):
    num_params = view_func.func_code.co_argcount
    if view_func.func_defaults is None:
        num_default_params = 0
    else:
        num_default_params = len(view_func.func_defaults)
    default_param_names = view_func.func_code.co_varnames[num_params - num_default_params:]
    default_param_values = view_func.func_defaults

    post_params = []

    for (name, value) in zip(default_param_names, default_param_values):
        if isinstance(value, POST):
            value.func_var_name = name
            if value.post_var_name is None:
                value.post_var_name = name
            post_params.append(value)
        elif value == POST:
            # If the function definition does not actually
            # instantiate a POST object but instead uses the POST
            # class itself as a value, we instantiate it as a
            # convenience
            post_var = POST(name)
            post_var.func_var_name = name
            post_params.append(post_var)

    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        for param in post_params:
            if param.func_var_name in kwargs:
                continue

            default_assigned = False
            try:
                val = request.POST[param.post_var_name]
            except KeyError:
                if param.default is POST.NotSpecified:
                    raise RequestVariableMissingError(param.post_var_name)
                val = param.default
                default_assigned = True

            if param.converter is not None and not default_assigned:
                try:
                    val = param.converter(val)
                except:
                    raise RequestVariableConversionError(param.post_var_name, val)
            kwargs[param.func_var_name] = val

        return view_func(request, *args, **kwargs)

    return _wrapped_view_func

# Converter functions for use with has_request_variables
def to_non_negative_int(x):
    x = int(x)
    if x < 0:
        raise ValueError("argument is negative")
    return x

def json_to_dict(json):
    data = simplejson.loads(json)
    if not isinstance(data, dict):
        raise ValueError("argument is not a dictionary")
    return data

def json_to_list(json):
    data = simplejson.loads(json)
    if not isinstance(data, list):
        raise ValueError("argument is not a list")
    return data

from zephyr.models import Message, UserProfile, UserMessage, UserActivity

from zephyr.decorator import asynchronous, authenticated_api_view, \
    authenticated_json_post_view, internal_notify_view, RespondAsynchronously, \
    has_request_variables, POST, json_to_list, to_non_negative_int
from zephyr.lib.response import json_success, json_error

import datetime
import simplejson
import socket
import time

SERVER_GENERATION = int(time.time())

@internal_notify_view
def notify_new_message(request):
    # If a message for some reason has no recipients (e.g. it is sent
    # by a bot to a stream that nobody is subscribed to), just skip
    # the message gracefully
    if request.POST["users"] == "":
        return json_success()

    # FIXME: better query
    users   = [UserProfile.objects.get(id=user)
               for user in json_to_list(request.POST['users'])]
    message = Message.objects.get(id=request.POST['message'])

    # Cause message.to_dict() to return the dicts already rendered in the other process.
    #
    # We decode this JSON only to eventually re-encode it as JSON.
    # This isn't trivial to fix, because we do access some fields in the meantime
    # (see send_with_safety_check).  It's probably not a big deal.
    message.precomputed_dicts = simplejson.loads(request.POST['rendered'])

    for user in users:
        user.receive(message)

    return json_success()

@internal_notify_view
def notify_pointer_update(request):
    # FIXME: better query
    user_profile = UserProfile.objects.get(id=request.POST['user'])
    new_pointer = int(request.POST['new_pointer'])
    pointer_updater = request.POST['pointer_updater']

    user_profile.update_pointer(new_pointer, pointer_updater)

    return json_success()

@asynchronous
@authenticated_json_post_view
def json_get_updates(request, user_profile, handler):
    client_id = request.session.session_key
    return get_updates_backend(request, user_profile, handler, client_id,
                               client=request._client, apply_markdown=True)

@asynchronous
@authenticated_api_view
@has_request_variables
def api_get_messages(request, user_profile, handler, client_id=POST(default=None),
                     apply_markdown=POST(default=False, converter=simplejson.loads)):
    return get_updates_backend(request, user_profile, handler, client_id,
                               apply_markdown=apply_markdown,
                               client=request._client)

def format_updates_response(messages=[], apply_markdown=True,
                            user_profile=None, new_pointer=None,
                            client=None, update_types=[],
                            client_server_generation=None):
    if client is not None and client.name.endswith("_mirror"):
        messages = [m for m in messages if m.sending_client.name != client.name]
    ret = {'messages': [message.to_dict(apply_markdown) for message in messages],
           "result": "success",
           "msg": "",
           'update_types': update_types}
    if client_server_generation is not None:
        ret['server_generation'] = SERVER_GENERATION
    if new_pointer is not None:
        ret['new_pointer'] = new_pointer
    if user_profile.realm.domain == "mit.edu":
        try:
            activity = UserActivity.objects.get(user_profile = user_profile,
                                                query="/api/v1/get_messages",
                                                client__name="zephyr_mirror")
            ret['zephyr_mirror_active'] = \
                (activity.last_visit.replace(tzinfo=None) >
                 datetime.datetime.utcnow() - datetime.timedelta(minutes=5))
        except UserActivity.DoesNotExist:
            ret['zephyr_mirror_active'] = False

    return ret

def return_messages_immediately(user_profile, client_id, last,
                                client_server_generation,
                                client_pointer, dont_block, **kwargs):
    update_types = []
    new_pointer = None
    if dont_block:
        update_types.append("nonblocking_request")

    if (client_server_generation is not None and
        client_server_generation != SERVER_GENERATION):
        update_types.append("client_reload")

    ptr = user_profile.pointer
    if (client_pointer is not None and ptr > client_pointer):
        new_pointer = ptr
        update_types.append("pointer_update")

    if last is not None:
        query = Message.objects.select_related().filter(
                usermessage__user_profile = user_profile).order_by('id')
        messages = query.filter(id__gt=last)[:400]

        # Filter for mirroring before checking whether there are any
        # messages to pass on.  If we don't do this, when the only message
        # to forward is one that was sent via the mirroring, the API
        # client will end up in an endless loop requesting more data from
        # us.
        if "client" in kwargs and kwargs["client"].name.endswith("_mirror"):
            messages = [m for m in messages if
                        m.sending_client.name != kwargs["client"].name]
    else: # last is None, so we're not interested in any old messages
        messages = []

    if messages:
        update_types.append("new_messages")

    if update_types:
        return format_updates_response(messages=messages,
                                       user_profile=user_profile,
                                       new_pointer=new_pointer,
                                       client_server_generation=client_server_generation,
                                       update_types=update_types,
                                       **kwargs)

    return None

def send_with_safety_check(response, handler, apply_markdown=True, **kwargs):
    # Make sure that Markdown rendering really happened, if requested.
    # This is a security issue because it's where we escape HTML.
    # c.f. ticket #64
    #
    # apply_markdown=True is the fail-safe default.
    if response['result'] == 'success' and apply_markdown:
        for msg in response['messages']:
            if msg['content_type'] != 'text/html':
                handler.set_status(500)
                handler.finish('Internal error: bad message format')
                return
    if response['result'] == 'error':
        handler.set_status(400)
    handler.finish(response)

@has_request_variables
def get_updates_backend(request, user_profile, handler, client_id,
                        last = POST(converter=to_non_negative_int, default=None),
                        client_server_generation = POST(whence='server_generation', default=None,
                                                        converter=int),
                        client_pointer = POST(whence='pointer', converter=int, default=None),
                        dont_block = POST(converter=simplejson.loads, default=False),
                        **kwargs):
    resp = return_messages_immediately(user_profile, client_id, last,
                                       client_server_generation,
                                       client_pointer,
                                       dont_block, **kwargs)
    if resp is not None:
        send_with_safety_check(resp, handler, **kwargs)

        # We have already invoked handler.finish(), so we bypass the usual view
        # response path.  We are "responding asynchronously" except that it
        # already happened.  This is slightly weird, but lets us share
        # send_with_safety_check with the code below.
        return RespondAsynchronously

    # Enter long-polling mode.
    #
    # Instead of responding to the client right away, leave our connection open
    # and return to the Tornado main loop.  One of the notify_* views will
    # eventually invoke one of these callbacks, which will send the delayed
    # response.

    def cb(**cb_kwargs):
        if handler.request.connection.stream.closed():
            return
        try:
            # It would be nice to be able to do these checks in
            # UserProfile.receive, but it doesn't know what the value
            # of "last" was for each callback.
            if last is not None and "messages" in cb_kwargs:
                messages = cb_kwargs["messages"]

                # Make sure the client doesn't get a message twice
                # when messages are processed out of order.
                if messages[0].id <= last:
                    # We must return a response because we don't have
                    # a way to re-queue a callback and so the client
                    # must do it by making a new request
                    handler.finish({"result": "success",
                                    "msg": "",
                                    'update_types': []})
                    return

            kwargs.update(cb_kwargs)
            res = format_updates_response(user_profile=user_profile,
                                          client_server_generation=client_server_generation,
                                          **kwargs)
            send_with_safety_check(res, handler, **kwargs)
        except socket.error:
            pass

    user_profile.add_receive_callback(handler.async_callback(cb))
    if client_pointer is not None:
        user_profile.add_pointer_update_callback(handler.async_callback(cb))

    # runtornado recognizes this special return value.
    return RespondAsynchronously

"""
Implements the per-domain data retention policy.

The goal is to have a single place where the policy is defined.  This is
complicated by needing to apply this policy both to the database and to log
files.  Additionally, we want to use an efficient query for the database,
rather than iterating through messages one by one.

The code in this module does not actually remove anything; it just identifies
which items should be kept or removed.
"""

import sys
import operator

from django.utils     import timezone
from django.db.models import Q
from datetime         import datetime, timedelta
from zephyr.models    import Realm, UserMessage

# Each domain has a maximum age for retained messages.
#
# FIXME: Move this into the database.
max_age = {
    'customer1.invalid': timedelta(days=31),
}

def should_expunge_from_log(msg, now):
    """Should a particular log entry be expunged?

       msg: a log entry dict
       now: current time for purposes of determining log entry age"""

    # This function will be called many times, but we want to compare all
    # entries against a consistent "current time".  So the caller passes
    # that time as a parameter.

    if msg.get('type') == 'default_streams':
        # These don't have an associated user.
        # We could use the 'domain' field, but it probably makes sense to
        # keep these forever.
        return False

    # FIXME: Yet another place where we compute the domain manually.
    # See #260.
    user = msg.get('sender_email')
    if user is None:
        user = msg.get('user')
    if user is None:
        # Avoid printing the entire message, but give enough information to find it later.
        print >>sys.stderr, "WARNING: Can't get user for entry at", msg['timestamp']
        return False
    domain = user.split('@', 1)[1]

    if domain not in max_age:
        # Keep forever.
        return False

    age = now - datetime.fromtimestamp(msg['timestamp'])
    return age > max_age[domain]

def get_UserMessages_to_expunge():
    """Fetch all UserMessages which should be expunged from the database.

       After deleting these, you may also want to call
       Message.remove_unreachable()."""
    # Unlike retain_in_log, this handles all messages at once, so we
    # use the actual current time.
    now = timezone.now()
    queries = [Q(user_profile__realm   = realm,
                 message__pub_date__lt = now - max_age[realm.domain])
               for realm in Realm.objects.all()
               if  realm.domain in max_age]

    if not queries:
        return UserMessage.objects.none()

    # Return all objects matching any of the queries in 'queries'.
    return UserMessage.objects.filter(reduce(operator.or_, queries))

import sys
import logging
import traceback
import platform

from django.utils.timezone import now
from django.views.debug import get_exception_reporter_filter


class AdminHumbugHandler(logging.Handler):
    """An exception log handler that Humbugs log entries to the Humbug realm.

    If the request is passed as the first argument to the log record,
    request data will be provided in the email report.
    """

    # adapted in part from django/utils/log.py

    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        # We have to defer imports to avoid circular imports in settings.py.
        from zephyr.models import Message, UserProfile, Recipient, \
                create_stream_if_needed, get_client, internal_send_message
        from django.conf import settings

        subject = '%s: %s' % (platform.node(), record.getMessage())
        try:
            request = record.request

            filter = get_exception_reporter_filter(request)
            request_repr = "Request info:\n~~~~\n"
            request_repr += "- path: %s\n" % (request.path,)
            if request.method == "GET":
                request_repr += "- GET: %s\n" % (request.GET,)
            elif request.method == "POST":
                request_repr += "- POST: %s\n" % (filter.get_post_parameters(request),)
            for field in ["REMOTE_ADDR", "QUERY_STRING", "SERVER_NAME"]:
                request_repr += "- %s: \"%s\"\n" % (field, request.META.get(field, "(None)"))
            request_repr += "~~~~"
        except Exception:
            request_repr = "Request repr() unavailable."
        subject = self.format_subject(subject)

        if record.exc_info:
            stack_trace = ''.join(traceback.format_exception(*record.exc_info))
        else:
            stack_trace = 'No stack trace available'

        internal_send_message("humbug+errors@humbughq.com",
                Recipient.STREAM, "devel", subject,
                "~~~~ pytb\n%s\n\n~~~~\n%s" % (stack_trace, request_repr))

    def format_subject(self, subject):
        """
        Escape CR and LF characters, and limit length to MAX_SUBJECT_LENGTH.
        """
        from zephyr.models import MAX_SUBJECT_LENGTH
        formatted_subject = subject.replace('\n', '\\n').replace('\r', '\\r')
        return formatted_subject[:MAX_SUBJECT_LENGTH]



from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import SetPasswordForm

from humbug import settings
from zephyr.models import Realm, do_change_password

def is_unique(value):
    try:
        User.objects.get(email__iexact=value)
        raise ValidationError(u'%s is already registered' % value)
    except User.DoesNotExist:
        pass

def is_active(value):
    try:
        if User.objects.get(email=value).is_active:
            raise ValidationError(u'%s is already active' % value)
    except User.DoesNotExist:
        pass

SIGNUP_STRING = '<a href="http://get.humbughq.com/">Sign up</a> to find out when Humbug is ready for you.'

def has_valid_realm(value):
    try:
        Realm.objects.get(domain=value.split("@")[-1])
    except Realm.DoesNotExist:
        raise ValidationError(mark_safe(u'Registration is not currently available for your domain. ' + SIGNUP_STRING))

def isnt_mit(value):
    if "@mit.edu" in value:
        raise ValidationError(mark_safe(u'Humbug for MIT is by invitation only. ' + SIGNUP_STRING))


class UniqueEmailField(forms.EmailField):
    default_validators = [validators.validate_email, is_unique]

class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, max_length=100)
    terms = forms.BooleanField(required=True)

class ToSForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    terms = forms.BooleanField(required=True)

class HomepageForm(forms.Form):
    if settings.ALLOW_REGISTER:
        email = UniqueEmailField()
    else:
        validators = UniqueEmailField.default_validators + [has_valid_realm, isnt_mit]
        email = UniqueEmailField(validators=validators)

class LoggingSetPasswordForm(SetPasswordForm):
    def save(self, commit=True):
        do_change_password(self.user, self.cleaned_data['new_password1'],
                           log=True, commit=commit)
        return self.user

from django.conf import settings

def add_settings(request):
    return {
        'full_navbar':   settings.FULL_NAVBAR,

        # c.f. Django's STATIC_URL variable
        'static_hidden': '/static/4nrjx8cwce2bka8r/',
    }

from django.views.debug import SafeExceptionReporterFilter

class HumbugExceptionReporterFilter(SafeExceptionReporterFilter):
    def get_post_parameters(self, request):
        filtered_post = SafeExceptionReporterFilter.get_post_parameters(self, request).copy()
        filtered_vars = ['content', 'secret', 'password', 'key', 'api_key', 'subject', 'stream']

        for var in filtered_vars:
            if var in filtered_post:
                filtered_post[var] = '**********'
        return filtered_post

from decorator import RequestVariableMissingError, RequestVariableConversionError
from zephyr.lib.response import json_error

import logging
import time

logger = logging.getLogger('humbug.requests')

class LogRequests(object):
    def process_request(self, request):
        request._time_started = time.time()

    def process_response(self, request, response):

        # The reverse proxy might have sent us the real external IP
        remote_ip = request.META.get('HTTP_X_REAL_IP')
        if remote_ip is None:
            remote_ip = request.META['REMOTE_ADDR']

        time_delta = -1
        # A time duration of -1 means the StartLogRequests middleware
        # didn't run for some reason
        if hasattr(request, '_time_started'):
            time_delta = time.time() - request._time_started
        logger.info('%-15s %-7s %3d %.3fs %s'
            % (remote_ip, request.method, response.status_code,
               time_delta, request.get_full_path()))
        return response

class JsonErrorHandler(object):
    def process_exception(self, request, exception):
        if hasattr(exception, 'to_json_error_msg') and callable(exception.to_json_error_msg):
            return json_error(exception.to_json_error_msg())
        return None

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext, loader
from django.utils.timezone import utc, now
from django.core.exceptions import ValidationError
from django.contrib.auth.views import login as django_login_page
from django.db.models import Q
from django.core.mail import send_mail
from zephyr.models import Message, UserProfile, Stream, Subscription, \
    Recipient, get_display_recipient, get_huddle, Realm, UserMessage, \
    do_add_subscription, do_remove_subscription, do_change_password, \
    do_change_full_name, do_change_enable_desktop_notifications, \
    do_activate_user, add_default_subs, do_create_user, do_send_message, \
    create_mit_user_if_needed, create_stream_if_needed, StreamColor, \
    PreregistrationUser, get_client, MitUser, User, UserActivity, \
    log_subscription_property_change, internal_send_message, \
    MAX_SUBJECT_LENGTH, MAX_MESSAGE_LENGTH
from zephyr.forms import RegistrationForm, HomepageForm, ToSForm, is_unique, \
    is_active
from django.views.decorators.csrf import csrf_exempt

from zephyr.decorator import require_post, \
    authenticated_api_view, authenticated_json_post_view, \
    has_request_variables, POST, authenticated_json_view, \
    to_non_negative_int, json_to_dict, json_to_list
from zephyr.lib.query import last_n
from zephyr.lib.avatar import gravatar_hash
from zephyr.lib.response import json_success, json_error
from zephyr.lib.time import timestamp_to_datetime

from confirmation.models import Confirmation

import datetime
import simplejson
import re
import urllib
import time
import requests
import os
import base64

SERVER_GENERATION = int(time.time())

def get_stream(stream_name, realm):
    try:
        return Stream.objects.get(name__iexact=stream_name, realm=realm)
    except Stream.DoesNotExist:
        return None

def notify_new_user(user_profile, internal=False):
    if internal:
        # When this is done using manage.py vs. the web interface
        internal_blurb = " **INTERNAL SIGNUP** "
    else:
        internal_blurb = " "

    internal_send_message("humbug+signups@humbughq.com",
            Recipient.STREAM, "signups", user_profile.realm.domain,
            "%s <`%s`> just signed up for Humbug!%s(total: **%i**)" % (
                user_profile.full_name,
                user_profile.user.email,
                internal_blurb,
                UserProfile.objects.filter(realm=user_profile.realm,
                                           user__is_active=True).count(),
                )
            )

@require_post
def accounts_register(request):
    key = request.POST['key']
    confirmation = Confirmation.objects.get(confirmation_key=key)
    email = confirmation.content_object.email
    mit_beta_user = isinstance(confirmation.content_object, MitUser)

    company_name = email.split('@')[-1]

    try:
        if mit_beta_user:
            # MIT users already exist, but are supposed to be inactive.
            is_active(email)
        else:
            # Other users should not already exist at all.
            is_unique(email)
    except ValidationError:
        return HttpResponseRedirect(reverse('django.contrib.auth.views.login') + '?email=' + urllib.quote_plus(email))

    if request.POST.get('from_confirmation'):
        form = RegistrationForm()
    else:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            password   = form.cleaned_data['password']
            full_name  = form.cleaned_data['full_name']
            short_name = email.split('@')[0]
            domain     = email.split('@')[-1]
            (realm, _) = Realm.objects.get_or_create(domain=domain)

            # FIXME: sanitize email addresses and fullname
            if mit_beta_user:
                user = User.objects.get(email=email)
                do_activate_user(user)
                do_change_password(user, password)
                user_profile = user.userprofile
                do_change_full_name(user_profile, full_name)
            else:
                user_profile = do_create_user(email, password, realm, full_name, short_name)
                add_default_subs(user_profile)

            notify_new_user(user_profile)

            login(request, authenticate(username=email, password=password))
            return HttpResponseRedirect(reverse('zephyr.views.home'))

    return render_to_response('zephyr/register.html',
        { 'form': form, 'company_name': company_name, 'email': email, 'key': key },
        context_instance=RequestContext(request))

@login_required(login_url = settings.HOME_NOT_LOGGED_IN)
def accounts_accept_terms(request):
    email = request.user.email
    company_name = email.split('@')[-1]
    if request.method == "POST":
        form = ToSForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            send_mail('Terms acceptance for ' + full_name,
                    loader.render_to_string('zephyr/tos_accept_body.txt',
                        {'name': full_name,
                         'email': email,
                         'ip': request.META['REMOTE_ADDR'],
                         'browser': request.META['HTTP_USER_AGENT']}),
                        "humbug@humbughq.com",
                        ["all@humbughq.com"])
            do_change_full_name(request.user.userprofile, full_name)
            return redirect(home)

    else:
        form = ToSForm()
    return render_to_response('zephyr/accounts_accept_terms.html',
        { 'form': form, 'company_name': company_name, 'email': email },
        context_instance=RequestContext(request))

def login_page(request, **kwargs):
    template_response = django_login_page(request, **kwargs)
    try:
        template_response.context_data['email'] = request.GET['email']
    except KeyError:
        pass
    return template_response

def accounts_home(request):
    if request.method == 'POST':
        form = HomepageForm(request.POST)
        if form.is_valid():
            try:
                email = form.cleaned_data['email']
                user = PreregistrationUser.objects.get(email=email)
            except PreregistrationUser.DoesNotExist:
                user = PreregistrationUser()
                user.email = email
                user.save()
            Confirmation.objects.send_confirmation(user, user.email)
            return HttpResponseRedirect(reverse('send_confirm', kwargs={'email':user.email}))
        try:
            email = request.POST['email']
            is_unique(email)
        except ValidationError:
            return HttpResponseRedirect(reverse('django.contrib.auth.views.login') + '?email=' + urllib.quote_plus(email))
    else:
        form = HomepageForm()
    return render_to_response('zephyr/accounts_home.html', {'form': form},
                              context_instance=RequestContext(request))

@login_required(login_url = settings.HOME_NOT_LOGGED_IN)
def home(request):
    # We need to modify the session object every two weeks or it will expire.
    # This line makes reloading the page a sufficient action to keep the
    # session alive.
    request.session.modified = True

    user_profile = UserProfile.objects.get(user=request.user)

    num_messages = UserMessage.objects.filter(user_profile=user_profile).count()

    if user_profile.pointer == -1 and num_messages > 0:
        # Put the new user's pointer at the bottom
        #
        # This improves performance, because we limit backfilling of messages
        # before the pointer.  It's also likely that someone joining an
        # organization is interested in recent messages more than the very
        # first messages on the system.

        max_id = (UserMessage.objects.filter(user_profile=user_profile)
                                     .order_by('message')
                                     .reverse()[0]).message_id
        user_profile.pointer = max_id
        user_profile.last_pointer_updater = request.session.session_key

    # Populate personals autocomplete list based on everyone in your
    # realm.  Later we might want a 2-layer autocomplete, where we
    # consider specially some sort of "buddy list" who e.g. you've
    # talked to before, but for small organizations, the right list is
    # everyone in your realm.
    people = [{'email'     : profile.user.email,
               'full_name' : profile.full_name}
              for profile in
              UserProfile.objects.select_related().filter(realm=user_profile.realm) if
              profile != user_profile]

    subscriptions = Subscription.objects.select_related().filter(user_profile_id=user_profile, active=True)
    streams = [get_display_recipient(sub.recipient) for sub in subscriptions
               if sub.recipient.type == Recipient.STREAM]

    return render_to_response('zephyr/index.html',
                              {'user_profile': user_profile,
                               'email_hash'  : gravatar_hash(user_profile.user.email),
                               'people'      : people,
                               'streams'     : streams,
                               'poll_timeout': settings.POLL_TIMEOUT,
                               'have_initial_messages':
                                   'true' if num_messages > 0 else 'false',
                               'show_debug':
                                   settings.DEBUG and ('show_debug' in request.GET),
                               'show_activity': can_view_activity(request) },
                              context_instance=RequestContext(request))

@authenticated_api_view
@has_request_variables
def api_update_pointer(request, user_profile, updater=POST('client_id')):
    return update_pointer_backend(request, user_profile, updater)

@authenticated_json_post_view
def json_update_pointer(request, user_profile):
    return update_pointer_backend(request, user_profile,
                                  request.session.session_key)

@has_request_variables
def update_pointer_backend(request, user_profile, updater,
                           pointer=POST(converter=to_non_negative_int)):
    if pointer <= user_profile.pointer:
        return json_success()

    user_profile.pointer = pointer
    user_profile.last_pointer_updater = updater
    user_profile.save()

    if settings.TORNADO_SERVER:
        requests.post(settings.TORNADO_SERVER + '/notify_pointer_update', data=dict(
            secret          = settings.SHARED_SECRET,
            user            = user_profile.id,
            new_pointer     = pointer,
            pointer_updater = updater))

    return json_success()

@authenticated_json_post_view
def json_get_old_messages(request, user_profile):
    return get_old_messages_backend(request, user_profile=user_profile,
                                    apply_markdown=True)

@authenticated_api_view
@has_request_variables
def api_get_old_messages(request, user_profile,
                         apply_markdown=POST(default=False,
                                             converter=simplejson.loads)):
    return get_old_messages_backend(request, user_profile=user_profile,
                                    apply_markdown=apply_markdown)

class BadNarrowOperator(Exception):
    def __init__(self, desc):
        self.desc = desc

    def to_json_error_msg(self):
        return 'Invalid narrow operator: ' + self.desc

class NarrowBuilder(object):
    def __init__(self, user_profile):
        self.user_profile = user_profile

    def __call__(self, operator, operand):
        # We have to be careful here because we're letting users call a method
        # by name! The prefix 'by_' prevents it from colliding with builtin
        # Python __magic__ stuff.
        method_name = 'by_' + operator.replace('-', '_')
        method = getattr(self, method_name, None)
        if method is None:
            raise BadNarrowOperator('unknown operator ' + operator)
        return method(operand)

    def by_is(self, operand):
        if operand == 'private-message':
            return (Q(recipient__type=Recipient.PERSONAL) |
                    Q(recipient__type=Recipient.HUDDLE))
        raise BadNarrowOperator("unknown 'is' operand " + operand)

    def by_stream(self, operand):
        try:
            stream = Stream.objects.get(realm=self.user_profile.realm,
                                        name__iexact=operand)
        except Stream.DoesNotExist:
            raise BadNarrowOperator('unknown stream ' + operand)
        recipient = Recipient.objects.get(type=Recipient.STREAM, type_id=stream.id)
        return Q(recipient=recipient)

    def by_subject(self, operand):
        return Q(subject=operand)

    def by_pm_with(self, operand):
        if ',' in operand:
            # Huddle
            try:
                emails = [e.strip() for e in operand.split(',')]
                recipient = recipient_for_emails(emails, False,
                    self.user_profile, self.user_profile)
            except ValidationError:
                raise BadNarrowOperator('unknown recipient ' + operand)
            return Q(recipient=recipient)
        else:
            # Personal message
            self_recipient = Recipient.objects.get(type=Recipient.PERSONAL,
                                                   type_id=self.user_profile.id)
            if operand == self.user_profile.user.email:
                # Personals with self
                return Q(recipient__type=Recipient.PERSONAL,
                         sender=self.user_profile, recipient=self_recipient)

            # Personals with other user; include both directions.
            try:
                narrow_profile = UserProfile.objects.get(user__email=operand)
            except UserProfile.DoesNotExist:
                raise BadNarrowOperator('unknown user ' + operand)

            narrow_recipient = Recipient.objects.get(type=Recipient.PERSONAL,
                                                     type_id=narrow_profile.id)
            return ((Q(sender=narrow_profile) & Q(recipient=self_recipient)) |
                    (Q(sender=self.user_profile) & Q(recipient=narrow_recipient)))

    def by_search(self, operand):
        return (Q(content__icontains=operand) |
                Q(subject__icontains=operand))

def narrow_parameter(json):
    # FIXME: A hack to support old mobile clients
    if json == '{}':
        return None

    data = json_to_list(json)
    for elem in data:
        if not isinstance(elem, list):
            raise ValueError("element is not a list")
        if (len(elem) != 2
            or any(not isinstance(x, str) and not isinstance(x, unicode)
                   for x in elem)):
            raise ValueError("element is not a string pair")
    return data

@has_request_variables
def get_old_messages_backend(request, anchor = POST(converter=to_non_negative_int),
                             num_before = POST(converter=to_non_negative_int),
                             num_after = POST(converter=to_non_negative_int),
                             narrow = POST('narrow', converter=narrow_parameter, default=None),
                             user_profile=None, apply_markdown=True):
    query = Message.objects.select_related().filter(usermessage__user_profile = user_profile).order_by('id')

    if narrow is not None:
        build = NarrowBuilder(user_profile)
        for operator, operand in narrow:
            query = query.filter(build(operator, operand))

    # We add 1 to the number of messages requested to ensure that the
    # resulting list always contains the anchor message
    if num_before != 0 and num_after == 0:
        num_before += 1
        messages = last_n(num_before, query.filter(id__lte=anchor))
    elif num_before == 0 and num_after != 0:
        num_after += 1
        messages = query.filter(id__gte=anchor)[:num_after]
    else:
        num_after += 1
        messages = (last_n(num_before, query.filter(id__lt=anchor))
                    + list(query.filter(id__gte=anchor)[:num_after]))

    ret = {'messages': [message.to_dict(apply_markdown) for message in messages],
           "result": "success",
           "msg": ""}
    return json_success(ret)

def generate_client_id():
    return base64.b16encode(os.urandom(16)).lower()

@authenticated_api_view
def api_get_profile(request, user_profile):
    result = dict(pointer        = user_profile.pointer,
                  client_id      = generate_client_id(),
                  max_message_id = -1)

    messages = Message.objects.filter(usermessage__user_profile=user_profile).order_by('-id')[:1]
    if messages:
        result['max_message_id'] = messages[0].id

    return json_success(result)

@authenticated_api_view
def api_send_message(request, user_profile):
    return send_message_backend(request, user_profile, request._client)

@authenticated_json_post_view
def json_send_message(request, user_profile):
    return send_message_backend(request, user_profile, request._client)

# Currently tabbott/extra@mit.edu is our only superuser.  TODO: Make
# this a real superuser security check.
def is_super_user_api(request):
    return request.POST.get("api-key") in ["xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"]

def already_sent_mirrored_message(message):
    if message.recipient.type == Recipient.HUDDLE:
        # For huddle messages, we use a 10-second window because the
        # timestamps aren't guaranteed to actually match between two
        # copies of the same message.
        time_window = datetime.timedelta(seconds=10)
    else:
        time_window = datetime.timedelta(seconds=0)

    # Since our database doesn't store timestamps with
    # better-than-second resolution, we should do our comparisons
    # using objects at second resolution
    pub_date_lowres = message.pub_date.replace(microsecond=0)
    return Message.objects.filter(
        sender=message.sender,
        recipient=message.recipient,
        content=message.content,
        subject=message.subject,
        sending_client=message.sending_client,
        pub_date__gte=pub_date_lowres - time_window,
        pub_date__lte=pub_date_lowres + time_window).exists()

# Validte that the passed in object is an email address from the user's realm
# TODO: Check that it's a real email address here.
def same_realm_email(user_profile, email):
    try:
        domain = email.split("@", 1)[1]
        return user_profile.realm.domain == domain
    except:
        return False

def extract_recipients(raw_recipients):
    try:
        recipients = json_to_list(raw_recipients)
    except simplejson.decoder.JSONDecodeError:
        recipients = [raw_recipients]

    # Strip recipients, and then remove any duplicates and any that
    # are the empty string after being stripped.
    recipients = [recipient.strip() for recipient in recipients]
    return list(set(recipient for recipient in recipients if recipient))

def create_mirrored_message_users(request, user_profile, recipients):
    if "sender" not in request.POST:
        return (False, None)

    sender_email = request.POST["sender"].strip().lower()
    referenced_users = set([sender_email])
    if request.POST['type'] == 'private':
        for email in recipients:
            referenced_users.add(email.lower())

    # Check that all referenced users are in our realm:
    for email in referenced_users:
        if not same_realm_email(user_profile, email):
            return (False, None)

    # Create users for the referenced users, if needed.
    for email in referenced_users:
        create_mit_user_if_needed(user_profile.realm, email)

    sender = UserProfile.objects.get(user__email=sender_email)
    return (True, sender)

def recipient_for_emails(emails, not_forged_zephyr_mirror, user_profile, sender):
    recipient_profile_ids = set()
    for email in emails:
        try:
            recipient_profile_ids.add(UserProfile.objects.get(user__email__iexact=email).id)
        except UserProfile.DoesNotExist:
            raise ValidationError("Invalid email '%s'" % (email,))

    if not_forged_zephyr_mirror and user_profile.id not in recipient_profile_ids:
        raise ValidationError("User not authorized for this query")

    # If the private message is just between the sender and
    # another person, force it to be a personal internally
    if (len(recipient_profile_ids) == 2
        and sender.id in recipient_profile_ids):
        recipient_profile_ids.remove(sender.id)

    if len(recipient_profile_ids) > 1:
        # Make sure the sender is included in huddle messages
        recipient_profile_ids.add(sender.id)
        huddle = get_huddle(list(recipient_profile_ids))
        return Recipient.objects.get(type_id=huddle.id, type=Recipient.HUDDLE)
    else:
        return Recipient.objects.get(type_id=list(recipient_profile_ids)[0],
                                     type=Recipient.PERSONAL)

# We do not @require_login for send_message_backend, since it is used
# both from the API and the web service.  Code calling
# send_message_backend should either check the API key or check that
# the user is logged in.
@has_request_variables
def send_message_backend(request, user_profile, client,
                         message_type_name = POST('type'),
                         message_to = POST('to', converter=extract_recipients),
                         forged = POST(default=False),
                         subject_name = POST('subject', lambda x: x.strip(), None),
                         message_content = POST('content')):
    is_super_user = is_super_user_api(request)
    if forged and not is_super_user:
        return json_error("User not authorized for this query")

    if len(message_to) == 0:
        return json_error("Message must have recipients.")
    if len(message_content) > MAX_MESSAGE_LENGTH:
        return json_error("Message too long.")

    if client.name == "zephyr_mirror":
        # Here's how security works for non-superuser mirroring:
        #
        # The message must be (1) a private message (2) that
        # is both sent and received exclusively by other users in your
        # realm which (3) must be the MIT realm and (4) you must have
        # received the message.
        #
        # If that's the case, we let it through, but we still have the
        # security flaw that we're trusting your Hesiod data for users
        # you report having sent you a message.
        if "sender" not in request.POST:
            return json_error("Missing sender")
        if message_type_name != "private" and not is_super_user:
            return json_error("User not authorized for this query")
        (valid_input, mirror_sender) = \
            create_mirrored_message_users(request, user_profile, message_to)
        if not valid_input:
            return json_error("Invalid mirrored message")
        if user_profile.realm.domain != "mit.edu":
            return json_error("Invalid mirrored realm")
        sender = mirror_sender
    else:
        sender = user_profile

    if message_type_name == 'stream':
        if subject_name is None:
            return json_error("Missing subject")
        if len(message_to) > 1:
            return json_error("Cannot send to multiple streams")
        stream_name = message_to[0].strip()
        if stream_name == "":
            return json_error("Stream can't be empty")
        if subject_name == "":
            return json_error("Subject can't be empty")
        if len(stream_name) > 30:
            return json_error("Stream name too long")
        if len(subject_name) > MAX_SUBJECT_LENGTH:
            return json_error("Subject too long")

        if not valid_stream_name(stream_name):
            return json_error("Invalid stream name")
        ## FIXME: Commented out temporarily while we figure out what we want
        # if not valid_stream_name(subject_name):
        #     return json_error("Invalid subject name")

        try:
            stream = Stream.objects.get(realm=user_profile.realm, name__iexact=stream_name)
        except Stream.DoesNotExist:
            return json_error("Stream does not exist")
        recipient = Recipient.objects.get(type_id=stream.id, type=Recipient.STREAM)
    elif message_type_name == 'private':
        not_forged_zephyr_mirror = client and client.name == "zephyr_mirror" and not forged
        try:
            recipient = recipient_for_emails(message_to, not_forged_zephyr_mirror, user_profile, sender)
        except ValidationError, e:
            return json_error(e.messages[0])
    else:
        return json_error("Invalid message type")

    message = Message()
    message.sender = sender
    message.content = message_content
    message.recipient = recipient
    if message_type_name == 'stream':
        message.subject = subject_name
    if forged:
        # Forged messages come with a timestamp
        message.pub_date = timestamp_to_datetime(request.POST['time'])
    else:
        message.pub_date = now()
    message.sending_client = client

    if client.name == "zephyr_mirror" and already_sent_mirrored_message(message):
        return json_success()

    do_send_message(message)

    return json_success()

@authenticated_api_view
def api_get_public_streams(request, user_profile):
    # Only get streams someone is currently subscribed to
    subs_filter = Subscription.objects.filter(active=True).values('recipient_id')
    stream_ids = Recipient.objects.filter(
        type=Recipient.STREAM, id__in=subs_filter).values('type_id')
    streams = sorted(stream.name for stream in
                     Stream.objects.filter(id__in = stream_ids,
                                           realm=user_profile.realm))
    return json_success({"streams": streams})

default_stream_color = "#c2c2c2"

def get_stream_color(sub):
    try:
        return StreamColor.objects.get(subscription=sub).color
    except StreamColor.DoesNotExist:
        return default_stream_color

def gather_subscriptions(user_profile):
    # This is a little awkward because the StreamColor table has foreign keys
    # to Subscription, but not vice versa, and not all Subscriptions have a
    # StreamColor.
    #
    # We could do this with a single OUTER JOIN query but Django's ORM does
    # not provide a simple way to specify one.

    # For now, don't display the subscription for your ability to receive personals.
    subs = Subscription.objects.filter(
        user_profile    = user_profile,
        active          = True,
        recipient__type = Recipient.STREAM)
    with_color = StreamColor.objects.filter(subscription__in = subs).select_related()
    no_color   = subs.exclude(id__in = with_color.values('subscription_id')).select_related()

    result = [(get_display_recipient(sc.subscription.recipient), sc.color)
        for sc in with_color]
    result.extend((get_display_recipient(sub.recipient), default_stream_color)
        for sub in no_color)

    return sorted(result)

@authenticated_api_view
def api_list_subscriptions(request, user_profile):
    return json_success({"subscriptions": gather_subscriptions(user_profile)})

@authenticated_json_post_view
def json_list_subscriptions(request, user_profile):
    return json_success({"subscriptions": gather_subscriptions(user_profile)})

@authenticated_api_view
def api_remove_subscriptions(request, user_profile):
    return remove_subscriptions_backend(request, user_profile)

@authenticated_json_post_view
def json_remove_subscriptions(request, user_profile):
    return remove_subscriptions_backend(request, user_profile)

@has_request_variables
def remove_subscriptions_backend(request, user_profile,
                                 streams_raw = POST("subscriptions", json_to_list)):
    streams = []
    for stream_name in set(stream_name.strip() for stream_name in streams_raw):
        stream = get_stream(stream_name, user_profile.realm)
        if stream is None:
            return json_error("Stream %s does not exist" % stream_name)
        streams.append(stream)

    result = dict(removed=[], not_subscribed=[])
    for stream in streams:
        did_remove = do_remove_subscription(user_profile, stream)
        if did_remove:
            result["removed"].append(stream.name)
        else:
            result["not_subscribed"].append(stream.name)

    return json_success(result)

def valid_stream_name(name):
    return name != ""

@authenticated_api_view
def api_add_subscriptions(request, user_profile):
    return add_subscriptions_backend(request, user_profile)

@authenticated_json_post_view
def json_add_subscriptions(request, user_profile):
    return add_subscriptions_backend(request, user_profile)

@has_request_variables
def add_subscriptions_backend(request, user_profile,
                              streams_raw = POST('subscriptions', json_to_list)):
    stream_names = []
    for stream_name in streams_raw:
        stream_name = stream_name.strip()
        if len(stream_name) > 30:
            return json_error("Stream name (%s) too long." % (stream_name,))
        if not valid_stream_name(stream_name):
            return json_error("Invalid stream name (%s)." % (stream_name,))
        stream_names.append(stream_name)

    result = dict(subscribed=[], already_subscribed=[])
    for stream_name in set(stream_names):
        stream = create_stream_if_needed(user_profile.realm, stream_name)
        did_subscribe = do_add_subscription(user_profile, stream)
        if did_subscribe:
            result["subscribed"].append(stream_name)
        else:
            result["already_subscribed"].append(stream_name)

    return json_success(result)

@authenticated_json_post_view
@has_request_variables
def json_change_settings(request, user_profile, full_name=POST,
                         old_password=POST, new_password=POST,
                         confirm_password=POST,
                         # enable_desktop_notification needs to default to False
                         # because browsers POST nothing for an unchecked checkbox
                         enable_desktop_notifications=POST(converter=lambda x: x == "on",
                                                           default=False)):
    if new_password != "" or confirm_password != "":
        if new_password != confirm_password:
            return json_error("New password must match confirmation password!")
        if not authenticate(username=user_profile.user.email, password=old_password):
            return json_error("Wrong password!")
        do_change_password(user_profile.user, new_password)

    result = {}
    if user_profile.full_name != full_name and full_name.strip() != "":
        do_change_full_name(user_profile, full_name.strip())
        result['full_name'] = full_name

    if user_profile.enable_desktop_notifications != enable_desktop_notifications:
        do_change_enable_desktop_notifications(user_profile, enable_desktop_notifications)
        result['enable_desktop_notifications'] = enable_desktop_notifications

    return json_success(result)

@authenticated_json_post_view
@has_request_variables
def json_stream_exists(request, user_profile, stream=POST):
    if not valid_stream_name(stream):
        return json_error("Invalid characters in stream name")
    stream = get_stream(stream, user_profile.realm)
    result = {"exists": bool(stream)}
    if stream is not None:
        recipient = Recipient.objects.get(type_id=stream.id, type=Recipient.STREAM)
        result["subscribed"] = Subscription.objects.filter(user_profile=user_profile,
                                                           recipient=recipient,
                                                           active=True).exists()
    return json_success(result)

def set_stream_color(user_profile, stream_name, color):
    stream = get_stream(stream_name, user_profile.realm)
    if not stream:
        return json_error("Invalid stream %s" % (stream.name,))
    recipient = Recipient.objects.get(type_id=stream.id, type=Recipient.STREAM)
    subscription = Subscription.objects.filter(user_profile=user_profile,
                                               recipient=recipient, active=True)
    if not subscription.exists():
        return json_error("Not subscribed to stream %s" % (stream_name,))

    stream_color, _ = StreamColor.objects.get_or_create(subscription=subscription[0])
    # TODO: sanitize color.
    stream_color.color = color
    stream_color.save()

class SubscriptionProperties(object):
    """
    A class for managing GET and POST requests for subscription properties. The
    name for a request handler is <request type>_<property name>.

    Requests must have already been authenticated before being processed here.

    Requests that set or change subscription properties should typically log the
    change through log_event.
    """
    def __call__(self, request, user_profile, property):
        property_method = getattr(self, "%s_%s" % (request.method.lower(), property), None)
        if not property_method:
            return json_error("Unknown property or invalid verb for %s" % (property,))

        return property_method(request, user_profile)

    def request_property(self, request_dict, property):
        return request_dict.get(property, "").strip()

    def get_stream_colors(self, request, user_profile):
        return json_success({"stream_colors": gather_subscriptions(user_profile)})

    def post_stream_colors(self, request, user_profile):
        stream_name = self.request_property(request.POST, "stream_name")
        if not stream_name:
            return json_error("Missing stream_name")
        color = self.request_property(request.POST, "color")
        if not color:
            return json_error("Missing color")

        set_stream_color(user_profile, stream_name, color)
        log_subscription_property_change(user_profile.user.email, "stream_color",
                                         {"stream_name": stream_name, "color": color})
        return json_success()

subscription_properties = SubscriptionProperties()

def make_property_call(request, query_dict, user_profile):
    property = query_dict.get("property").strip()
    if not property:
        return json_error("Missing property")

    return subscription_properties(request, user_profile, property.lower())

def make_get_property_call(request, user_profile):
    return make_property_call(request, request.GET, user_profile)

def make_post_property_call(request, user_profile):
    return make_property_call(request, request.POST, user_profile)

@authenticated_json_view
def json_subscription_property(request, user_profile):
    """
    This is the entry point to accessing or changing subscription
    properties. Authentication happens here.

    Add a handler for a new subscription property in SubscriptionProperties.
    """
    if request.method == "GET":
        return make_get_property_call(request, user_profile)
    elif request.method == "POST":
        return make_post_property_call(request, user_profile)
    else:
        return json_error("Invalid verb")

@csrf_exempt
@require_post
@has_request_variables
def api_fetch_api_key(request, username=POST, password=POST):
    user = authenticate(username=username, password=password)
    if user is None:
        return json_error("Your username or password is incorrect.", status=403)
    if not user.is_active:
        return json_error("Your account has been disabled.", status=403)
    return json_success({"api_key": user.userprofile.api_key})

@authenticated_json_post_view
@has_request_variables
def json_fetch_api_key(request, user_profile, password=POST):
    if not request.user.check_password(password):
        return json_error("Your username or password is incorrect.")
    return json_success({"api_key": user_profile.api_key})

class ActivityTable(object):
    def __init__(self, client_name, queries, default_tab=False):
        self.default_tab = default_tab
        self.has_pointer = False
        self.rows = {}
        for url, query_name in queries:
            if 'pointer' in query_name:
                self.has_pointer = True
            for record in UserActivity.objects.filter(
                    query=url,
                    client__name=client_name):
                row = self.rows.setdefault(record.user_profile.user.email, {})
                row['realm'] = record.user_profile.realm.domain
                row[query_name + '_count'] = record.count
                row[query_name + '_last' ] = record.last_visit

        for row in self.rows.values():
            # kind of a hack
            last_action = max(v for v in row.values() if isinstance(v, datetime.datetime))
            age = now() - last_action
            if age < datetime.timedelta(minutes=10):
                row['class'] = 'recently_active'
            elif age >= datetime.timedelta(days=1):
                row['class'] = 'long_inactive'
            row['age'] = age

    def sorted_rows(self):
        return sorted(self.rows.iteritems(), key=lambda (k,r): r['age'])

def can_view_activity(request):
    return request.user.userprofile.realm.domain == 'humbughq.com'

@login_required(login_url = settings.HOME_NOT_LOGGED_IN)
def get_activity(request):
    if not can_view_activity(request):
        return HttpResponseRedirect(reverse('zephyr.views.login_page'))

    web_queries = (
        ("/json/get_updates",    "get_updates"),
        ("/json/send_message",   "send_message"),
        ("/json/update_pointer", "update_pointer"),
    )

    api_queries = (
        ("/api/v1/get_messages",  "get_updates"),
        ("/api/v1/send_message",  "send_message"),
    )

    return render_to_response('zephyr/activity.html',
        { 'data': {
            'Website': ActivityTable('website',       web_queries, default_tab=True),
            'Mirror':  ActivityTable('zephyr_mirror', api_queries),
            'API':     ActivityTable('API',           api_queries)
        }}, context_instance=RequestContext(request))

@authenticated_api_view
@has_request_variables
def api_github_landing(request, user_profile, event=POST,
                       payload=POST(converter=json_to_dict)):
    # TODO: this should all be moved to an external bot

    repository = payload['repository']

    if event == 'pull_request':
        pull_req = payload['pull_request']

        subject = "%s: pull request %d" % (repository['name'],
                                           pull_req['number'])
        content = ("Pull request from %s [%s](%s):\n\n %s\n\n> %s"
                   % (pull_req['user']['login'],
                      payload['action'],
                      pull_req['html_url'],
                      pull_req['title'],
                      pull_req['body']))
    elif event == 'push':
        short_ref = re.sub(r'^refs/heads/', '', payload['ref'])
        subject = repository['name']
        if re.match(r'^0+$', payload['after']):
            content = "%s deleted branch %s" % (payload['pusher']['name'],
                                                short_ref)
        elif len(payload['commits']) == 0:
            content = ("%s [force pushed](%s) to branch %s.  Head is now %s"
                       % (payload['pusher']['name'],
                          payload['compare'],
                          short_ref,
                          payload['after'][:7]))
        else:
            content = ("%s [pushed](%s) to branch %s\n\n"
                       % (payload['pusher']['name'],
                          payload['compare'],
                          short_ref))
            num_commits = len(payload['commits'])
            max_commits = 10
            truncated_commits = payload['commits'][:max_commits]
            for commit in truncated_commits:
                short_id = commit['id'][:7]
                (short_commit_msg, _, _) = commit['message'].partition("\n")
                content += "* [%s](%s): %s\n" % (short_id, commit['url'],
                                                 short_commit_msg)
            if (num_commits > max_commits):
                content += ("\n[and %d more commits]"
                            % (num_commits - max_commits,))
    else:
        # We don't handle other events even though we get notified
        # about them
        return json_success()

    if len(subject) > MAX_SUBJECT_LENGTH:
        subject = subject[:57].rstrip() + '...'

    return send_message_backend(request, user_profile, get_client("github_bot"),
                                message_type_name="stream",
                                message_to=["commits"],
                                forged=False, subject_name=subject,
                                message_content=content)


# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Realm'
        db.create_table('zephyr_realm', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
        ))
        db.send_create_signal('zephyr', ['Realm'])

        # Adding model 'UserProfile'
        db.create_table('zephyr_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('pointer', self.gf('django.db.models.fields.IntegerField')()),
            ('last_pointer_updater', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('realm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Realm'])),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('enable_desktop_notifications', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('zephyr', ['UserProfile'])

        # Adding model 'PreregistrationUser'
        db.create_table('zephyr_preregistrationuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('zephyr', ['PreregistrationUser'])

        # Adding model 'MitUser'
        db.create_table('zephyr_mituser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('zephyr', ['MitUser'])

        # Adding model 'Stream'
        db.create_table('zephyr_stream', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30, db_index=True)),
            ('realm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Realm'])),
        ))
        db.send_create_signal('zephyr', ['Stream'])

        # Adding unique constraint on 'Stream', fields ['name', 'realm']
        db.create_unique('zephyr_stream', ['name', 'realm_id'])

        # Adding model 'Recipient'
        db.create_table('zephyr_recipient', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('type', self.gf('django.db.models.fields.PositiveSmallIntegerField')(db_index=True)),
        ))
        db.send_create_signal('zephyr', ['Recipient'])

        # Adding unique constraint on 'Recipient', fields ['type', 'type_id']
        db.create_unique('zephyr_recipient', ['type', 'type_id'])

        # Adding model 'Client'
        db.create_table('zephyr_client', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30, db_index=True)),
        ))
        db.send_create_signal('zephyr', ['Client'])

        # Adding model 'Message'
        db.create_table('zephyr_message', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Recipient'])),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=60, db_index=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('sending_client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Client'])),
        ))
        db.send_create_signal('zephyr', ['Message'])

        # Adding model 'UserMessage'
        db.create_table('zephyr_usermessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Message'])),
            ('archived', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('zephyr', ['UserMessage'])

        # Adding unique constraint on 'UserMessage', fields ['user_profile', 'message']
        db.create_unique('zephyr_usermessage', ['user_profile_id', 'message_id'])

        # Adding model 'Subscription'
        db.create_table('zephyr_subscription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Recipient'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('zephyr', ['Subscription'])

        # Adding unique constraint on 'Subscription', fields ['user_profile', 'recipient']
        db.create_unique('zephyr_subscription', ['user_profile_id', 'recipient_id'])

        # Adding model 'Huddle'
        db.create_table('zephyr_huddle', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('huddle_hash', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
        ))
        db.send_create_signal('zephyr', ['Huddle'])

        # Adding model 'UserActivity'
        db.create_table('zephyr_useractivity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Client'])),
            ('query', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('count', self.gf('django.db.models.fields.IntegerField')()),
            ('last_visit', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('zephyr', ['UserActivity'])

        # Adding unique constraint on 'UserActivity', fields ['user_profile', 'client', 'query']
        db.create_unique('zephyr_useractivity', ['user_profile_id', 'client_id', 'query'])

        # Adding model 'DefaultStream'
        db.create_table('zephyr_defaultstream', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('realm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Realm'])),
            ('stream', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Stream'])),
        ))
        db.send_create_signal('zephyr', ['DefaultStream'])

        # Adding unique constraint on 'DefaultStream', fields ['realm', 'stream']
        db.create_unique('zephyr_defaultstream', ['realm_id', 'stream_id'])

        # Adding model 'StreamColor'
        db.create_table('zephyr_streamcolor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subscription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Subscription'])),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('zephyr', ['StreamColor'])


    def backwards(self, orm):
        # Removing unique constraint on 'DefaultStream', fields ['realm', 'stream']
        db.delete_unique('zephyr_defaultstream', ['realm_id', 'stream_id'])

        # Removing unique constraint on 'UserActivity', fields ['user_profile', 'client', 'query']
        db.delete_unique('zephyr_useractivity', ['user_profile_id', 'client_id', 'query'])

        # Removing unique constraint on 'Subscription', fields ['user_profile', 'recipient']
        db.delete_unique('zephyr_subscription', ['user_profile_id', 'recipient_id'])

        # Removing unique constraint on 'UserMessage', fields ['user_profile', 'message']
        db.delete_unique('zephyr_usermessage', ['user_profile_id', 'message_id'])

        # Removing unique constraint on 'Recipient', fields ['type', 'type_id']
        db.delete_unique('zephyr_recipient', ['type', 'type_id'])

        # Removing unique constraint on 'Stream', fields ['name', 'realm']
        db.delete_unique('zephyr_stream', ['name', 'realm_id'])

        # Deleting model 'Realm'
        db.delete_table('zephyr_realm')

        # Deleting model 'UserProfile'
        db.delete_table('zephyr_userprofile')

        # Deleting model 'PreregistrationUser'
        db.delete_table('zephyr_preregistrationuser')

        # Deleting model 'MitUser'
        db.delete_table('zephyr_mituser')

        # Deleting model 'Stream'
        db.delete_table('zephyr_stream')

        # Deleting model 'Recipient'
        db.delete_table('zephyr_recipient')

        # Deleting model 'Client'
        db.delete_table('zephyr_client')

        # Deleting model 'Message'
        db.delete_table('zephyr_message')

        # Deleting model 'UserMessage'
        db.delete_table('zephyr_usermessage')

        # Deleting model 'Subscription'
        db.delete_table('zephyr_subscription')

        # Deleting model 'Huddle'
        db.delete_table('zephyr_huddle')

        # Deleting model 'UserActivity'
        db.delete_table('zephyr_useractivity')

        # Deleting model 'DefaultStream'
        db.delete_table('zephyr_defaultstream')

        # Deleting model 'StreamColor'
        db.delete_table('zephyr_streamcolor')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Stream']"})
        },
        'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Recipient']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Realm']"})
        },
        'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Subscription']"})
        },
        'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']"})
        },
        'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']"})
        },
        'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']"})
        },
        'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['zephyr']

import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.core import validators

from zephyr.models import Realm, do_create_user
from zephyr.views import do_send_message, notify_new_user
from zephyr.lib.initial_password import initial_password

class Command(BaseCommand):
    help = "Create the specified user with a default initial password."

    def handle(self, *args, **options):
        try:
            email, full_name = args
            try:
                validators.validate_email(email)
            except ValidationError:
                raise CommandError("Invalid email address.")
        except ValueError:
            if len(args) != 0:
                raise CommandError("Either specify an email and full name" + \
                        "as two parameters, or specify no parameters for" + \
                        "interactive user creation.")
                return 1
            else:
                while True:
                    email = raw_input("Email: ")
                    try:
                        validators.validate_email(email)
                        break
                    except ValidationError:
                        print >> sys.stderr, "Invalid email address."
                full_name = raw_input("Full name: ")

        try:
            realm = Realm.objects.get(domain=email.split('@')[-1])
        except Realm.DoesNotExist:
            raise CommandError("Realm does not exist.")

        try:
            notify_new_user(do_create_user(email, initial_password(email),
                realm, full_name, email.split('@')[0]),
                internal=True)
        except IntegrityError:
            raise CommandError("User already exists.")

from django.core.management.base import BaseCommand
from zephyr.retention_policy     import get_UserMessages_to_expunge
from zephyr.models               import Message

class Command(BaseCommand):
    help = ('Expunge old UserMessages and Messages from the database, '
            + 'according to the retention policy.')

    def handle(self, *args, **kwargs):
        get_UserMessages_to_expunge().delete()
        Message.remove_unreachable()

from django.core.management.base import BaseCommand

from zephyr.models import Realm, set_default_streams, log_event

from optparse import make_option
import sys
import time

class Command(BaseCommand):
    help = """Set default streams for a realm

Users created under this realm will start out with these streams. This
command is not additive: if you re-run it on a domain with a different
set of default streams, those will be the new complete set of default
streams.

For example:

python manage.py set_default_streams --domain=foo.com --streams=foo,bar,baz
python manage.py set_default_streams --domain=foo.com --streams="foo,bar,baz with space"
python manage.py set_default_streams --domain=foo.com --streams=
"""

    option_list = BaseCommand.option_list + (
        make_option('-d', '--domain',
                    dest='domain',
                    type='str',
                    help='The name of the existing realm to which to attach default streams.'),
        make_option('-s', '--streams',
                    dest='streams',
                    type='str',
                    help='A comma-separated list of stream names.'),
        )

    def handle(self, **options):
        if options["domain"] is None or options["streams"] is None:
            print >>sys.stderr, "Please provide both a domain name and a default \
set of streams (which can be empty, with `--streams=`)."
            exit(1)

        stream_names = [stream.strip() for stream in options["streams"].split(",")]
        realm = Realm.objects.get(domain=options["domain"])
        set_default_streams(realm, stream_names)

        log_event({'type': 'default_streams',
                   'domain': realm.domain,
                   'streams': stream_names})

from optparse import make_option
from django.core.management.base import BaseCommand
from confirmation.models import Confirmation
from zephyr.models import User, MitUser

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--resend', '-r', dest='resend', action='store_true',
                    help='Send tokens even if tokens were previously sent for the user.'),)
    help = "Generate an activation email to send to MIT users."

    def handle(self, *args, **options):
        for username in args:
            email = username + "@mit.edu"
            try:
                User.objects.get(email=email)
            except User.DoesNotExist:
                print username + ": User does not exist in database"
                continue
            mit_user, created = MitUser.objects.get_or_create(email=email)
            if not created and not options["resend"]:
                print username + ": User already exists. Use -r to resend."
            else:
                Confirmation.objects.send_confirmation(mit_user, email)
                print username + ": Mailed."


from django.core.management.base import NoArgsCommand
from zephyr.models import clear_database

class Command(NoArgsCommand):
    help = "Clear only tables we change: messages, accounts + sessions"

    def handle_noargs(self, **options):
        clear_database()
        self.stdout.write("Successfully cleared the database.\n")


from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import User
import simplejson

def dump():
    passwords = []
    for u in User.objects.all():
        passwords.append((u.email, u.password))
    file("dumped-passwords", "w").write(simplejson.dumps(passwords) + "\n")

def restore(change):
    for (email, password) in simplejson.loads(file("dumped-passwords").read()):
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            print "Skipping...", email
            continue
        if change:
            user.password = password
            user.save()

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--restore', default=False, action='store_true'),
        make_option('--dry-run', '-n', default=False, action='store_true'),)

    def handle(self, *args, **options):
        if options["restore"]:
            restore(change=not options['dry_run'])
        else:
            dump()

from django.core.management.base import BaseCommand
from zephyr.lib.initial_password import initial_password, initial_api_key

class Command(BaseCommand):
    help = "Print the initial password and API key for accounts as created by populate_db"

    fmt = '%-30s %-16s  %-32s'

    def handle(self, *args, **options):
        print self.fmt % ('email', 'password', 'API key')
        for email in args:
            if '@' not in email:
                print 'ERROR: %s does not look like an email address' % (email,)
                continue
            print self.fmt % (email, initial_password(email), initial_api_key(email))

from optparse import make_option
from django.core.management.base import BaseCommand

from zephyr.models import Realm, UserProfile

# Helper to be used with manage.py shell to get rid of bad users on prod.
def banish_busted_users(change=False):
    for u in UserProfile.objects.select_related().all():
        if (u.user.is_active or u.realm.domain != "mit.edu"):
            continue
        (banished_realm, _) = Realm.objects.get_or_create(domain="mit.deleted")
        if "|mit.edu@mit.edu" in u.user.email.lower():
            print u.user.email
            if change:
                u.realm = banished_realm
                u.user.email = u.user.email.split("@")[0] + "@" + banished_realm.domain
                u.user.save()
                u.save()

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run', '-n', dest='dry_run', default=False, action='store_true'),)

    def handle(self, *args, **options):
        banish_busted_users(change=not options['dry_run'])

from optparse import make_option
from django.core.management.base import BaseCommand

from zephyr.models import UserProfile, compute_mit_user_fullname
# Helper to be used with manage.py shell to fix bad names on prod.
def update_mit_fullnames(change=False):
    for u in UserProfile.objects.select_related().all():
        if (u.user.is_active or u.realm.domain != "mit.edu"):
            # Don't change fullnames for non-MIT users or users who
            # actually have an account (is_active) and thus have
            # presumably set their fullname how they like it.
            continue
        computed_name = compute_mit_user_fullname(u.user.email)
        if u.full_name != computed_name:
            print "%s: %s => %s" % (u.user.email, u.full_name, computed_name)
            if change:
                u.full_name = computed_name
                u.save()

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run', '-n', dest='dry_run', default=False, action='store_true'),)

    def handle(self, *args, **options):
        update_mit_fullnames(change=not options['dry_run'])

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.conf import settings
import os
import sys
import tornado.web
import logging

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noreload', action='store_false',
            dest='auto_reload', default=True,
            help="Configures tornado to not auto-reload (for prod use)."),
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
        from tornado import httpserver, wsgi, ioloop, web

        try:
            addr, port = addrport.split(':')
        except ValueError:
            addr, port = '', addrport

        if not addr:
            addr = '127.0.0.1'

        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)

        auto_reload = options.get('auto_reload', False)
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

        if auto_reload:
            from tornado import autoreload
            autoreload.start()

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

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import Realm, UserProfile, Message, UserMessage
from zephyr.lib.time import datetime_to_timestamp, timestamp_to_datetime
import simplejson

def dump():
    pointers = []
    for u in UserProfile.objects.select_related("user__email").all():
        pointer = u.pointer
        if pointer != -1:
            pub_date = Message.objects.get(id=pointer).pub_date
            pointers.append((u.user.email, datetime_to_timestamp(pub_date)))
        else:
            pointers.append((u.user.email, -1))
    file("dumped-pointers", "w").write(simplejson.dumps(pointers) + "\n")

def restore(change):
    for (email, timestamp) in simplejson.loads(file("dumped-pointers").read()):
        try:
            u = UserProfile.objects.get(user__email__iexact=email)
        except UserProfile.DoesNotExist:
            print "Skipping...", email
            continue
        if timestamp == -1:
            pointer = -1
        else:
            try:
                pointer = UserMessage.objects.filter(user_profile=u,
                    message__pub_date__gte=timestamp_to_datetime(timestamp)).order_by("message")[0].message_id
            except IndexError:
                print "Alert...", email, timestamp
                continue
        if change:
            u.pointer = pointer
            u.save()

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--restore', default=False, action='store_true'),
        make_option('--dry-run', '-n', default=False, action='store_true'),)

    def handle(self, *args, **options):
        if options["restore"]:
            restore(change=not options['dry_run'])
        else:
            dump()

from django.core.management.base import BaseCommand
from zephyr.models import Realm, Message, UserProfile, Recipient, create_stream_if_needed, \
        get_client, do_create_realm
from zephyr.views import do_send_message
from django.utils.timezone import now

class Command(BaseCommand):
    help = "Create a realm for the specified domain(s)."

    def handle(self, *args, **options):
        for domain in args:
            realm, created = do_create_realm(domain)
            if created:
                print domain + ": Created."
            else:
                print domain + ": Already exists."


from django.core.management.base import BaseCommand
from django.utils.timezone import utc, now

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from zephyr.models import Message, UserProfile, Stream, Recipient, Client, \
    Subscription, Huddle, get_huddle, Realm, UserMessage, get_user_profile_by_id, \
    bulk_create_realms, bulk_create_streams, bulk_create_users, bulk_create_huddles, \
    bulk_create_clients, set_default_streams, \
    do_send_message, clear_database, StreamColor, \
    get_huddle_hash, get_client, do_activate_user
from zephyr.lib.parallel import run_parallel
from django.db import transaction, connection
from django.conf import settings
from zephyr.lib.bulk_create import batch_bulk_create
from zephyr.lib.time import timestamp_to_datetime
from zephyr.models import MAX_MESSAGE_LENGTH

import simplejson
import datetime
import random
import sys
import os
from optparse import make_option

settings.TORNADO_SERVER = None

def create_users(realms, name_list):
    user_set = set()
    for full_name, email in name_list:
        (short_name, domain) = email.split("@")
        user_set.add((email, full_name, short_name, True))
    bulk_create_users(realms, user_set)

def create_streams(realms, realm, stream_list):
    stream_set = set()
    for stream_name in stream_list:
        stream_set.add((realm.domain, stream_name))
    bulk_create_streams(realms, stream_set)

class Command(BaseCommand):
    help = "Populate a test database"

    option_list = BaseCommand.option_list + (
        make_option('-n', '--num-messages',
                    dest='num_messages',
                    type='int',
                    default=600,
                    help='The number of messages to create.'),
        make_option('--extra-users',
                    dest='extra_users',
                    type='int',
                    default=0,
                    help='The number of extra users to create'),
        make_option('--huddles',
                    dest='num_huddles',
                    type='int',
                    default=3,
                    help='The number of huddles to create.'),
        make_option('--personals',
                    dest='num_personals',
                    type='int',
                    default=6,
                    help='The number of personal pairs to create.'),
        make_option('--threads',
                    dest='threads',
                    type='int',
                    default=10,
                    help='The number of threads to use.'),
        make_option('--percent-huddles',
                    dest='percent_huddles',
                    type='float',
                    default=15,
                    help='The percent of messages to be huddles.'),
        make_option('--percent-personals',
                    dest='percent_personals',
                    type='float',
                    default=15,
                    help='The percent of messages to be personals.'),
        make_option('--stickyness',
                    dest='stickyness',
                    type='float',
                    default=20,
                    help='The percent of messages to repeat recent folks.'),
        make_option('--nodelete',
                    action="store_false",
                    default=True,
                    dest='delete',
                    help='Whether to delete all the existing messages.'),
        make_option('--test-suite',
                    default=False,
                    action="store_true",
                    help='Whether to delete all the existing messages.'),
        make_option('--replay-old-messages',
                    action="store_true",
                    default=False,
                    dest='replay_old_messages',
                    help='Whether to replace the log of old messages.'),
        )

    def handle(self, **options):
        if options["percent_huddles"] + options["percent_personals"] > 100:
            self.stderr.write("Error!  More than 100% of messages allocated.\n")
            return

        if options["delete"]:
            # Start by clearing all the data in our database
            clear_database()

            # Create our two default realms
            humbug_realm = Realm.objects.create(domain="humbughq.com")
            Realm.objects.create(domain="mit.edu")
            realms = {}
            for realm in Realm.objects.all():
                realms[realm.domain] = realm

            # Create test Users (UserProfiles are automatically created,
            # as are subscriptions to the ability to receive personals).
            names = [("Othello, the Moor of Venice", "othello@humbughq.com"), ("Iago", "iago@humbughq.com"),
                     ("Prospero from The Tempest", "prospero@humbughq.com"),
                     ("Cordelia Lear", "cordelia@humbughq.com"), ("King Hamlet", "hamlet@humbughq.com")]
            for i in xrange(options["extra_users"]):
                names.append(('Extra User %d' % (i,), 'extrauser%d@humbughq.com' % (i,)))
            create_users(realms, names)
            # Create public streams.
            stream_list = ["Verona", "Denmark", "Scotland", "Venice", "Rome"]
            create_streams(realms, humbug_realm, stream_list)
            recipient_streams = [recipient.type_id for recipient in
                                 Recipient.objects.filter(type=Recipient.STREAM)]
            # Create subscriptions to streams
            subscriptions_to_add = []
            profiles = UserProfile.objects.select_related().all()
            for i, profile in enumerate(profiles):
                # Subscribe to some streams.
                for type_id in recipient_streams[:int(len(recipient_streams) *
                                                      float(i)/len(profiles)) + 1]:
                    r = Recipient.objects.get(type=Recipient.STREAM, type_id=type_id)
                    s = Subscription(recipient=r, user_profile=profile)
                    subscriptions_to_add.append(s)
            batch_bulk_create(Subscription, subscriptions_to_add)
        else:
            humbug_realm = Realm.objects.get(domain="humbughq.com")
            recipient_streams = [klass.type_id for klass in
                                 Recipient.objects.filter(type=Recipient.STREAM)]

        # Extract a list of all users
        users = [user.id for user in User.objects.all()]

        # Create several initial huddles
        for i in xrange(options["num_huddles"]):
            get_huddle(random.sample(users, random.randint(3, 4)))

        # Create several initial pairs for personals
        personals_pairs = [random.sample(users, 2)
                           for i in xrange(options["num_personals"])]

        threads = options["threads"]
        jobs = []
        for i in xrange(threads):
            count = options["num_messages"] / threads
            if i < options["num_messages"] % threads:
                count += 1
            jobs.append((count, personals_pairs, options, self.stdout.write))
        for status, job in run_parallel(send_messages, jobs, threads=threads):
            pass
        # Get a new database connection, after our parallel jobs
        # closed the original one
        connection.close()

        if options["delete"]:
            # Create the "website" and "API" clients; if we don't, the
            # default values in zephyr/decorators.py will not work
            # with the Django test suite.
            get_client("website")
            get_client("API")

            # Create internal users; first the ones who are referenced
            # directly by the test suite; the MIT ones are needed to
            # test the Zephyr mirroring codepaths.
            testsuite_mit_users = [
                ("Fred Sipb (MIT)", "sipbtest@mit.edu"),
                ("Athena Consulting Exchange User (MIT)", "starnine@mit.edu"),
                ("Esp Classroom (MIT)", "espuser@mit.edu"),
                ]
            create_users(realms, testsuite_mit_users)

            # These bots are directly referenced from code and thus
            # are needed for the test suite.
            hardcoded_humbug_users_nosubs = [
                ("Humbug New User Bot", "humbug+signups@humbughq.com"),
                ("Humbug Error Bot", "humbug+errors@humbughq.com"),
                ]
            create_users(realms, hardcoded_humbug_users_nosubs)

            if not options["test_suite"]:
                # To keep the messages.json fixtures file for the test
                # suite fast, don't add these users and subscriptions
                # when running populate_db for the test suite

                internal_mit_users = []
                create_users(realms, internal_mit_users)

                internal_humbug_users = []
                create_users(realms, internal_humbug_users)
                humbug_stream_list = ["devel", "all", "humbug", "design", "support", "social", "test"]
                create_streams(realms, humbug_realm, humbug_stream_list)

                # Now subscribe everyone to these streams
                subscriptions_to_add = []
                profiles = UserProfile.objects.select_related().filter(realm=humbug_realm)
                for cls in humbug_stream_list:
                    stream = Stream.objects.get(name=cls, realm=humbug_realm)
                    recipient = Recipient.objects.get(type=Recipient.STREAM, type_id=stream.id)
                    for profile in profiles:
                        # Subscribe to some streams.
                        s = Subscription(recipient=recipient, user_profile=profile)
                        subscriptions_to_add.append(s)
                batch_bulk_create(Subscription, subscriptions_to_add)

                # These bots are not needed by the test suite
                internal_humbug_users_nosubs = [
                    ("Humbug Commit Bot", "humbug+commits@humbughq.com"),
                    ("Humbug Trac Bot", "humbug+trac@humbughq.com"),
                    ("Humbug Nagios Bot", "humbug+nagios@humbughq.com"),
                    ("Humbug Feedback Bot", "feedback@humbughq.com"),
                    ]
                create_users(realms, internal_humbug_users_nosubs)

            self.stdout.write("Successfully populated test database.\n")
        if options["replay_old_messages"]:
            restore_saved_messages()
        connection.close()

recipient_hash = {}
def get_recipient_by_id(rid):
    if rid in recipient_hash:
        return recipient_hash[rid]
    return Recipient.objects.get(id=rid)

def restore_saved_messages():
    old_messages = []
    duplicate_suppression_hash = {}

    stream_dict = {}
    user_set = set()
    email_set = set(u.email for u in User.objects.all())
    realm_set = set()
    # Initial client_set is nonempty temporarily because we don't have
    # clients in logs at all right now -- later we can start with nothing.
    client_set = set(["populate_db", "website", "zephyr_mirror"])
    huddle_user_set = set()
    # First, determine all the objects our messages will need.
    print datetime.datetime.now(), "Creating realms/streams/etc..."
    def process_line(line):
        old_message_json = line.strip()

        # Due to populate_db's shakespeare mode, we have a lot of
        # duplicate messages in our log that only differ in their
        # logged ID numbers (same timestamp, content, etc.).  With
        # sqlite, bulk creating those messages won't work properly: in
        # particular, the first 100 messages will actually only result
        # in 20 rows ending up in the target table, which screws up
        # the below accounting where for handling changing
        # subscriptions, we assume that the Nth row populate_db
        # created goes with the Nth non-subscription row of the input
        # So suppress the duplicates when using sqlite.
        if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
            tmp_message = simplejson.loads(old_message_json)
            tmp_message['id'] = '1'
            duplicate_suppression_key = simplejson.dumps(tmp_message)
            if duplicate_suppression_key in duplicate_suppression_hash:
                return
            duplicate_suppression_hash[duplicate_suppression_key] = True

        old_message = simplejson.loads(old_message_json)
        message_type = old_message["type"]

        # Lower case emails and domains; it will screw up
        # deduplication if we don't
        def fix_email(email):
            return email.strip().lower()

        if message_type in ["stream", "huddle", "personal"]:
            old_message["sender_email"] = fix_email(old_message["sender_email"])
            # Fix the length on too-long messages before we start processing them
            if len(old_message["content"]) > MAX_MESSAGE_LENGTH:
                old_message["content"] = "[ This message was deleted because it was too long ]"
        if message_type in ["subscription_added", "subscription_removed"]:
            old_message["domain"] = old_message["domain"].lower()
            old_message["user"] = fix_email(old_message["user"])
        elif message_type == "subscription_property":
            old_message["user"] = fix_email(old_message["user"])
        elif message_type.startswith("user_"):
            old_message["user"] = fix_email(old_message["user"])
        elif message_type.startswith("enable_"):
            old_message["user"] = fix_email(old_message["user"])

        if message_type == 'personal':
            old_message["recipient"][0]["email"] = fix_email(old_message["recipient"][0]["email"])
        elif message_type == "huddle":
            for i in xrange(len(old_message["recipient"])):
                old_message["recipient"][i]["email"] = fix_email(old_message["recipient"][i]["email"])

        old_messages.append(old_message)

        if message_type in ["subscription_added", "subscription_removed"]:
            stream_name = old_message["name"].strip()
            canon_stream_name = stream_name.lower()
            if canon_stream_name not in stream_dict:
                stream_dict[(old_message["domain"], canon_stream_name)] = \
                    (old_message["domain"], stream_name)
        elif message_type == "user_created":
            user_set.add((old_message["user"], old_message["full_name"], old_message["short_name"], False))
        elif message_type == "realm_created":
            realm_set.add(old_message["domain"])

        if message_type not in ["stream", "huddle", "personal"]:
            return

        sender_email = old_message["sender_email"]

        domain = sender_email.split('@')[1]
        realm_set.add(domain)

        if old_message["sender_email"] not in email_set:
            user_set.add((old_message["sender_email"],
                          old_message["sender_full_name"],
                          old_message["sender_short_name"],
                          False))

        if 'sending_client' in old_message:
            client_set.add(old_message['sending_client'])

        if message_type == 'stream':
            stream_name = old_message["recipient"].strip()
            canon_stream_name = stream_name.lower()
            if canon_stream_name not in stream_dict:
                stream_dict[(domain, canon_stream_name)] = (domain, stream_name)
        elif message_type == 'personal':
            u = old_message["recipient"][0]
            if u["email"] not in email_set:
                user_set.add((u["email"], u["full_name"], u["short_name"], False))
                email_set.add(u["email"])
        elif message_type == 'huddle':
            for u in old_message["recipient"]:
                user_set.add((u["email"], u["full_name"], u["short_name"], False))
                if u["email"] not in email_set:
                    user_set.add((u["email"], u["full_name"], u["short_name"], False))
                    email_set.add(u["email"])
            huddle_user_set.add(tuple(sorted(set(u["email"] for u in old_message["recipient"]))))
        else:
            raise ValueError('Bad message type')

    with file(settings.MESSAGE_LOG, "r") as message_log:
        for line in message_log.readlines():
            process_line(line)

    stream_recipients = {}
    user_recipients = {}
    huddle_recipients = {}

    # Then, create the objects our messages need.
    print datetime.datetime.now(), "Creating realms..."
    bulk_create_realms(realm_set)

    realms = {}
    for realm in Realm.objects.all():
        realms[realm.domain] = realm

    print datetime.datetime.now(), "Creating clients..."
    bulk_create_clients(client_set)

    clients = {}
    for client in Client.objects.all():
        clients[client.name] = client

    print datetime.datetime.now(), "Creating streams..."
    bulk_create_streams(realms, stream_dict.values())

    streams = {}
    for stream in Stream.objects.all():
        streams[stream.id] = stream
    for recipient in Recipient.objects.filter(type=Recipient.STREAM):
        stream_recipients[(streams[recipient.type_id].realm_id,
                           streams[recipient.type_id].name.lower())] = recipient

    print datetime.datetime.now(), "Creating users..."
    bulk_create_users(realms, user_set)

    users = {}
    users_by_id = {}
    for user_profile in UserProfile.objects.select_related().all():
        users[user_profile.user.email] = user_profile
        users_by_id[user_profile.id] = user_profile
    for recipient in Recipient.objects.filter(type=Recipient.PERSONAL):
        user_recipients[users_by_id[recipient.type_id].user.email] = recipient

    print datetime.datetime.now(), "Creating huddles..."
    bulk_create_huddles(users, huddle_user_set)

    huddles_by_id = {}
    for huddle in Huddle.objects.all():
        huddles_by_id[huddle.id] = huddle
    for recipient in Recipient.objects.filter(type=Recipient.HUDDLE):
        huddle_recipients[huddles_by_id[recipient.type_id].huddle_hash] = recipient

    # TODO: Add a special entry type in the log that is a subscription
    # change and import those as we go to make subscription changes
    # take effect!
    print datetime.datetime.now(), "Importing subscriptions..."
    subscribers = {}
    for s in Subscription.objects.select_related().all():
        if s.active:
            subscribers.setdefault(s.recipient.id, set()).add(s.user_profile.id)

    # Then create all the messages, without talking to the DB!
    print datetime.datetime.now(), "Importing messages, part 1..."
    first_message_id = None
    if Message.objects.exists():
        first_message_id = Message.objects.all().order_by("-id")[0].id + 1

    messages_to_create = []
    for idx, old_message in enumerate(old_messages):
        message_type = old_message["type"]
        if message_type not in ["stream", "huddle", "personal"]:
            continue

        message = Message()

        sender_email = old_message["sender_email"]
        domain = sender_email.split('@')[1]
        realm = realms[domain]

        message.sender = users[sender_email]
        type_hash = {"stream": Recipient.STREAM,
                     "huddle": Recipient.HUDDLE,
                     "personal": Recipient.PERSONAL}

        if 'sending_client' in old_message:
            message.sending_client = clients[old_message['sending_client']]
        elif sender_email in ["othello@humbughq.com", "iago@humbughq.com", "prospero@humbughq.com",
                              "cordelia@humbughq.com", "hamlet@humbughq.com"]:
            message.sending_client = clients['populate_db']
        elif realm.domain == "humbughq.com":
            message.sending_client = clients["website"]
        elif realm.domain == "mit.edu":
            message.sending_client = clients['zephyr_mirror']
        else:
            message.sending_client = clients['populate_db']

        message.type = type_hash[message_type]
        message.content = old_message["content"]
        message.subject = old_message["subject"]
        message.pub_date = timestamp_to_datetime(old_message["timestamp"])

        if message.type == Recipient.PERSONAL:
            message.recipient = user_recipients[old_message["recipient"][0]["email"]]
        elif message.type == Recipient.STREAM:
            message.recipient = stream_recipients[(realm.id,
                                                   old_message["recipient"].lower())]
        elif message.type == Recipient.HUDDLE:
            huddle_hash = get_huddle_hash([users[u["email"]].id
                                           for u in old_message["recipient"]])
            message.recipient = huddle_recipients[huddle_hash]
        else:
            raise ValueError('Bad message type')
        messages_to_create.append(message)

    print datetime.datetime.now(), "Importing messages, part 2..."
    batch_bulk_create(Message, messages_to_create, batch_size=100)
    messages_to_create = []

    # Finally, create all the UserMessage objects
    print datetime.datetime.now(), "Importing usermessages, part 1..."
    personal_recipients = {}
    for r in Recipient.objects.filter(type = Recipient.PERSONAL):
        personal_recipients[r.id] = True

    all_messages = Message.objects.all()
    user_messages_to_create = []

    messages_by_id = {}
    for message in all_messages:
        messages_by_id[message.id] = message

    if first_message_id is None:
        first_message_id = min(messages_by_id.keys())

    tot_user_messages = 0
    pending_subs = {}
    current_message_id = first_message_id
    pending_colors = {}
    for old_message in old_messages:
        message_type = old_message["type"]
        if message_type == 'subscription_added':
            stream_key = (realms[old_message["domain"]].id, old_message["name"].strip().lower())
            subscribers.setdefault(stream_recipients[stream_key].id,
                                   set()).add(users[old_message["user"]].id)
            pending_subs[(stream_recipients[stream_key].id,
                          users[old_message["user"]].id)] = True
            continue
        elif message_type == "subscription_removed":
            stream_key = (realms[old_message["domain"]].id, old_message["name"].strip().lower())
            user_id = users[old_message["user"]].id
            subscribers.setdefault(stream_recipients[stream_key].id, set())
            try:
                subscribers[stream_recipients[stream_key].id].remove(user_id)
            except KeyError:
                print "Error unsubscribing %s from %s: not subscribed" % (
                    old_message["user"], old_message["name"])
            pending_subs[(stream_recipients[stream_key].id,
                          users[old_message["user"]].id)] = False
            continue
        elif message_type == "user_activated" or message_type == "user_created":
            # These are rare, so just handle them the slow way
            user = User.objects.get(email=old_message["user"])
            join_date = timestamp_to_datetime(old_message['timestamp'])
            do_activate_user(user, log=False, join_date=join_date)
            # Update the cache of users to show this user as activated
            users_by_id[user.userprofile.id] = UserProfile.objects.get(user=user)
            users[user.email] = user.userprofile
            continue
        elif message_type == "user_change_password":
            # Just handle these the slow way
            user = User.objects.get(email=old_message["user"])
            user.password = old_message["pwhash"]
            user.save()
            continue
        elif message_type == "user_change_full_name":
            # Just handle these the slow way
            user_profile = UserProfile.objects.get(user__email=old_message["user"])
            user_profile.full_name = old_message["full_name"]
            user_profile.save()
            continue
        elif message_type == "enable_desktop_notifications_changed":
            # Just handle these the slow way
            user_profile = UserProfile.objects.get(user__email=old_message["user"])
            user_profile.enable_desktop_notifications = (old_message["enable_desktop_notifications"] != "false")
            user_profile.save()
            continue
        elif message_type == "default_streams":
            set_default_streams(Realm.objects.get(domain=old_message["domain"]),
                                old_message["streams"])
            continue
        elif message_type == "subscription_property":
            property_name = old_message.get("property")
            if property_name == "stream_color":
                pending_colors[(old_message["user"],
                                old_message["stream_name"].lower())] = old_message["color"]
            else:
                raise RuntimeError("Unknown property %s" % (property_name,))
            continue
        elif message_type == "realm_created":
            continue
        if message_type not in ["stream", "huddle", "personal"]:
            raise RuntimeError("Unexpected message type %s" % (message_type,))

        message = messages_by_id[current_message_id]
        current_message_id += 1

        if message.recipient_id not in subscribers:
            # Nobody received this message -- probably due to our
            # subscriptions being out-of-date.
            continue

        recipient_user_ids = set()
        for user_profile_id in subscribers[message.recipient_id]:
            recipient_user_ids.add(user_profile_id)
        if message.recipient_id in personal_recipients:
            # Include the sender in huddle recipients
            recipient_user_ids.add(message.sender_id)

        for user_profile_id in recipient_user_ids:
            if users_by_id[user_profile_id].user.is_active:
                um = UserMessage(user_profile_id=user_profile_id,
                                 message=message)
                user_messages_to_create.append(um)

        if len(user_messages_to_create) > 100000:
            tot_user_messages += len(user_messages_to_create)
            batch_bulk_create(UserMessage, user_messages_to_create)
            user_messages_to_create = []

    print datetime.datetime.now(), "Importing usermessages, part 2..."
    tot_user_messages += len(user_messages_to_create)
    batch_bulk_create(UserMessage, user_messages_to_create)

    print datetime.datetime.now(), "Finalizing subscriptions..."
    current_subs = {}
    current_subs_obj = {}
    for s in Subscription.objects.select_related().all():
        current_subs[(s.recipient_id, s.user_profile_id)] = s.active
        current_subs_obj[(s.recipient_id, s.user_profile_id)] = s

    subscriptions_to_add = []
    subscriptions_to_change = []
    for pending_sub in pending_subs.keys():
        (recipient_id, user_profile_id) = pending_sub
        current_state = current_subs.get(pending_sub)
        if pending_subs[pending_sub] == current_state:
            # Already correct in the database
            continue
        elif current_state is not None:
            subscriptions_to_change.append((pending_sub, pending_subs[pending_sub]))
            continue

        s = Subscription(recipient_id=recipient_id,
                         user_profile_id=user_profile_id,
                         active=pending_subs[pending_sub])
        subscriptions_to_add.append(s)
    batch_bulk_create(Subscription, subscriptions_to_add)
    with transaction.commit_on_success():
        for (sub, active) in subscriptions_to_change:
            current_subs_obj[sub].active = active
            current_subs_obj[sub].save()

    subs = {}
    for sub in Subscription.objects.all():
        subs[(sub.user_profile_id, sub.recipient_id)] = sub

    colors_to_change = []
    for key in pending_colors.keys():
        (email, stream_name) = key
        color = pending_colors[key]
        user_profile = users[email]
        domain = email.split("@")[1]
        realm = realms[domain]
        recipient = stream_recipients[(realm.id, stream_name)]
        subscription = subs[(user_profile.id, recipient.id)]
        colors_to_change.append(StreamColor(subscription=subscription,
                                            color=color))
    batch_bulk_create(StreamColor, colors_to_change)

    print datetime.datetime.now(), "Finished importing %s messages (%s usermessages)" % \
        (len(all_messages), tot_user_messages)

    site = Site.objects.get_current()
    site.domain = 'humbughq.com'
    site.save()

    print datetime.datetime.now(), "Filling in user pointers..."

    # Set restored pointers to the very latest messages
    with transaction.commit_on_success():
        for user_profile in UserProfile.objects.all():
            try:
                top = UserMessage.objects.filter(
                    user_profile_id=user_profile.id).order_by("-message")[0]
                user_profile.pointer = top.message_id
            except IndexError:
                user_profile.pointer = -1
            user_profile.save()

    print datetime.datetime.now(), "Done replaying old messages"

# Create some test messages, including:
# - multiple streams
# - multiple subjects per stream
# - multiple huddles
# - multiple personals converastions
# - multiple messages per subject
# - both single and multi-line content
def send_messages(data):
    (tot_messages, personals_pairs, options, output) = data
    random.seed(os.getpid())
    # Close the database connection, so that we get a new one that
    # isn't shared with the other threads
    connection.close()
    texts = file("zephyr/management/commands/test_messages.txt", "r").readlines()
    offset = random.randint(0, len(texts))

    recipient_streams = [klass.id for klass in
                         Recipient.objects.filter(type=Recipient.STREAM)]
    recipient_huddles = [h.id for h in Recipient.objects.filter(type=Recipient.HUDDLE)]

    huddle_members = {}
    for h in recipient_huddles:
        huddle_members[h] = [s.user_profile.id for s in
                             Subscription.objects.filter(recipient_id=h)]

    num_messages = 0
    random_max = 1000000
    recipients = {}
    while num_messages < tot_messages:
      with transaction.commit_on_success():
        saved_data = ''
        message = Message()
        message.sending_client = get_client('populate_db')
        length = random.randint(1, 5)
        lines = (t.strip() for t in texts[offset: offset + length])
        message.content = '\n'.join(lines)
        offset += length
        offset = offset % len(texts)

        randkey = random.randint(1, random_max)
        if (num_messages > 0 and
            random.randint(1, random_max) * 100. / random_max < options["stickyness"]):
            # Use an old recipient
            message_type, recipient_id, saved_data = recipients[num_messages - 1]
            if message_type == Recipient.PERSONAL:
                personals_pair = saved_data
                random.shuffle(personals_pair)
            elif message_type == Recipient.STREAM:
                message.subject = saved_data
                message.recipient = get_recipient_by_id(recipient_id)
            elif message_type == Recipient.HUDDLE:
                message.recipient = get_recipient_by_id(recipient_id)
        elif (randkey <= random_max * options["percent_huddles"] / 100.):
            message_type = Recipient.HUDDLE
            message.recipient = get_recipient_by_id(random.choice(recipient_huddles))
        elif (randkey <= random_max * (options["percent_huddles"] + options["percent_personals"]) / 100.):
            message_type = Recipient.PERSONAL
            personals_pair = random.choice(personals_pairs)
            random.shuffle(personals_pair)
        elif (randkey <= random_max * 1.0):
            message_type = Recipient.STREAM
            message.recipient = get_recipient_by_id(random.choice(recipient_streams))

        if message_type == Recipient.HUDDLE:
            sender_id = random.choice(huddle_members[message.recipient.id])
            message.sender = get_user_profile_by_id(sender_id)
        elif message_type == Recipient.PERSONAL:
            message.recipient = Recipient.objects.get(type=Recipient.PERSONAL,
                                                         type_id=personals_pair[0])
            message.sender = get_user_profile_by_id(personals_pair[1])
            saved_data = personals_pair
        elif message_type == Recipient.STREAM:
            stream = Stream.objects.get(id=message.recipient.type_id)
            # Pick a random subscriber to the stream
            message.sender = random.choice(Subscription.objects.filter(
                    recipient=message.recipient)).user_profile
            message.subject = stream.name + str(random.randint(1, 3))
            saved_data = message.subject

        message.pub_date = now()
        do_send_message(message)

        recipients[num_messages] = [message_type, message.recipient.id, saved_data]
        num_messages += 1
    connection.close()
    return tot_messages

import os
import sys
import datetime
import tempfile
import traceback
import simplejson
from os import path

from django.core.management.base import BaseCommand
from zephyr.retention_policy     import should_expunge_from_log

now = datetime.datetime.now()

def copy_retained_messages(infile, outfile):
    """Copy messages from infile to outfile which should be retained
       according to policy."""
    for ln in infile:
        msg = simplejson.loads(ln)
        if not should_expunge_from_log(msg, now):
            outfile.write(ln)

def expunge(filename):
    """Expunge entries from the named log file, in place."""

    # We don't use the 'with' statement for tmpfile because we need to
    # either move it or delete it, depending on success or failure.
    #
    # We create it in the same directory as infile for two reasons:
    #
    #   - It makes it more likely we will notice leftover temp files
    #
    #   - It ensures that they are on the same filesystem, so we can
    #     use atomic os.rename().
    #
    tmpfile = tempfile.NamedTemporaryFile(
        mode   = 'wb',
        dir    = path.dirname(filename),
        delete = False)

    try:
        try:
            with open(filename, 'rb') as infile:
                copy_retained_messages(infile, tmpfile)
        finally:
            tmpfile.close()

        os.rename(tmpfile.name, filename)
    except:
        os.unlink(tmpfile.name)
        raise

class Command(BaseCommand):
    help = ('Expunge old entries from one or more log files, '
            + 'according to the retention policy.')
    args = '<log file> <log file> ...'

    def handle(self, *args, **kwargs):
        if len(args) == 0:
            print >>sys.stderr, 'WARNING: No log files specified; doing nothing.'

        for infile in args:
            try:
                expunge(infile)
            except:
                print >>sys.stderr, 'WARNING: Could not expunge from', infile
                traceback.print_exc()

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import Realm, UserProfile, UserActivity, get_client
import simplejson
from zephyr.lib.time import datetime_to_timestamp, timestamp_to_datetime

def dump():
    pointers = []
    for activity in UserActivity.objects.select_related("user_profile__user__email",
                                                        "client__name").all():
        pointers.append((activity.user_profile.user.email, activity.client.name,
                         activity.query, activity.count,
                         datetime_to_timestamp(activity.last_visit)))
    file("dumped-activity", "w").write(simplejson.dumps(pointers) + "\n")

def restore(change):
    for (email, client_name, query, count, timestamp) in simplejson.loads(file("dumped-activity").read()):
        user_profile = UserProfile.objects.get(user__email=email)
        client = get_client(client_name)
        last_visit = timestamp_to_datetime(timestamp)
        print "%s: activity for %s,%s" % (email, client_name, query)
        if change:
            activity, created = UserActivity.objects.get_or_create(user_profile=user_profile,
                                                                   query=query, client=client,
                                                                   defaults={"last_visit": last_visit,
                                                                             "count": count})
            if not created:
                activity.count += count
                activity.last_visit = max(last_visit, activity.last_visit)
            activity.save()

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--restore', default=False, action='store_true'),
        make_option('--dry-run', '-n', default=False, action='store_true'),)

    def handle(self, *args, **options):
        if options["restore"]:
            restore(change=not options['dry_run'])
        else:
            dump()

import datetime
import calendar
from django.utils.timezone import utc

def timestamp_to_datetime(timestamp):
    return datetime.datetime.utcfromtimestamp(float(timestamp)).replace(tzinfo=utc)

def datetime_to_timestamp(datetime_object):
    return calendar.timegm(datetime_object.timetuple())

def last_n(n, query_set):
    """Get the last n results from a Django QuerySet, in a semi-efficient way.
       Returns a list."""

    # We don't use reversed() because we would get a generator,
    # which causes bool(last_n(...)) to be True always.

    xs = list(query_set.reverse()[:n])
    xs.reverse()
    return xs

from django.conf import settings

import hashlib
import base64

def initial_password(email):

    """Given an email address, returns the initial password for that account, as
       created by populate_db."""

    digest = hashlib.sha256(settings.INITIAL_PASSWORD_SALT + email).digest()
    return base64.b64encode(digest)[:16]

def initial_api_key(email):

    """Given an email address, returns the initial API key for that account"""

    digest = hashlib.sha256(settings.INITIAL_API_KEY_SALT + email).digest()
    return base64.b16encode(digest)[:32].lower()

from functools import wraps

import django.core.cache

def cache_with_key(keyfunc):
    """Decorator which applies Django caching to a function.

       Decorator argument is a function which computes a cache key
       from the original function's arguments.  You are responsible
       for avoiding collisions with other uses of this decorator or
       other uses of caching."""

    def decorator(func):
        djcache = django.core.cache.cache

        @wraps(func)
        def func_with_caching(*args, **kwargs):
            key = keyfunc(*args, **kwargs)
            val = djcache.get(key)

            # Values are singleton tuples so that we can distinguish
            # a result of None from a missing key.
            if val is not None:
                return val[0]

            val = func(*args, **kwargs)
            djcache.set(key, (val,))
            return val

        return func_with_caching

    return decorator

def cache(func):
    """Decorator which applies Django caching to a function.

       Uses a key based on the function's name, filename, and
       the repr() of its arguments."""

    func_uniqifier = '%s-%s' % (func.func_code.co_filename, func.func_name)

    @wraps(func)
    def keyfunc(*args, **kwargs):
        # Django complains about spaces because memcached rejects them
        key = func_uniqifier + repr((args, kwargs))
        return key.replace('-','--').replace(' ','-s')

    return cache_with_key(keyfunc)(func)


from django.http import HttpResponse
import simplejson

def json_response(res_type="success", msg="", data={}, status=200):
    content = {"result": res_type, "msg": msg}
    content.update(data)
    return HttpResponse(content=simplejson.dumps(content),
                        mimetype='application/json', status=status)

def json_success(data={}):
    return json_response(data=data)

def json_error(msg, data={}, status=400):
    return json_response(res_type="error", msg=msg, data=data, status=status)

import hashlib

def gravatar_hash(email):
    """Compute the Gravatar hash for an email address."""
    return hashlib.md5(email.lower()).hexdigest()

"""
Context managers, i.e. things you can use with the 'with' statement.
"""

import fcntl
from os import path
from contextlib import contextmanager

@contextmanager
def flock(lockfile, shared=False):
    """Lock a file object using flock(2) for the duration of a 'with' statement.

       If shared is True, use a LOCK_SH lock, otherwise LOCK_EX."""

    fcntl.flock(lockfile, fcntl.LOCK_SH if shared else fcntl.LOCK_EX)
    try:
        yield
    finally:
        fcntl.flock(lockfile, fcntl.LOCK_UN)

@contextmanager
def lockfile(filename, shared=False):
    """Lock a file using flock(2) for the duration of a 'with' statement.

       If shared is True, use a LOCK_SH lock, otherwise LOCK_EX.

       The file is given by name and will be created if it does not exist."""

    if not path.exists(filename):
        with open(filename, 'w') as lock:
            lock.write('0')

    # TODO: Can we just open the file for writing, and skip the above check?
    with open(filename, 'r') as lock:
        with flock(lock, shared=shared):
            yield

from django.conf import settings
# batch_bulk_create should become obsolete with Django 1.5, when the
# Django bulk_create method accepts a batch_size directly.
def batch_bulk_create(cls, cls_list, batch_size=150):
    if "sqlite" not in settings.DATABASES["default"]["ENGINE"]:
        # We don't need a low batch size with mysql, but we do need
        # one to avoid "MySQL Server has gone away" errors
        batch_size = 10000
    while len(cls_list) > 0:
        current_batch = cls_list[0:batch_size]
        cls.objects.bulk_create(current_batch)
        cls_list = cls_list[batch_size:]

import os
import pty
import sys
import errno

def run_parallel(job, data, threads=6):
    pids = {}

    def wait_for_one():
        while True:
            try:
                (pid, status) = os.wait()
                return status, pids.pop(pid)
            except KeyError:
                pass

    for item in data:
        pid = os.fork()
        if pid == 0:
            sys.stdin.close()
            try:
                os.close(pty.STDIN_FILENO)
            except OSError, e:
                if e.errno != errno.EBADF:
                    raise
            sys.stdin = open("/dev/null", "r")
            os._exit(job(item))

        pids[pid] = item
        threads = threads - 1

        if threads == 0:
            (status, item) = wait_for_one()
            threads += 1
            yield (status, item)
            if status != 0:
                # Stop if any error occurred
                break

    while True:
        try:
            (status, item) = wait_for_one()
            yield (status, item)
        except OSError, e:
            if e.errno == errno.ECHILD:
                break
            else:
                raise

if __name__ == "__main__":
    # run some unit tests
    import time
    jobs = [10, 19, 18, 6, 14, 12, 8, 2, 1, 13, 3, 17, 9, 11, 5, 16, 7, 15, 4]
    expected_output = [6, 10, 12, 2, 1, 14, 8, 3, 18, 19, 5, 9, 13, 11, 4, 7, 17, 16, 15]
    def wait_and_print(x):
        time.sleep(x * 0.1)
        return 0

    output = []
    for (status, job) in run_parallel(wait_and_print, jobs):
        output.append(job)
    if output == expected_output:
        print "Successfully passed test!"
    else:
        print "Failed test!"
        print jobs
        print expected_output
        print output


import markdown
import logging
import traceback
import urlparse
import re

from zephyr.lib.avatar  import gravatar_hash
from zephyr.lib.bugdown import codehilite, fenced_code

class Gravatar(markdown.inlinepatterns.Pattern):
    def handleMatch(self, match):
        img = markdown.util.etree.Element('img')
        img.set('class', 'message_body_gravatar img-rounded')
        img.set('src', 'https://secure.gravatar.com/avatar/%s?d=identicon&s=30'
            % (gravatar_hash(match.group('email')),))
        return img

def fixup_link(link):
    """Set certain attributes we want on every link."""
    link.set('target', '_blank')
    link.set('title',  link.get('href'))

class AutoLink(markdown.inlinepatterns.Pattern):
    def handleMatch(self, match):
        url = match.group('url')
        a = markdown.util.etree.Element('a')
        a.set('href', url)
        a.text = url
        fixup_link(a)
        return a

class UListProcessor(markdown.blockprocessors.OListProcessor):
    """ Process unordered list blocks.

        Based on markdown.blockprocessors.UListProcessor, but does not accept
        '+' as a bullet character."""

    TAG = 'ul'
    RE = re.compile(r'^[ ]{0,3}[*-][ ]+(.*)')

# Based on markdown.inlinepatterns.LinkPattern
class LinkPattern(markdown.inlinepatterns.Pattern):
    """ Return a link element from the given match. """
    def handleMatch(self, m):
        el = markdown.util.etree.Element("a")
        el.text = m.group(2)
        href = m.group(9)

        if href:
            if href[0] == "<":
                href = href[1:-1]
            el.set("href", self.sanitize_url(self.unescape(href.strip())))
        else:
            el.set("href", "")

        fixup_link(el)
        return el

    def sanitize_url(self, url):
        """
        Sanitize a url against xss attacks.
        See the docstring on markdown.inlinepatterns.LinkPattern.sanitize_url.
        """
        try:
            parts = urlparse.urlparse(url.replace(' ', '%20'))
            scheme, netloc, path, params, query, fragment = parts
        except ValueError:
            # Bad url - so bad it couldn't be parsed.
            return ''

        # Humbug modification: If scheme is not specified, assume http://
        # It's unlikely that users want relative links within humbughq.com.
        # We re-enter sanitize_url because netloc etc. need to be re-parsed.
        if not scheme:
            return self.sanitize_url('http://' + url)

        locless_schemes = ['', 'mailto', 'news']
        if netloc == '' and scheme not in locless_schemes:
            # This fails regardless of anything else.
            # Return immediately to save additional proccessing
            return ''

        for part in parts[2:]:
            if ":" in part:
                # Not a safe url
                return ''

        # Url passes all tests. Return url as-is.
        return urlparse.urlunparse(parts)

class Bugdown(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        del md.preprocessors['reference']

        for k in ('image_link', 'image_reference', 'automail',
                  'autolink', 'link', 'reference', 'short_reference',
                  'escape'):
            del md.inlinePatterns[k]

        for k in ('hashheader', 'setextheader', 'olist', 'ulist'):
            del md.parser.blockprocessors[k]

        md.parser.blockprocessors.add('ulist', UListProcessor(md.parser), '>hr')

        md.inlinePatterns.add('gravatar', Gravatar(r'!gravatar\((?P<email>[^)]*)\)'), '_begin')
        md.inlinePatterns.add('link', LinkPattern(markdown.inlinepatterns.LINK_RE, md), '>backtick')

        # A link starts at a word boundary, and ends at space or end-of-input.
        # But any trailing punctuation (other than /) is not included.
        # We accomplish this with a non-greedy match followed by a greedy
        # lookahead assertion.
        #
        # markdown.inlinepatterns.Pattern compiles this with re.UNICODE, which
        # is important because we're using \w.
        link_regex = r'\b(?P<url>https?://[^\s]+?)(?=[^\w/]*(\s|\Z))'
        md.inlinePatterns.add('autolink', AutoLink(link_regex), '>link')

_md_engine = markdown.Markdown(
    safe_mode     = 'escape',
    output_format = 'html',
    extensions    = ['nl2br',
        codehilite.makeExtension(configs=[
            ('force_linenos', False),
            ('guess_lang',    False)]),
        fenced_code.makeExtension(),
        Bugdown()])

# We want to log Markdown parser failures, but shouldn't log the actual input
# message for privacy reasons.  The compromise is to replace all alphanumeric
# characters with 'x'.
#
# We also use repr() to improve reproducibility, and to escape terminal control
# codes, which can do surprisingly nasty things.
_privacy_re = re.compile(r'\w', flags=re.UNICODE)
def _sanitize_for_log(md):
    return repr(_privacy_re.sub('x', md))

def _linkify(match):
    url = match.group('url')
    return ' [%s](%s) ' % (url, url)

def convert(md):
    """Convert Markdown to HTML, with Humbug-specific settings and hacks."""

    # Reset the parser; otherwise it will get slower over time.
    _md_engine.reset()

    try:
        html = _md_engine.convert(md)
    except:
        # FIXME: Do something more reasonable here!
        html = '<p>[Humbug note: Sorry, we could not understand the formatting of your message]</p>'
        logging.getLogger('').error('Exception in Markdown parser: %sInput (sanitized) was: %s'
            % (traceback.format_exc(), _sanitize_for_log(md)))

    return html

#!/usr/bin/python

"""
CodeHilite Extension for Python-Markdown
========================================

Adds code/syntax highlighting to standard Python-Markdown code blocks.

Copyright 2006-2008 [Waylan Limberg](http://achinghead.com/).

Project website: <http://packages.python.org/Markdown/extensions/code_hilite.html>
Contact: markdown@freewisdom.org

License: BSD (see ../LICENSE.md for details)

Dependencies:
* [Python 2.3+](http://python.org/)
* [Markdown 2.0+](http://packages.python.org/Markdown/)
* [Pygments](http://pygments.org/)

"""

import markdown
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
    from pygments.formatters import HtmlFormatter
    pygments = True
except ImportError:
    pygments = False

# ------------------ The Main CodeHilite Class ----------------------
class CodeHilite:
    """
    Determine language of source code, and pass it into the pygments hilighter.

    Basic Usage:
        >>> code = CodeHilite(src = 'some text')
        >>> html = code.hilite()

    * src: Source string or any object with a .readline attribute.

    * force_linenos: (Boolean) Force line numbering 'on' (True) or 'off' (False).
                     If not specified, number lines iff a shebang line is present.

    * guess_lang: (Boolean) Turn language auto-detection 'on' or 'off' (on by default).

    * css_class: Set class name of wrapper div ('codehilite' by default).

    Low Level Usage:
        >>> code = CodeHilite()
        >>> code.src = 'some text' # String or anything with a .readline attr.
        >>> code.linenos = True  # True or False; Turns line numbering on or of.
        >>> html = code.hilite()

    """

    def __init__(self, src=None, force_linenos=None, guess_lang=True,
                css_class="codehilite", lang=None, style='default',
                noclasses=False, tab_length=4):
        self.src = src
        self.lang = lang
        self.linenos = force_linenos
        self.guess_lang = guess_lang
        self.css_class = css_class
        self.style = style
        self.noclasses = noclasses
        self.tab_length = tab_length

    def hilite(self):
        """
        Pass code to the [Pygments](http://pygments.pocoo.org/) highliter with
        optional line numbers. The output should then be styled with css to
        your liking. No styles are applied by default - only styling hooks
        (i.e.: <span class="k">).

        returns : A string of html.

        """

        self.src = self.src.strip('\n')

        if self.lang is None:
            self._getLang()

        if pygments:
            try:
                lexer = get_lexer_by_name(self.lang)
            except ValueError:
                try:
                    if self.guess_lang:
                        lexer = guess_lexer(self.src)
                    else:
                        lexer = TextLexer()
                except ValueError:
                    lexer = TextLexer()
            formatter = HtmlFormatter(linenos=bool(self.linenos),
                                      cssclass=self.css_class,
                                      style=self.style,
                                      noclasses=self.noclasses)
            return highlight(self.src, lexer, formatter)
        else:
            # just escape and build markup usable by JS highlighting libs
            txt = self.src.replace('&', '&amp;')
            txt = txt.replace('<', '&lt;')
            txt = txt.replace('>', '&gt;')
            txt = txt.replace('"', '&quot;')
            classes = []
            if self.lang:
                classes.append('language-%s' % self.lang)
            if self.linenos:
                classes.append('linenums')
            class_str = ''
            if classes:
                class_str = ' class="%s"' % ' '.join(classes) 
            return '<pre class="%s"><code%s>%s</code></pre>\n'% \
                        (self.css_class, class_str, txt)

    def _getLang(self):
        """
        Determines language of a code block from shebang line and whether said
        line should be removed or left in place. If the sheband line contains a
        path (even a single /) then it is assumed to be a real shebang line and
        left alone. However, if no path is given (e.i.: #!python or :::python)
        then it is assumed to be a mock shebang for language identifitation of a
        code fragment and removed from the code block prior to processing for
        code highlighting. When a mock shebang (e.i: #!python) is found, line
        numbering is turned on. When colons are found in place of a shebang
        (e.i.: :::python), line numbering is left in the current state - off
        by default.

        """

        import re

        #split text into lines
        lines = self.src.split("\n")
        #pull first line to examine
        fl = lines.pop(0)

        c = re.compile(r'''
            (?:(?:^::+)|(?P<shebang>^[#]!))	# Shebang or 2 or more colons.
            (?P<path>(?:/\w+)*[/ ])?        # Zero or 1 path
            (?P<lang>[\w+-]*)               # The language
            ''',  re.VERBOSE)
        # search first line for shebang
        m = c.search(fl)
        if m:
            # we have a match
            try:
                self.lang = m.group('lang').lower()
            except IndexError:
                self.lang = None
            if m.group('path'):
                # path exists - restore first line
                lines.insert(0, fl)
            if m.group('shebang') and self.linenos is None:
                # shebang exists - use line numbers
                self.linenos = True
        else:
            # No match
            lines.insert(0, fl)

        self.src = "\n".join(lines).strip("\n")



# ------------------ The Markdown Extension -------------------------------
class HiliteTreeprocessor(markdown.treeprocessors.Treeprocessor):
    """ Hilight source code in code blocks. """

    def run(self, root):
        """ Find code blocks and store in htmlStash. """
        blocks = root.getiterator('pre')
        for block in blocks:
            children = block.getchildren()
            if len(children) == 1 and children[0].tag == 'code':
                code = CodeHilite(children[0].text,
                            force_linenos=self.config['force_linenos'],
                            guess_lang=self.config['guess_lang'],
                            css_class=self.config['css_class'],
                            style=self.config['pygments_style'],
                            noclasses=self.config['noclasses'],
                            tab_length=self.markdown.tab_length)
                placeholder = self.markdown.htmlStash.store(code.hilite(),
                                                            safe=True)
                # Clear codeblock in etree instance
                block.clear()
                # Change to p element which will later
                # be removed when inserting raw html
                block.tag = 'p'
                block.text = placeholder


class CodeHiliteExtension(markdown.Extension):
    """ Add source code hilighting to markdown codeblocks. """

    def __init__(self, configs):
        # define default configs
        self.config = {
            'force_linenos' : [None, "Force line numbers - Default: detect based on shebang"],
            'guess_lang' : [True, "Automatic language detection - Default: True"],
            'css_class' : ["codehilite",
                           "Set class name for wrapper <div> - Default: codehilite"],
            'pygments_style' : ['default', 'Pygments HTML Formatter Style (Colorscheme) - Default: default'],
            'noclasses': [False, 'Use inline styles instead of CSS classes - Default false']
            }

        # Override defaults with user settings
        for key, value in configs:
            # convert strings to booleans
            if value == 'True': value = True
            if value == 'False': value = False
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        """ Add HilitePostprocessor to Markdown instance. """
        hiliter = HiliteTreeprocessor(md)
        hiliter.config = self.getConfigs()
        md.treeprocessors.add("hilite", hiliter, "<inline")

        md.registerExtension(self)


def makeExtension(configs={}):
  return CodeHiliteExtension(configs=configs)


#!/usr/bin/env python

"""
Fenced Code Extension for Python Markdown
=========================================

This extension adds Fenced Code Blocks to Python-Markdown.

    >>> import markdown
    >>> text = '''
    ... A paragraph before a fenced code block:
    ...
    ... ~~~
    ... Fenced code block
    ... ~~~
    ... '''
    >>> html = markdown.markdown(text, extensions=['fenced_code'])
    >>> print html
    <p>A paragraph before a fenced code block:</p>
    <pre><code>Fenced code block
    </code></pre>

Works with safe_mode also (we check this because we are using the HtmlStash):

    >>> print markdown.markdown(text, extensions=['fenced_code'], safe_mode='replace')
    <p>A paragraph before a fenced code block:</p>
    <pre><code>Fenced code block
    </code></pre>

Include tilde's in a code block and wrap with blank lines:

    >>> text = '''
    ... ~~~~~~~~
    ...
    ... ~~~~
    ... ~~~~~~~~'''
    >>> print markdown.markdown(text, extensions=['fenced_code'])
    <pre><code>
    ~~~~
    </code></pre>

Language tags:

    >>> text = '''
    ... ~~~~{.python}
    ... # Some python code
    ... ~~~~'''
    >>> print markdown.markdown(text, extensions=['fenced_code'])
    <pre><code class="python"># Some python code
    </code></pre>

Optionally backticks instead of tildes as per how github's code block markdown is identified:

    >>> text = '''
    ... `````
    ... # Arbitrary code
    ... ~~~~~ # these tildes will not close the block
    ... `````'''
    >>> print markdown.markdown(text, extensions=['fenced_code'])
    <pre><code># Arbitrary code
    ~~~~~ # these tildes will not close the block
    </code></pre>

Copyright 2007-2008 [Waylan Limberg](http://achinghead.com/).

Project website: <http://packages.python.org/Markdown/extensions/fenced_code_blocks.html>
Contact: markdown@freewisdom.org

License: BSD (see ../docs/LICENSE for details)

Dependencies:
* [Python 2.4+](http://python.org)
* [Markdown 2.0+](http://packages.python.org/Markdown/)
* [Pygments (optional)](http://pygments.org)

"""

import re
import markdown
from zephyr.lib.bugdown.codehilite import CodeHilite, CodeHiliteExtension

# Global vars
FENCED_BLOCK_RE = re.compile( \
    r'(?P<fence>^(?:~{3,}|`{3,}))[ ]*(\{?\.?(?P<lang>[a-zA-Z0-9_+-]*)\}?)?[ ]*\n(?P<code>.*?)(?<=\n)(?P=fence)[ ]*$',
    re.MULTILINE|re.DOTALL
    )
CODE_WRAP = '<pre><code%s>%s</code></pre>'
LANG_TAG = ' class="%s"'

class FencedCodeExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        """ Add FencedBlockPreprocessor to the Markdown instance. """
        md.registerExtension(self)

        md.preprocessors.add('fenced_code_block',
                                 FencedBlockPreprocessor(md),
                                 "_begin")


class FencedBlockPreprocessor(markdown.preprocessors.Preprocessor):

    def __init__(self, md):
        markdown.preprocessors.Preprocessor.__init__(self, md)

        self.checked_for_codehilite = False
        self.codehilite_conf = {}

    def run(self, lines):
        """ Match and store Fenced Code Blocks in the HtmlStash. """

        # Check for code hilite extension
        if not self.checked_for_codehilite:
            for ext in self.markdown.registeredExtensions:
                if isinstance(ext, CodeHiliteExtension):
                    self.codehilite_conf = ext.config
                    break

            self.checked_for_codehilite = True

        text = "\n".join(lines)
        while 1:
            m = FENCED_BLOCK_RE.search(text)
            if m:
                lang = ''
                if m.group('lang'):
                    lang = LANG_TAG % m.group('lang')

                # If config is not empty, then the codehighlite extension
                # is enabled, so we call it to highlite the code
                if self.codehilite_conf:
                    highliter = CodeHilite(m.group('code'),
                            force_linenos=self.codehilite_conf['force_linenos'][0],
                            guess_lang=self.codehilite_conf['guess_lang'][0],
                            css_class=self.codehilite_conf['css_class'][0],
                            style=self.codehilite_conf['pygments_style'][0],
                            lang=(m.group('lang') or None),
                            noclasses=self.codehilite_conf['noclasses'][0])

                    code = highliter.hilite()
                else:
                    code = CODE_WRAP % (lang, self._escape(m.group('code')))

                placeholder = self.markdown.htmlStash.store(code, safe=True)
                text = '%s\n%s\n%s'% (text[:m.start()], placeholder, text[m.end():])
            else:
                break
        return text.split("\n")

    def _escape(self, txt):
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt


def makeExtension(configs=None):
    return FencedCodeExtension(configs=configs)


if __name__ == "__main__":
    import doctest
    doctest.testmod()


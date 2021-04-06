#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":

    if "--no-traceback" not in sys.argv and len(sys.argv) > 1:
        sys.argv.append("--traceback")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "humbug.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


from zephyr.models import UserProfile, get_user_profile_by_id, \
    get_user_profile_by_email

from openid.consumer.consumer import SUCCESS

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
            user_profile = get_user_profile_by_email(username)
            if user_profile.check_password(password):
                return user_profile
        except UserProfile.DoesNotExist:
            return None

    def get_user(self, user_profile_id):
        """ Get a UserProfile object from the user_profile_id. """
        try:
            return get_user_profile_by_id(user_profile_id)
        except UserProfile.DoesNotExist:
            return None

# Adapted from http://djangosnippets.org/snippets/2183/ by user Hangya (September 1, 2010)

class GoogleBackend(object):
    def authenticate(self, openid_response):
        if openid_response is None:
            return None
        if openid_response.status != SUCCESS:
            return None

        google_email = openid_response.getSigned('http://openid.net/srv/ax/1.0', 'value.email')

        try:
            user_profile = get_user_profile_by_email(google_email)
        except UserProfile.DoesNotExist:
            # create a new user, or send a message to admins, etc.
            return None

        return user_profile

    def get_user(self, user_profile_id):
        """ Get a UserProfile object from the user_profile_id. """
        try:
            return get_user_profile_by_id(user_profile_id)
        except UserProfile.DoesNotExist:
            return None

# Django settings for humbug project.
import os
import platform
import time
import re

from zephyr.openid import openid_failure_handler

SERVER_GENERATION = int(time.time())

DEPLOYED = (('zulip.net' in platform.node())
            or os.path.exists('/etc/humbug-server'))
STAGING_DEPLOYED = (platform.node() == 'staging.zulip.net')
TESTING_DEPLOYED = not not re.match(r'^test', platform.node())

# Uncomment end of next line to test JS/CSS minification.
DEBUG = not DEPLOYED # and platform.node() != 'your-machine'
TEMPLATE_DEBUG = DEBUG
TEST_SUITE = False

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)
if DEPLOYED and not TESTING_DEPLOYED:
    # The IP addresses are for app.zulip.{com,net} and staging.zulip.{com,net}
    ALLOWED_HOSTS = ['localhost', '.humbughq.com', '54.214.48.144', '54.213.44.54',
                     '54.213.41.54', '54.213.44.58', '54.213.44.73',
                     '54.245.120.64', '54.213.44.83', '.zulip.com', '.zulip.net']
elif TESTING_DEPLOYED:
    # Allow any hosts for our test instances, to reduce 500 spam
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['localhost']

ADMINS = (
    ('Zulip Error Reports', 'errors@zulip.com'),
)

MANAGERS = ADMINS

DATABASES = {"default": {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'humbug',
    'USER': 'humbug',
    'PASSWORD': '', # Authentication done via certificates
    'HOST': 'postgres.humbughq.com',
    'SCHEMA': 'humbug',
    'OPTIONS': {
        'sslmode': 'verify-full',
        },
    },
}

if not DEPLOYED:
    DATABASES["default"].update({
            'PASSWORD': 'xxxxxxxxxxxx',
            'HOST': 'localhost',
            'OPTIONS': {}
            })
    INTERNAL_HUMBUG_USERS = []

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
# We set this site's domain to 'zulip.com' in populate_db.
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

DEPLOY_ROOT = os.path.join(os.path.realpath(os.path.dirname(__file__)), '..')
TEMPLATE_DIRS = ( os.path.join(DEPLOY_ROOT, 'templates'), )

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# A fixed salt used for hashing in certain places, e.g. email-based
# username generation.
HASH_SALT = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Use this salt to hash a user's email into a filename for their user-uploaded
# avatar.  If this salt is discovered, attackers will only be able to determine
# that the owner of an email account has uploaded an avatar to Humbug, which isn't
# the end of the world.  Don't use the salt where there is more security exposure.
AVATAR_SALT = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

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

# Used just for generating initial passwords (only used in testing environments).
INITIAL_PASSWORD_SALT = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# A shared secret, used to authenticate different parts of the app to each other.
# FIXME: store this password more securely
SHARED_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Base URL of the Tornado server
# We set it to None when running backend tests or populate_db.
# We override the port number when running frontend tests.
TORNADO_SERVER = 'http://localhost:9993'
RUNNING_INSIDE_TORNADO = False

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
    'zephyr.middleware.RateLimitMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

AUTHENTICATION_BACKENDS = ('humbug.backends.EmailAuthBackend',
                           'humbug.backends.GoogleBackend',
                           'guardian.backends.ObjectPermissionBackend')
ANONYMOUS_USER_ID = None

AUTH_USER_MODEL = "zephyr.UserProfile"

TEST_RUNNER = 'zephyr.tests.Runner'

ROOT_URLCONF = 'humbug.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'humbug.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'humbug.authhack',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'south',
    'django_openid_auth',
    'confirmation',
    'guardian',
    'pipeline',
    'zephyr',
)

LOCAL_STATSD = (False)
USING_STATSD = (DEPLOYED and not TESTING_DEPLOYED) or LOCAL_STATSD

if USING_STATSD:
    if LOCAL_STATSD:
        STATSD_HOST = 'localhost'
    else:
        STATSD_HOST = '10.252.2.167'

    INSTALLED_APPS = ('django_statsd',) + INSTALLED_APPS
    STATSD_PORT = 8125
    STATSD_CLIENT = 'django_statsd.clients.normal'

    if STAGING_DEPLOYED:
        STATSD_PREFIX = 'staging'
    elif DEPLOYED:
        STATSD_PREFIX = 'app'
    else:
        STATSD_PREFIX = 'user'

RATE_LIMITING = True
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

RATE_LIMITING_RULES = [
    (60, 100),     # 100 requests max every minute
    ]

# Static files and minification

STATIC_URL = '/static/'

# HumbugStorage is a modified version of PipelineCachedStorage,
# and, like that class, it inserts a file hash into filenames
# to prevent the browser from using stale files from cache.
#
# Unlike PipelineStorage, it requires the files to exist in
# STATIC_ROOT even for dev servers.  So we only use
# HumbugStorage when not DEBUG.

# This is the default behavior from Pipeline, but we set it
# here so that urls.py can read it.
PIPELINE = not DEBUG

if DEBUG:
    STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'
    STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    )
    if PIPELINE:
        STATIC_ROOT = 'prod-static/serve'
    else:
        STATIC_ROOT = 'static/'
else:
    STATICFILES_STORAGE = 'zephyr.storage.HumbugStorage'
    STATICFILES_FINDERS = (
        'zephyr.finders.HumbugFinder',
    )
    if DEPLOYED:
        STATIC_ROOT = '/home/humbug/prod-static'
    else:
        STATIC_ROOT = 'prod-static/serve'

STATICFILES_DIRS = ['static/']
STATIC_HEADER_FILE = 'zephyr/static_header.txt'

# To use minified files in dev, set PIPELINE = True.  For the full
# cache-busting behavior, you must also set DEBUG = False.
#
# You will need to run ./tools/update-prod-static after changing
# static files.

PIPELINE_CSS = {
    'activity': {
        'source_filenames': ('styles/activity.css',),
        'output_filename':  'min/activity.css'
    },
    'portico': {
        'source_filenames': (
            'third/zocial/zocial.css',
            'styles/portico.css',
            'styles/pygments.css',
            'styles/thirdparty-fonts.css',
            'styles/fonts.css',
        ),
        'output_filename': 'min/portico.css'
    },
    # Two versions of the app CSS exist because of QTBUG-3467
    'app-fontcompat': {
        'source_filenames': (
            'third/bootstrap-notify/css/bootstrap-notify.css',
            'third/spectrum/spectrum.css',
            'styles/zulip.css',
            'styles/pygments.css',
            'styles/thirdparty-fonts.css',
            # We don't want fonts.css on QtWebKit, so its omitted here
        ),
        'output_filename': 'min/app-fontcompat.css'
    },
    'app': {
        'source_filenames': (
            'third/bootstrap-notify/css/bootstrap-notify.css',
            'third/spectrum/spectrum.css',
            'styles/zulip.css',
            'styles/pygments.css',
            'styles/thirdparty-fonts.css',
            'styles/fonts.css',
        ),
        'output_filename': 'min/app.css'
    },
    'common': {
        'source_filenames': (
            'third/bootstrap/css/bootstrap.css',
            'third/bootstrap/css/bootstrap-responsive.css',
        ),
        'output_filename': 'min/common.css'
    },
}

JS_SPECS = {
    'common': {
        'source_filenames': (
            'third/jquery/jquery-1.7.2.js',
            'js/blueslip.js',
            'third/bootstrap/js/bootstrap.js',
            'js/common.js',
            'third/underscore/underscore.js',
            ),
        'output_filename':  'min/common.js'
    },
    'landing-page': {
        'source_filenames': (
            'third/jquery-form/jquery.form.js',
            'js/landing-page.js',
            ),
        'output_filename':  'min/landing-page.js'
    },
    'signup': {
        'source_filenames': (
            'js/signup.js',
            'third/jquery-validate/jquery.validate.js',
            ),
        'output_filename':  'min/signup.js'
    },
    'initial_invite': {
        'source_filenames': (
            'third/jquery-validate/jquery.validate.js',
            'js/initial_invite.js',
            ),
        'output_filename':  'min/initial_invite.js'
    },
    'api': {
        'source_filenames': ('js/api.js',),
        'output_filename':  'min/api.js'
    },
    'app_debug': {
        'source_filenames': ('js/debug.js',),
        'output_filename':  'min/app_debug.js'
    },
    'app': {
        'source_filenames': [
            'third/bootstrap-notify/js/bootstrap-notify.js',
            'third/html5-formdata/formdata.js',
            'third/jquery-validate/jquery.validate.js',
            'third/jquery-form/jquery.form.js',
            'third/jquery-highlight/jquery.highlight.js',
            'third/jquery-filedrop/jquery.filedrop.js',
            'third/jquery-caret/jquery.caret.1.02.js',
            'third/xdate/xdate.dev.js',
            'third/spin/spin.js',
            'third/jquery-mousewheel/jquery.mousewheel.js',
            'third/jquery-throttle-debounce/jquery.ba-throttle-debounce.js',
            'third/jquery-idle/jquery.idle.js',
            'third/jquery-autosize/jquery.autosize.js',
            'third/spectrum/spectrum.js',
            ('third/handlebars/handlebars.runtime.js'
                if PIPELINE
                else 'third/handlebars/handlebars.js'),

            'js/feature_flags.js',
            'js/util.js',
            'js/setup.js',
            'js/viewport.js',
            'js/rows.js',
            'js/unread.js',
            'js/message_tour.js',
            'js/stream_list.js',
            'js/narrow.js',
            'js/reload.js',
            'js/notifications_bar.js',
            'js/compose.js',
            'js/subs.js',
            'js/message_edit.js',
            'js/ui.js',
            'js/popovers.js',
            'js/typeahead_helper.js',
            'js/search.js',
            'js/composebox_typeahead.js',
            'js/navigate.js',
            'js/hotkey.js',
            'js/notifications.js',
            'js/hashchange.js',
            'js/invite.js',
            'js/message_list.js',
            'js/onboarding.js',
            'js/zephyr.js',
            'js/activity.js',
            'js/colorspace.js',
            'js/timerender.js',
            'js/tutorial.js',
            'js/templates.js',
            'js/avatar.js',
            'js/settings.js',
            'js/tab_bar.js',
            'js/metrics.js',
            'js/emoji.js'
        ],
        'output_filename': 'min/app.js'
    },
    'activity': {
        'source_filenames': (
            'third/sorttable/sorttable.js',
        ),
        'output_filename': 'min/activity.js'
    },
}

if not DEBUG:
    # This file is generated by update-prod-static.
    # In dev we fetch individual templates using Ajax.
    JS_SPECS['app']['source_filenames'].append('templates/compiled.js')


PIPELINE_JS = {}  # Now handled in tools/minify-js
PIPELINE_JS_COMPRESSOR  = None

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_YUI_BINARY     = '/usr/bin/env yui-compressor'


USING_RABBITMQ = DEPLOYED
# This password also appears in servers/configure-rabbitmq
RABBITMQ_PASSWORD = 'xxxxxxxxxxxxxxxx'


SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

CACHES = {
    'default': {
        'BACKEND':  'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT':  3600
    },
    'database': {
        'BACKEND':  'django.core.cache.backends.db.DatabaseCache',
        'LOCATION':  'third_party_api_results',
        # Basically never timeout.  Setting to 0 isn't guaranteed
        # to work, see https://code.djangoproject.com/ticket/9595
        'TIMEOUT': 2000000000,
        'OPTIONS': {
            'MAX_ENTRIES': 100000000,
            'CULL_FREQUENCY': 10,
        }
    },
}

if DEPLOYED:
    SERVER_LOG_PATH = "/home/humbug/logs/server.log"
    EVENT_LOG_DIR = '/home/humbug/logs/event_log'
    ERROR_LOG_DIR = '/home/humbug/logs/errors'
    STATS_DIR = '/home/humbug/stats'
    PERSISTENT_QUEUE_FILENAME = "/home/humbug/tornado/event_queues.pickle"
else:
    EVENT_LOG_DIR = 'event_log'
    SERVER_LOG_PATH = "server.log"
    ERROR_LOG_DIR = 'errors'
    STATS_DIR = 'stats'
    PERSISTENT_QUEUE_FILENAME = "event_queues.pickle"

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
            '()': 'zephyr.lib.logging_util.HumbugLimiter',
        },
        'EmailLimiter': {
            '()': 'zephyr.lib.logging_util.EmailLimiter',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'nop': {
            '()': 'zephyr.lib.logging_util.ReturnTrue',
        },
        'require_really_deployed': {
            '()': 'zephyr.lib.logging_util.RequireReallyDeployed',
        },
    },
    'handlers': {
        'humbug_admins': {
            'level':     'ERROR',
            'class':     'zephyr.handlers.AdminHumbugHandler',
            # For testing the handler delete the next line
            'filters':   ['HumbugLimiter', 'require_debug_false', 'require_really_deployed'],
            'formatter': 'default'
        },
        'console': {
            'level':     'DEBUG',
            'class':     'logging.StreamHandler',
            'formatter': 'default'
        },
        'file': {
            'level':       'DEBUG',
            'class':       'logging.handlers.TimedRotatingFileHandler',
            'formatter':   'default',
            'filename':    SERVER_LOG_PATH,
            'when':        'D',
            'interval':    7,
            'backupCount': 100000000,
        },
        # Django has some hardcoded code to add the
        # require_debug_false filter to the mail_admins handler if no
        # filters are specified.  So for testing, one is recommended
        # to replace the list of filters for mail_admins with 'nop'.
        'mail_admins': {
            'level': 'ERROR',
            'class': 'zephyr.handlers.HumbugAdminEmailHandler',
            # For testing the handler replace the filters list with just 'nop'
            'filters': ['EmailLimiter', 'require_debug_false', 'require_really_deployed'],
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level':    'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['humbug_admins', 'console', 'file', 'mail_admins'],
            'level':    'INFO',
            'propagate': False,
        },
        'humbug.requests': {
            'handlers': ['console', 'file'],
            'level':    'INFO',
            'propagate': False,
        },
        ## Uncomment the following to get all database queries logged to the console
        # 'django.db': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        #     'propagate': False,
        # },
    }
}

TEMPLATE_CONTEXT_PROCESSORS = (
    'zephyr.context_processors.add_settings',
    'zephyr.context_processors.add_metrics',
)

ACCOUNT_ACTIVATION_DAYS=7
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'humbug@humbughq.com'
EMAIL_HOST_PASSWORD = 'xxxxxxxxxxxxxxxx'
EMAIL_PORT = 587

DEFAULT_FROM_EMAIL = "Zulip <zulip@zulip.com>"

LOGIN_REDIRECT_URL='/'
OPENID_SSO_SERVER_URL = 'https://www.google.com/accounts/o8/id'
OPENID_CREATE_USERS = True
OPENID_RENDER_FAILURE = openid_failure_handler

MAILCHIMP_API_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-us4'
HUMBUG_FRIENDS_LIST_ID = '84b2f3da6b'

# Client-side polling timeout for get_events, in milliseconds.
# We configure this here so that the client test suite can override it.
# We already kill the connection server-side with heartbeat events,
# but it's good to have a safety.  This value should be greater than
# (HEARTBEAT_MIN_FREQ_SECS + 10)
POLL_TIMEOUT = 90 * 1000

# The new user tutorial is enabled by default, and disabled for
# client tests.
TUTORIAL_ENABLED = True

HOME_NOT_LOGGED_IN = '/login'
if DEPLOYED:
    ALLOW_REGISTER = False
    FULL_NAVBAR    = False
else:
    ALLOW_REGISTER = True
    FULL_NAVBAR    = True

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

# We want all temporary uploaded files to be stored on disk.

FILE_UPLOAD_MAX_MEMORY_SIZE = 0

# We are not currently using embedly due to some performance issues, but
# we are keeping the code on master for now, behind this launch flag.
# If you turn this back on for dev, you will want it to be still False
# for running the tests, or you will need to ensure that embedly_client.is_supported()
# gets called before the tests run.
USING_EMBEDLY = False
EMBEDLY_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

if DEPLOYED:
    S3_KEY="xxxxxxxxxxxxxxxxxxxx"
    S3_SECRET_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    S3_BUCKET="humbug-user-uploads"
    S3_AVATAR_BUCKET="humbug-user-avatars"

    MIXPANEL_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
else:
    S3_KEY="xxxxxxxxxxxxxxxxxxxx"
    S3_SECRET_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    S3_BUCKET="humbug-user-uploads-test"
    S3_AVATAR_BUCKET="humbug-user-avatars-test"

    MIXPANEL_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Hack to allow longer-than-72-characters inputs into "username" forms
#
# This is needed because we're using the email address as the "username".
#
# This code can go away once we switch to Django 1.5 with pluggable
# user models
#
# Adapted from https://gist.github.com/1143957
from django.conf import settings

import sys

USERNAME_MAXLENGTH = getattr(settings, 'USERNAME_MAXLENGTH', 72)

def hack_forms(length=USERNAME_MAXLENGTH, forms=[
        'django.contrib.auth.forms.UserCreationForm',
        'django.contrib.auth.forms.UserChangeForm',
        'django.contrib.auth.forms.AuthenticationForm',
    ]):
    """
    Hacks username length in django forms.
    """
    for form in forms:
        modulename, sep, classname = form.rpartition('.')
        if not modulename in sys.modules:
            __import__(modulename)
        module = sys.modules[modulename]
        klass = getattr(module, classname)
        hack_single_form(klass, length)

def hack_single_form(form_class, length=USERNAME_MAXLENGTH):
    if hasattr(form_class, 'declared_fields'):
        fields = form_class.declared_fields
    elif hasattr(form_class, 'base_fields'):
        fields = form_class.base_fields
    else:
        raise TypeError('Provided object: %s doesnt seem to be a valid Form or '
                        'ModelForm class.' % form_class)
    username = fields['username']
    hack_validators(username.validators)
    username.max_length = length
    username.widget.attrs['maxlength'] = length

def hack_validators(validators, length=USERNAME_MAXLENGTH):
    from django.core.validators import MaxLengthValidator
    for key, validator in enumerate(validators):
        if isinstance(validator, MaxLengthValidator):
            validators.pop(key)
    validators.insert(0, MaxLengthValidator(length))

hack_forms()

from django.conf import settings
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView, RedirectView
import os.path
import zephyr.forms

# NB: There are several other pieces of code which route requests by URL:
#
#   - runtornado.py has its own URL list for Tornado views.  See the
#     invocation of web.Application in that file.
#
#   - The Nginx config knows which URLs to route to Django or Tornado.
#
#   - Likewise for the local dev server in tools/run-dev.py.

urlpatterns = patterns('',
    url(r'^$', 'zephyr.views.home'),
    url(r'^accounts/login/openid/$', 'django_openid_auth.views.login_begin', name='openid-login'),
    url(r'^accounts/login/openid/done/$', 'zephyr.views.process_openid_login', name='openid-complete'),
    url(r'^accounts/login/openid/done/$', 'django_openid_auth.views.login_complete', name='openid-complete'),
    # We have two entries for accounts/login to allow reverses on the Django
    # view we're wrapping to continue to function.
    url(r'^accounts/login/',  'zephyr.views.login_page',         {'template_name': 'zephyr/login.html'}),
    url(r'^accounts/login/',  'django.contrib.auth.views.login', {'template_name': 'zephyr/login.html'}),
    url(r'^accounts/logout/', 'zephyr.views.logout_then_login'),

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
    url(r'^accounts/send_confirm/(?P<email>[\S]+)?',
        TemplateView.as_view(template_name='zephyr/accounts_send_confirm.html'), name='send_confirm'),
    url(r'^accounts/register/', 'zephyr.views.accounts_register'),
    url(r'^accounts/do_confirm/(?P<confirmation_key>[\w]+)', 'confirmation.views.confirm'),
    url(r'^invite/$', 'zephyr.views.initial_invite_page', name='initial-invite-users'),

    # Portico-styled page used to provide email confirmation of terms acceptance.
    url(r'^accounts/accept_terms/$', 'zephyr.views.accounts_accept_terms'),

    # Terms of service and privacy policy
    url(r'^terms/$',   TemplateView.as_view(template_name='zephyr/terms.html')),
    url(r'^privacy/$', TemplateView.as_view(template_name='zephyr/privacy.html')),

    # "About Humbug" information
    url(r'^what-is-humbug/$', TemplateView.as_view(template_name='zephyr/what-is-humbug.html')),
    url(r'^new-user/$', TemplateView.as_view(template_name='zephyr/new-user.html')),
    url(r'^features/$', TemplateView.as_view(template_name='zephyr/features.html')),

    # Landing page, signup form, and nice register URL
    url(r'^hello/$', TemplateView.as_view(template_name='zephyr/hello.html'),
                                         name='landing-page'),
    url(r'^signup/$', TemplateView.as_view(template_name='zephyr/signup.html'),
                                         name='signup'),
    url(r'^signup/sign-me-up$', 'zephyr.views.beta_signup_submission', name='beta-signup-submission'),
    url(r'^register/$', 'zephyr.views.accounts_home', name='register'),
    url(r'^login/$',  'zephyr.views.login_page', {'template_name': 'zephyr/login.html'}),

    # API and integrations documentation
    url(r'^api/$', TemplateView.as_view(template_name='zephyr/api.html')),
    url(r'^api/endpoints/$', 'zephyr.views.api_endpoint_docs'),
    url(r'^integrations/$', TemplateView.as_view(template_name='zephyr/integrations.html')),
    url(r'^zephyr/$', TemplateView.as_view(template_name='zephyr/zephyr.html')),
    url(r'^apps$', TemplateView.as_view(template_name='zephyr/apps.html')),

    # Job postings
    url(r'^jobs/$', TemplateView.as_view(template_name='zephyr/jobs/index.html')),
    url(r'^jobs/lead-designer/$', TemplateView.as_view(template_name='zephyr/jobs/lead-designer.html')),

    url(r'^robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),
)

urlpatterns += patterns('zephyr.views',
    # These are json format views used by the web client.  They require a logged in browser.
    url(r'^json/update_pointer$',           'json_update_pointer'),
    url(r'^json/get_old_messages$',         'json_get_old_messages'),
    url(r'^json/get_public_streams$',       'json_get_public_streams'),
    url(r'^json/send_message$',             'json_send_message'),
    url(r'^json/invite_users$',             'json_invite_users'),
    url(r'^json/bulk_invite_users$',        'json_bulk_invite_users'),
    url(r'^json/settings/change$',          'json_change_settings'),
    url(r'^json/subscriptions/list$',       'json_list_subscriptions'),
    url(r'^json/subscriptions/remove$',     'json_remove_subscriptions'),
    url(r'^json/subscriptions/add$',        'json_add_subscriptions'),
    url(r'^json/subscriptions/exists$',     'json_stream_exists'),
    url(r'^json/subscriptions/property$',   'json_subscription_property'),
    url(r'^json/get_subscribers$',          'json_get_subscribers'),
    url(r'^json/fetch_api_key$',            'json_fetch_api_key'),
    url(r'^json/get_members$',              'json_get_members'),
    url(r'^json/update_active_status$',     'json_update_active_status'),
    url(r'^json/get_active_statuses$',      'json_get_active_statuses'),
    url(r'^json/tutorial_status$',          'json_tutorial_status'),
    url(r'^json/change_enter_sends$',       'json_change_enter_sends'),
    url(r'^json/get_profile$',              'json_get_profile'),
    url(r'^json/report_error$',             'json_report_error'),
    url(r'^json/update_message_flags$',     'json_update_flags'),
    url(r'^json/register$',                 'json_events_register'),
    url(r'^json/upload_file$',              'json_upload_file'),
    url(r'^json/messages_in_narrow$',       'json_messages_in_narrow'),
    url(r'^json/create_bot$',               'json_create_bot'),
    url(r'^json/get_bots$',                 'json_get_bots'),
    url(r'^json/update_onboarding_steps$',  'json_update_onboarding_steps'),
    url(r'^json/update_message$',           'json_update_message'),
    url(r'^json/fetch_raw_message$',        'json_fetch_raw_message'),

    # These are json format views used by the API.  They require an API key.
    url(r'^api/v1/get_profile$',            'api_get_profile'),
    url(r'^api/v1/get_old_messages$',       'api_get_old_messages'),
    url(r'^api/v1/get_public_streams$',     'api_get_public_streams'),
    url(r'^api/v1/subscriptions/list$',     'api_list_subscriptions'),
    url(r'^api/v1/subscriptions/add$',      'api_add_subscriptions'),
    url(r'^api/v1/subscriptions/remove$',   'api_remove_subscriptions'),
    url(r'^api/v1/get_subscribers$',        'api_get_subscribers'),
    url(r'^api/v1/send_message$',           'api_send_message'),
    url(r'^api/v1/update_pointer$',         'api_update_pointer'),
    url(r'^api/v1/get_members$',            'api_get_members'),

    # This json format view used by the API accepts a username password/pair and returns an API key.
    url(r'^api/v1/fetch_api_key$',          'api_fetch_api_key'),

    # These are integration-specific web hook callbacks
    url(r'^api/v1/external/beanstalk$' ,    'api_beanstalk_webhook'),
    url(r'^api/v1/external/github$',        'api_github_landing'),
    url(r'^api/v1/external/jira$',          'api_jira_webhook'),
    url(r'^api/v1/external/pivotal$',       'api_pivotal_webhook'),
    url(r'^api/v1/external/newrelic$',      'api_newrelic_webhook'),
)

v1_api_and_json_patterns = patterns('zephyr.views',
    # JSON format views used by the redesigned API, accept basic auth username:password.
    # GET returns messages, possibly filtered, POST sends a message
    url(r'^messages$', 'rest_dispatch',
            {'GET':  'get_old_messages_backend',
             'PATCH': 'update_message_backend',
             'POST': 'send_message_backend'}),
    url(r'^streams$', 'rest_dispatch',
            {'GET':  'get_public_streams_backend'}),
    # GET returns "stream info" (undefined currently?), HEAD returns whether stream exists (200 or 404)
    url(r'^streams/(?P<stream_name>.*)/members$', 'rest_dispatch',
            {'GET': 'get_subscribers_backend'}),
    url(r'^streams/(?P<stream_name>.*)$', 'rest_dispatch',
            {'HEAD': 'stream_exists_backend',
             'GET': 'stream_exists_backend'}),
    url(r'^users$', 'rest_dispatch',
            {'GET': 'get_members_backend'}),
    url(r'^users/me$', 'rest_dispatch',
            {'GET': 'get_profile_backend'}),
    url(r'^users/me/enter-sends$', 'rest_dispatch',
            {'POST': 'json_change_enter_sends'}),
    url(r'^users/me/pointer$', 'rest_dispatch',
            {'GET': 'get_pointer_backend',
             'PUT': 'update_pointer_backend'}),
    # GET lists your streams, POST bulk adds, PATCH bulk modifies/removes
    url(r'^users/me/subscriptions$', 'rest_dispatch',
            {'GET': 'list_subscriptions_backend',
             'POST': 'add_subscriptions_backend',
             'PATCH': 'update_subscriptions_backend'}),
    url(r'^users/(?P<email>.*)$', 'rest_dispatch',
            {'DELETE': 'deactivate_user_backend'}),
    url(r'^bots/(?P<email>.*)/api_key/regenerate$', 'rest_dispatch',
            {'POST': 'regenerate_bot_api_key'}),
    url(r'^bots/(?P<email>.*)$', 'rest_dispatch',
            {'POST': 'update_bot_backend'}),
    url(r'^register$', 'rest_dispatch',
            {'POST': 'api_events_register'}),
    url(r'^messages/latest$', 'rest_dispatch',
        {'GET': 'get_updates_backend'}),
    url(r'^events$', 'rest_dispatch',
        {'GET': 'get_events_backend'}),
)


urlpatterns += patterns('zephyr.tornadoviews',
    # Tornado views
    url(r'^api/v1/get_messages$',           'api_get_messages'),
    url(r'^json/get_updates$',              'json_get_updates'),
    url(r'^json/get_events$',               'json_get_events'),
    # Used internally for communication between Django and Tornado processes
    url(r'^notify_tornado$',                'notify'),
)

# Include the dual-use patterns twice
urlpatterns += patterns('',
    url(r'^api/v1/', include(v1_api_and_json_patterns)),
    url(r'^json/', include(v1_api_and_json_patterns)),
)


if not settings.DEPLOYED:
    use_prod_static = getattr(settings, 'PIPELINE', False)
    static_root = os.path.join(settings.DEPLOY_ROOT,
        'prod-static/serve' if use_prod_static else 'static')

    urlpatterns += patterns('',
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': static_root}))

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
import os
import traceback
import signal

from zephyr_mirror_backend import parse_args
from zephyr_mirror_backend import RandomExponentialBackoff

def die(signal, frame):
    # We actually want to exit, so run os._exit (so as not to be caught and restarted)
    os._exit(1)

signal.signal(signal.SIGINT, die)

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

backoff = RandomExponentialBackoff()
while backoff.keep_going():
    print "Starting zephyr mirroring bot"
    try:
        subprocess.call(args)
    except:
        traceback.print_exc()
    backoff.fail()

print ""
print ""
print "ERROR: The Zephyr mirroring bot is unable to continue mirroring Zephyrs."
print "This is often caused by failing to maintain unexpired Kerberos tickets"
print "or AFS tokens.  See https://zulip.com/zephyr for documentation on how to"
print "maintain unexpired Kerberos tickets and AFS tokens."
print ""
sys.exit(1)


# Humbug Inc's internal git plugin configuration.
# The plugin and example config are under api/integrations/

# Leaving all the instructions out of this file to avoid having to
# sync them as we update the comments.

HUMBUG_USER = "commit-bot@zulip.com"
HUMBUG_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# commit_notice_destination() lets you customize where commit notices
# are sent to.
#
# It takes the following arguments:
# * repo   = the name of the git repository
# * branch = the name of the branch that was pushed to
# * commit = the commit id
#
# Returns a dictionary encoding the stream and subject to send the
# notification to (or None to send no notification, e.g. for ).
#
# The default code below will send every commit pushed to "master" to
# * stream "commits"
# * subject "deploy => master" (using a pretty unicode right arrow)
# And similarly for branch "test-post-receive" (for use when testing).
def commit_notice_destination(repo, branch, commit):
    if branch in ["master", "prod", "test-post-receive"]:
        return dict(stream  = 'test' if 'test-' in branch else 'commits',
                    subject = u"deploy \u21D2 %s" % (branch,))

    # Return None for cases where you don't want a notice sent
    return None

HUMBUG_API_PATH = "/home/humbug/humbug/api"
HUMBUG_SITE = "https://staging.zulip.com"

# Humbug Inc's internal trac plugin configuration.
# The plugin and example config are under api/integrations/

# Leaving all the instructions out of this file to avoid having to
# sync them as we update the comments.

HUMBUG_USER = "trac-bot@zulip.com"
HUMBUG_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
STREAM_FOR_NOTIFICATIONS = "trac"
TRAC_BASE_TICKET_URL = "https://trac.humbughq.com/ticket"

TRAC_NOTIFY_FIELDS = ["description", "summary", "resolution", "comment",
                      "owner"]
HUMBUG_API_PATH = "/home/humbug/humbug/api"
HUMBUG_SITE = "https://staging.zulip.com"

#!/usr/bin/env python
import time

def nagios_from_file(results_file):
    """Returns a nagios-appropriate string and return code obtained by
    parsing the desired file on disk. The file on disk should be of format

    %s|%s % (timestamp, nagios_string)

    This file is created by various nagios checking cron jobs such as
    check-rabbitmq-queues and check-rabbitmq-consumers"""

    data = file(results_file).read().strip()
    pieces = data.split('|')

    if not len(pieces) == 4:
        state = 'UNKNOWN'
        ret = 3
        data = "Results file malformed"
    else:
        timestamp = int(pieces[0])

        time_diff = time.time() - timestamp
        if time_diff > 60 * 2:
            ret = 3
            state = 'UNKNOWN'
            data = "Results file is stale"
        else:
            ret = int(pieces[1])
            state = pieces[2]
            data = pieces[3]

    return (ret, "%s: %s" % (state, data))


#!/usr/bin/env python
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
try:
    import simplejson
except ImportError:
    import json as simplejson
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
import tempfile
import random
import select

class CountingBackoff(object):
    def __init__(self, maximum_retries=10):
        self.number_of_retries = 0
        self.maximum_retries = maximum_retries

    def keep_going(self):
        return self.number_of_retries < self.maximum_retries

    def succeed(self):
        self.number_of_retries = 0

    def fail(self):
        self.number_of_retries = min(self.number_of_retries + 1,
                                     self.maximum_retries)

class RandomExponentialBackoff(CountingBackoff):
    def fail(self):
        self.number_of_retries = min(self.number_of_retries + 1,
                                     self.maximum_retries)
        # Exponential growth with ratio sqrt(2); compute random delay
        # between x and 2x where x is growing exponentially
        delay_scale = int(2 ** (self.number_of_retries / 2.0 - 1)) + 1
        delay = delay_scale + random.randint(1, delay_scale)
        message = "Sleeping for %ss [max %s] before retrying." % (delay, delay_scale * 2)
        try:
            logger.warning(message)
        except NameError:
            print message
        time.sleep(delay)

DEFAULT_SITE = "https://api.zulip.com"

class States:
    Startup, HumbugToZephyr, ZephyrToHumbug, ChildSending = range(4)
CURRENT_STATE = States.Startup

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
        logger.warning("Streams were: %s" % ([cls for cls, instance, recipient in subs],))
        return
    try:
        actual_zephyr_subs = [cls for (cls, _, _) in zephyr._z.getSubscriptions()]
    except IOError:
        logger.exception("Error getting current Zephyr subscriptions")
        # Don't add anything to current_zephyr_subs so that we'll
        # retry the next time we check for streams to subscribe to
        # (within 15 seconds).
        return
    for (cls, instance, recipient) in subs:
        if cls not in actual_zephyr_subs:
            logger.error("Zephyr failed to subscribe us to %s; will retry" % (cls,))
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

def update_subscriptions():
    try:
        f = file("/home/humbug/public_streams", "r")
        public_streams = simplejson.loads(f.read())
        f.close()
    except:
        logger.exception("Error reading public streams:")
        return

    classes_to_subscribe = set()
    for stream in public_streams:
        zephyr_class = stream.encode("utf-8")
        if (options.shard is not None and
            not hashlib.sha1(zephyr_class).hexdigest().startswith(options.shard)):
            # This stream is being handled by a different zephyr_mirror job.
            continue
        if zephyr_class in current_zephyr_subs:
            continue
        classes_to_subscribe.add((zephyr_class, "*", "*"))

    if len(classes_to_subscribe) > 0:
        zephyr_bulk_subscribe(list(classes_to_subscribe))

def maybe_kill_child():
    try:
        if child_pid is not None:
            os.kill(child_pid, signal.SIGTERM)
    except OSError:
        # We don't care if the child process no longer exists, so just log the error
        logger.exception("")

def maybe_restart_mirroring_script():
    if os.stat(os.path.join(options.root_path, "stamps", "restart_stamp")).st_mtime > start_time or \
            ((options.user == "tabbott" or options.user == "tabbott/extra") and
             os.stat(os.path.join(options.root_path, "stamps", "tabbott_stamp")).st_mtime > start_time):
        logger.warning("")
        logger.warning("zephyr mirroring script has been updated; restarting...")
        maybe_kill_child()
        try:
            zephyr._z.cancelSubs()
        except IOError:
            # We don't care whether we failed to cancel subs properly, but we should log it
            logger.exception("")
        while True:
            try:
                os.execvp(os.path.join(options.root_path, "user_root", "zephyr_mirror_backend.py"), sys.argv)
            except Exception:
                logger.exception("Error restarting mirroring script; trying again... Traceback:")
                time.sleep(1)

def process_loop(log):
    restart_check_count = 0
    last_check_time = time.time()
    while True:
        select.select([zephyr._z.getFD()], [], [], 15)
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

        if time.time() - last_check_time > 15:
            last_check_time = time.time()
            try:
                maybe_restart_mirroring_script()
                if restart_check_count > 0:
                    logger.info("Stopped getting errors checking whether restart is required.")
                    restart_check_count = 0
            except Exception:
                if restart_check_count < 5:
                    logger.exception("Error checking whether restart is required:")
                    restart_check_count += 1

            if options.forward_class_messages:
                try:
                    update_subscriptions()
                except Exception:
                    logger.exception("Error updating subscriptions from Zulip:")

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
    if notice.format.startswith("Zephyr error: See") or notice.format.endswith("@(@color(blue))"):
        logger.debug("Skipping message we got from Zulip!")
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
        global CURRENT_STATE
        CURRENT_STATE = States.ChildSending
        # Actually send the message in a child process, to avoid blocking.
        try:
            res = send_humbug(zeph)
            if res.get("result") != "success":
                logger.error("Error relaying zephyr:\n%s\n%s" % (zeph, res))
        except Exception:
            logger.exception("Error relaying zephyr:")
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

def quit_failed_initialization(message):
    logger.error(message)
    maybe_kill_child()
    sys.exit(1)

def zephyr_init_autoretry():
    backoff = RandomExponentialBackoff()
    while backoff.keep_going():
        try:
            # zephyr.init() tries to clear old subscriptions, and thus
            # sometimes gets a SERVNAK from the server
            zephyr.init()
            backoff.succeed()
            return
        except IOError:
            logger.exception("Error initializing Zephyr library (retrying).  Traceback:")
            backoff.fail()

    quit_failed_initialization("Could not initialize Zephyr library, quitting!")

def zephyr_subscribe_autoretry(sub):
    backoff = RandomExponentialBackoff()
    while backoff.keep_going():
        try:
            zephyr.Subscriptions().add(sub)
            backoff.succeed()
            return
        except IOError:
            # Probably a SERVNAK from the zephyr server, but log the
            # traceback just in case it's something else
            logger.exception("Error subscribing to personals (retrying).  Traceback:")
            backoff.fail()

    quit_failed_initialization("Could not subscribe to personals, quitting!")

def zephyr_to_humbug(options):
    zephyr_init_autoretry()
    if options.forward_class_messages:
        update_subscriptions()
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

    logger.info("Successfully initialized; Starting receive loop.")

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
        logger.error("zwrite command '%s' failed with return code %d:" % (
            " ".join(zwrite_args), p.returncode,))
        if stdout:
            logger.info("stdout: " + stdout)
    elif stderr:
        logger.warning("zwrite command '%s' printed the following warning:" % (
            " ".join(zwrite_args),))
    if stderr:
        logger.warning("stderr: " + stderr)
    return (p.returncode, stderr)

def send_authed_zephyr(zwrite_args, content):
    return send_zephyr(zwrite_args, content)

def send_unauthed_zephyr(zwrite_args, content):
    return send_zephyr(zwrite_args + ["-d"], content)

def forward_to_zephyr(message):
    wrapper = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)
    wrapped_content = "\n".join("\n".join(wrapper.wrap(line))
            for line in message["content"].replace("@", "@@").split("\n"))

    zwrite_args = ["zwrite", "-n", "-s", message["sender_full_name"], "-F", "Zephyr error: See http://zephyr.1ts.org/wiki/df"]
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

    heading = "Hi there! This is an automated message from Zulip."
    support_closing = """If you have any questions, please be in touch through the \
Feedback tab or at support@zulip.com."""

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

Your last message was forwarded from Zulip to Zephyr unauthenticated, \
because your Kerberos tickets have expired. It was sent successfully, \
but please renew your Kerberos tickets in the screen session where you \
are running the Zulip-Zephyr mirroring bot, so we can send \
authenticated Zephyr messages for you again.

%s""" % (heading, support_closing))

    # zwrite failed and it wasn't because of expired tickets: This is
    # probably because the recipient isn't subscribed to personals,
    # but regardless, we should just notify the user.
    return send_error_humbug("""%s

Your Zulip-Zephyr mirror bot was unable to forward that last message \
from Zulip to Zephyr. That means that while Zulip users (like you) \
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
            # We forward mail zephyrs, so no need to log a warning.
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
        res = humbug_client.add_subscriptions(list({"name": stream} for stream in zephyr_subscriptions))
        if res.get("result") != "success":
            logger.error("Error subscribing to streams:\n%s" % (res["msg"],))
            return

        already = res.get("already_subscribed")
        new = res.get("subscribed")
        if verbose:
            if already is not None and len(already) > 0:
                logger.info("\nAlready subscribed to: %s" % (", ".join(already.values()[0]),))
            if new is not None and len(new) > 0:
                logger.info("\nSuccessfully subscribed to: %s" % (", ".join(new.values()[0]),))

    if len(skipped) > 0:
        if verbose:
            logger.info("\n" + "\n".join(textwrap.wrap("""\
You have some lines in ~/.zephyr.subs that could not be
synced to your Zulip subscriptions because they do not
use "*" as both the instance and recipient and not one of
the special cases (e.g. personals and mail zephyrs) that
Zulip has a mechanism for forwarding.  Zulip does not
allow subscribing to only some subjects on a Zulip
stream, so this tool has not created a corresponding
Zulip subscription to these lines in ~/.zephyr.subs:
""")) + "\n")

    for (cls, instance, recipient, reason) in skipped:
        if verbose:
            if reason != "":
                logger.info("  [%s,%s,%s] (%s)" % (cls, instance, recipient, reason))
            else:
                logger.info("  [%s,%s,%s]" % (cls, instance, recipient))
    if len(skipped) > 0:
        if verbose:
            logger.info("\n" + "\n".join(textwrap.wrap("""\
If you wish to be subscribed to any Zulip streams related
to these .zephyrs.subs lines, please do so via the Zulip
web interface.
""")) + "\n")

def valid_stream_name(name):
    return name != ""

def parse_zephyr_subs(verbose=False):
    zephyr_subscriptions = set()
    subs_file = os.path.join(os.environ["HOME"], ".zephyr.subs")
    if not os.path.exists(subs_file):
        if verbose:
            logger.error("Couldn't find ~/.zephyr.subs!")
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
                    logger.error("Skipping subscription to unsupported class name: [%s]" % (line,))
                continue
        except Exception:
            if verbose:
                logger.error("Couldn't parse ~/.zephyr.subs line: [%s]" % (line,))
            continue
        zephyr_subscriptions.add((cls.strip(), instance.strip(), recipient.strip()))
    return zephyr_subscriptions

def open_logger():
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
    log_format = "%(asctime)s <initial>: %(message)s"
    formatter = logging.Formatter(log_format)
    logging.basicConfig(format=log_format)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

def configure_logger(logger, direction_name):
    if direction_name is None:
        log_format = "%(message)s"
    else:
        log_format = "%(asctime)s [" + direction_name + "] %(message)s"
    formatter = logging.Formatter(log_format)

    # Replace the formatters for the file and stdout loggers
    for handler in logger.handlers:
        handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

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

def die_gracefully(signal, frame):
    if CURRENT_STATE == States.HumbugToZephyr or CURRENT_STATE == States.ChildSending:
        # this is a child process, so we want os._exit (no clean-up necessary)
        os._exit(1)

    if CURRENT_STATE == States.ZephyrToHumbug:
        try:
            # zephyr=>humbug processes may have added subs, so run cancelSubs
            zephyr._z.cancelSubs()
        except IOError:
            # We don't care whether we failed to cancel subs properly, but we should log it
            logger.exception("")

    sys.exit(1)

if __name__ == "__main__":
    # Set the SIGCHLD handler back to SIG_DFL to prevent these errors
    # when importing the "requests" module after being restarted using
    # the restart_stamp functionality:
    #
    # close failed in file object destructor:
    # IOError: [Errno 10] No child processes
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)

    signal.signal(signal.SIGINT, die_gracefully)

    (options, args) = parse_args()

    logger = open_logger()
    configure_logger(logger, "parent")

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
            logger.error("\n" + "\n".join(textwrap.wrap("""\
Could not find API key file.
You need to either place your api key file at %s,
or specify the --api-key-file option.""" % (options.api_key_file,))))
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
        configure_logger(logger, None)  # make the output cleaner
        logger.info("Syncing your ~/.zephyr.subs to your Zulip Subscriptions!")
        add_humbug_subscriptions(True)
        sys.exit(0)

    # Kill all zephyr_mirror processes other than this one and its parent.
    if not options.test_mode:
        pgrep_query = "python.*zephyr_mirror"
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
            logger.info("Killing duplicate zephyr_mirror process %s" % (pid,))
            try:
                os.kill(pid, signal.SIGINT)
            except OSError:
                # We don't care if the target process no longer exists, so just log the error
                logger.exception("")

    if options.shard is not None and set(options.shard) != set("a"):
        # The shard that is all "a"s is the one that handles personals
        # forwarding and humbug => zephyr forwarding
        options.forward_personals = False
        options.forward_from_humbug = False

    if options.forward_from_humbug:
        child_pid = os.fork()
        if child_pid == 0:
            CURRENT_STATE = States.HumbugToZephyr
            # Run the humbug => zephyr mirror in the child
            configure_logger(logger, "humbug=>zephyr")
            humbug_to_zephyr(options)
            sys.exit(0)
    else:
        child_pid = None
    CURRENT_STATE = States.ZephyrToHumbug

    import zephyr
    logger_name = "zephyr=>humbug"
    if options.shard is not None:
        logger_name += "(%s)" % (options.shard,)
    configure_logger(logger, logger_name)
    # Have the kernel reap children for when we fork off processes to send Humbugs
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    zephyr_to_humbug(options)

#!/usr/bin/env python
import sys
import pstats

'''
This is a helper script to make it easy to show profile
results after using a Python decorator.  It's meant to be
a simple example that you can hack on, or better yet, you
can find more advanced tools for showing profiler results.
'''

try:
    fn = sys.argv[1]
except:
    print '''
    Please supply a filename.  (If you use the profiled decorator,
    the file will have a suffix of ".profile".)
    '''
    sys.exit(1)

p = pstats.Stats(fn)
p.strip_dirs().sort_stats('cumulative').print_stats(25)
p.strip_dirs().sort_stats('time').print_stats(25)


#!/usr/bin/env python
#
# Generates % delta activity metrics from graphite/statsd data
#
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import optparse
from datetime import timedelta, datetime
from zephyr.lib.timestamp import datetime_to_timestamp
from zephyr.lib.utils import statsd_key
import requests

# Workaround to support the Python-requests 1.0 transition of .json
# from a property to a function
requests_json_is_function = callable(requests.Response.json)
def extract_json_response(resp):
    if requests_json_is_function:
        return resp.json()
    else:
        return resp.json

def get_data_url(buckets, realm):
    realm_key = statsd_key(realm, True)

    # This is the slightly-cleaned up JSON api version of https://graphiti.zulip.net/graphs/945c7aafc2d
    #
    # Fetches 1 month worth of data
    DATA_URL="https://graphite.zulip.net/render/?from=-1000d&format=json"
    for bucket in buckets:
        if realm != 'all':
            statsd_target = "stats.gauges.staging.users.active.%s.%s" % (realm_key, bucket)
            DATA_URL += "&target=%s" % (statsd_target,)
        else:
            # all means adding up all realms, but exclude the .all. metrics since that would double things
            DATA_URL += "&target=sum(exclude(stats.gauges.staging.users.active.*.%s, 'all'))" % (bucket,)
    return DATA_URL

def get_data(url, username, pw):
    from requests.auth import HTTPDigestAuth

    res = requests.get(url, auth=HTTPDigestAuth(username, pw), verify=False)

    if res.status_code != 200:
        print "Failed to fetch data url: %s" % (res.error,)
        return []

    return extract_json_response(res)

def noon_of(day=datetime.now()):
    return datetime(year=day.year, month=day.month, day=day.day, hour=12)

def points_during_day(data, noon):
    """Returns all the points in the dataset that occur in the 12 hours around
    the datetime object that is passed in. data must be sorted."""
    before =datetime_to_timestamp(noon - timedelta(hours=12))
    after = datetime_to_timestamp(noon + timedelta(hours=12))

    between = filter(lambda pt: pt[1] > before and pt[1] < after, data)
    return between

def best_during_day(data, day):
    valid = sorted(points_during_day(data, day), key=lambda pt: pt[0], reverse=True)
    if len(valid):
        return valid[0][0]
    else:
        return None

def percent_diff(prev, cur):
    if prev is None or cur is None:
        return None
    if cur == 0 and prev == 0:
        return ""
    if prev == 0:
        return "NaN"
    return "%.02f%%" % (((cur - prev) / prev) * 100,)

def parse_data(data, today):
    def print_results(all_days, days, compare_with_last=False):
        first_data_point = True
        best_last_time = 0
        for i in all_days:
            day = today - timedelta(days=i)
            # Ignore weekends
            if day.weekday() in days:
                best = best_during_day(metric['datapoints'], day)
                if best is None:
                    continue

                if not compare_with_last:
                    percent = percent_diff(best, best_today)
                else:
                    if first_data_point:
                        percent = ""
                        first_data_point = False
                    else:
                        percent = percent_diff(best_last_time, best)

                if best is not None:
                    print "Last %s, %s %s ago:\t%.01f\t\t%s" \
                        % (day.strftime("%A"), i, "days", best, percent)
                best_last_time = best

    for metric in data:
        # print "Got %s with data points %s" % (metric['target'], len(metric['datapoints']))
        # Calculate % between peak 2hr and 10min across each day and week
        metric['datapoints'].sort(key=lambda p: p[1])

        best_today = best_during_day(metric['datapoints'], today)
        print "Date\t\t\t\tUsers\t\tChange from then to today"
        print "Today, 0 days ago:\t\t%.01f" % (best_today,)
        print_results(xrange(1, 1000), [0, 1, 2, 3, 4, 7])

        print "\n\nWeekly Wednesday results"
        print "Date\t\t\t\tUsers\t\tDelta from previous week"
        print_results(reversed(xrange(1, 1000)), [2], True)



parser = optparse.OptionParser(r"""

%prog --user username --password pw [--start-from unixtimestamp]

    Generates activity statistics with detailed week-over-week percentage change
""")

parser.add_option('--user',
                  help='Graphite usernarme',
                  metavar='USER')
parser.add_option('--password',
                  help='Graphite password',
                  metavar='PASSWORD')
parser.add_option('--start-from',
                  help='What day to consider as \'today\' when calculating stats as a Unix timestamp',
                  metavar='STARTDATE',
                  default='today')
parser.add_option('--realm',
                  help='Which realm to query',
                  default='all')
parser.add_option('--bucket',
                  help='Which bucket to query',
                  default='12hr')

if __name__ == '__main__':
    (options, args) = parser.parse_args()

    if not options.user or not options.password:
        parser.error("You must enter a username and password to log into graphite with")

    startfrom = noon_of(day=datetime.now())
    if options.start_from != 'today':
        startfrom = noon_of(day=datetime.fromtimestamp(int(options.start_from)))
        print "Using baseline of today as %s" % (startfrom,)

    realm_key = statsd_key(options.realm, True)
    buckets = [options.bucket]

    # This is the slightly-cleaned up JSON api version of https://graphiti.zulip.net/graphs/945c7aafc2d
    #
    # Fetches 1 month worth of data
    DATA_URL = get_data_url(buckets, options.realm)
    data = get_data(DATA_URL, options.user, options.password)


    parse_data(data, startfrom)

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

# Clean up stale .pyc files etc.
subprocess.check_call('./tools/clean-repo')

# Set up a new process group, so that we can later kill run{server,tornado}
# and all of the processes they spawn.
os.setpgrp()

# Pass --nostatic because we configure static serving ourselves in
# humbug/urls.py.
for cmd in ['python manage.py runserver --nostatic %s localhost:%d'
                % (manage_args, django_port),
            'python manage.py runtornado %s localhost:%d'
                % (manage_args, tornado_port)]:
    subprocess.Popen(cmd, shell=True)

class Resource(resource.Resource):
    def getChild(self, name, request):
        request.requestHeaders.setRawHeaders('X-Forwarded-Host', [proxy_host])

        if (request.uri in ['/json/get_updates', '/api/v1/get_messages', '/json/get_events'] or
            request.uri.startswith('/api/v1/messages/latest') or
            request.uri.startswith('/api/v1/events')):
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

import subprocess
import os

# check_output is backported from subprocess.py in Python 2.7

def check_output(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output

DEPLOYMENTS_DIR = "/home/humbug/humbug-deployments"
LOCK_DIR = os.path.join(DEPLOYMENTS_DIR, "lock")
TIMESTAMP_FORMAT = '%Y-%m-%d-%H-%M-%S'

# Color codes
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: models.py 28 2009-10-22 15:03:02Z jarek.zgoda $'

import os
import re
import base64

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


B16_RE = re.compile('^[a-f0-9]{40}$')

def generate_key():
    return base64.b16encode(os.urandom(20)).lower()

def generate_activation_url(key):
    current_site = Site.objects.get_current()
    return u'https://%s%s' % (current_site.domain,
            reverse('confirmation.views.confirm', kwargs={'confirmation_key': key}))


class ConfirmationManager(models.Manager):

    def confirm(self, confirmation_key):
        if B16_RE.search(confirmation_key):
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

    def get_link_for_object(self, obj):
        key = generate_key()
        self.create(content_object=obj, date_sent=now(), confirmation_key=key)
        return generate_activation_url(key)

    def send_confirmation(self, obj, email_address, additional_context=None,
            subject_template_path=None, body_template_path=None):
        confirmation_key = generate_key()
        current_site = Site.objects.get_current()
        activate_url = generate_activation_url(confirmation_key)
        context = Context({
            'activate_url': activate_url,
            'current_site': current_site,
            'confirmation_key': confirmation_key,
            'target': obj,
            'days': getattr(settings, 'EMAIL_CONFIRMATION_DAYS', 10),
        })
        if additional_context is not None:
            context.update(additional_context)
        templates = [
            'confirmation/%s_confirmation_email_subject.txt' % obj._meta.module_name,
            'confirmation/confirmation_email_subject.txt',
        ]
        if subject_template_path:
            template = loader.get_template(subject_template_path)
        else:
            template = loader.select_template(templates)
        subject = template.render(context).strip().replace(u'\n', u' ') # no newlines, please
        templates = [
            'confirmation/%s_confirmation_email_body.txt' % obj._meta.module_name,
            'confirmation/confirmation_email_body.txt',
        ]
        if body_template_path:
            template = loader.get_template(body_template_path)
        else:
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
        'gafyd_name': request.GET.get("gafyd_name", None),
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import humbug

import os
from distutils.core import setup

def recur_expand(target_root, dir):
  for root, _, files in os.walk(dir):
    paths = [os.path.join(root, f) for f in files]
    if len(paths):
      yield os.path.join(target_root, root), paths

setup(name='humbug',
      version=humbug.__version__,
      description='Bindings for the Humbug message API',
      author='Humbug, Inc.',
      author_email='humbug@humbughq.com',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Topic :: Communications :: Chat',
      ],
      url='https://www.zulip.com/dist/api/',
      packages=['humbug'],
      data_files=[('share/humbug/examples', ["examples/humbugrc", "examples/send-message", "examples/subscribe",
                                             "examples/get-public-streams", "examples/unsubscribe",
                                             "examples/list-members", "examples/list-subscriptions",
                                             "examples/print-messages"])] + \
          list(recur_expand('share/humbug', 'integrations/')) + \
          [('share/humbug/demos',
            [os.path.join("demos", relpath) for relpath in
            os.listdir("demos")])],
      scripts=["bin/humbug-send"],
     )

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
from distutils.version import LooseVersion

from ConfigParser import SafeConfigParser


__version__ = "0.1.9"

# Check that we have a recent enough version
# Older versions don't provide the 'json' attribute on responses.
assert(LooseVersion(requests.__version__) >= LooseVersion('0.12.1'))
# In newer versions, the 'json' attribute is a function, not a property
requests_json_is_function = callable(requests.Response.json)

API_VERSTRING = "v1/"

def generate_option_group(parser):
    group = optparse.OptionGroup(parser, 'API configuration')
    group.add_option('--site',
                      default=None,
                      help=optparse.SUPPRESS_HELP)
    group.add_option('--api-key',
                     action='store')
    group.add_option('--user',
                     dest='email',
                     help='Email address of the calling bot or user.')
    group.add_option('--config-file',
                     action='store',
                     help='Location of an ini file containing the\nabove information. (default ~/.humbugrc)')
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
                 site=None, client="API: Python"):
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
            if site is None and config.has_option("api", "site"):
                site = config.get("api", "site")

        self.api_key = api_key
        self.email = email
        self.verbose = verbose
        if site is not None:
            if not site.startswith("http"):
                site = "https://" + site
            self.base_url = site
        else:
            self.base_url = "https://api.zulip.com"
        if self.base_url != "https://api.zulip.com" and not self.base_url.endswith("/api"):
            self.base_url += "/api"
        if not self.base_url.endswith("/"):
            self.base_url += "/"
        self.retry_on_errors = retry_on_errors
        self.client_name = client

    def do_api_query(self, orig_request, url, method="POST", longpolling = False):
        request = {}
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
                            (url.split(API_VERSTRING, 2)[0], error_string,))
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
                if method == "GET":
                    kwarg = "params"
                else:
                    kwarg = "data"
                kwargs = {kwarg: query_state["request"]}
                res = requests.request(
                        method,
                        urlparse.urljoin(self.base_url, url),
                        auth=requests.auth.HTTPBasicAuth(self.email,
                                                         self.api_key),
                        verify=True, timeout=90,
                        **kwargs)

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

            try:
                if requests_json_is_function:
                    json_result = res.json()
                else:
                    json_result = res.json
            except Exception:
                json_result = None

            if json_result is not None:
                end_error_retry(True)
                return json_result
            end_error_retry(False)
            return {'msg': "Unexpected error from the server", "result": "http-error",
                    "status_code": res.status_code}

    @classmethod
    def _register(cls, name, url=None, make_request=(lambda request={}: request),
            method="POST", **query_kwargs):
        if url is None:
            url = name
        def call(self, *args, **kwargs):
            request = make_request(*args, **kwargs)
            return self.do_api_query(request, API_VERSTRING + url, method=method, **query_kwargs)
        call.func_name = name
        setattr(cls, name, call)

    def call_on_each_event(self, callback, event_types=None):
        def do_register():
            while True:
                if event_types is None:
                    res = self.register()
                else:
                    res = self.register(event_types=event_types)

                if 'error' in res.get('result'):
                    if self.verbose:
                        print "Server returned error:\n%s" % res['msg']
                    time.sleep(1)
                else:
                    return (res['queue_id'], res['last_event_id'])

        queue_id = None
        while True:
            if queue_id is None:
                (queue_id, last_event_id) = do_register()

            res = self.get_events(queue_id=queue_id, last_event_id=last_event_id)
            if 'error' in res.get('result'):
                if res["result"] == "http-error":
                    if self.verbose:
                        print "HTTP error fetching events -- probably a server restart"
                elif res["result"] == "connection-error":
                    if self.verbose:
                        print "Connection error fetching events -- probably server is temporarily down?"
                else:
                    if self.verbose:
                        print "Server returned error:\n%s" % res["msg"]
                    if res["msg"].startswith("Bad event queue id:"):
                        # Our event queue went away, probably because
                        # we were asleep or the server restarted
                        # abnormally.  We may have missed some
                        # events while the network was down or
                        # something, but there's not really anything
                        # we can do about it other than resuming
                        # getting new ones.
                        #
                        # Reset queue_id to register a new event queue.
                        queue_id = None
                # TODO: Make this back off once it's more reliable
                time.sleep(1)
                continue

            for event in res['events']:
                last_event_id = max(last_event_id, int(event['id']))
                callback(event)

    def call_on_each_message(self, callback):
        def event_callback(event):
            if event['type'] == 'message':
                callback(event['message'])

        self.call_on_each_event(event_callback, ['message'])

def _mk_subs(streams):
    return {'subscriptions': streams}

def _mk_rm_subs(streams):
    return {'delete': streams}

def _mk_events(event_types=None):
    if event_types is None:
        return dict()
    return dict(event_types=event_types)

Client._register('send_message', url='messages', make_request=(lambda request: request))
Client._register('update_message', method='PATCH', url='messages', make_request=(lambda request: request))
Client._register('get_messages', method='GET', url='messages/latest', longpolling=True)
Client._register('get_events', url='events', method='GET', longpolling=True, make_request=(lambda **kwargs: kwargs))
Client._register('register', make_request=_mk_events)
Client._register('get_profile', method='GET', url='users/me')
Client._register('get_public_streams', method='GET', url='streams')
Client._register('get_members', method='GET', url='users')
Client._register('list_subscriptions', method='GET', url='users/me/subscriptions')
Client._register('add_subscriptions', url='users/me/subscriptions',    make_request=_mk_subs)
Client._register('remove_subscriptions', method='PATCH', url='users/me/subscriptions', make_request=_mk_rm_subs)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright Â© 2013 Humbug, Inc.
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


# Change these values to configure authentication for the plugin
HUMBUG_USER = "svn-bot@example.com"
HUMBUG_API_KEY = "0123456789abcdef0123456789abcdef"

# commit_notice_destination() lets you customize where commit notices
# are sent to with the full power of a Python function.
#
# It takes the following arguments:
# * path   = the path to the svn repository on the server
# * commit = the commit id
#
# Returns a dictionary encoding the stream and subject to send the
# notification to (or None to send no notification).
#
# The default code below will send every commit except for the "master-plan"
# and "secret" repos to
# * stream "commits"
# * subject "deploy => branch_name" (using a pretty unicode right arrow)
def commit_notice_destination(path, commit):
    repo = path.split('/')[-1]
    if repo not in ["evil-master-plan", "my-super-secret-repository"]:
        return dict(stream  = "commits",
                    subject = u"deploy \u21D2 %s" % (repo,))

    # Return None for cases where you don't want a notice sent
    return None

## If properly installed, the Humbug API should be in your import
## path, but if not, set a custom path below
HUMBUG_API_PATH = None

# This should not need to change unless you have a custom Humbug subdomain.
HUMBUG_SITE = "https://api.zulip.com"

# -*- coding: utf-8 -*-
#
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

# See humbug_trac.py for installation and configuration instructions

# Change these constants to configure the plugin:
HUMBUG_USER = "trac-bot@example.com"
HUMBUG_API_KEY = "0123456789abcdef0123456789abcdef"
STREAM_FOR_NOTIFICATIONS = "trac"
TRAC_BASE_TICKET_URL = "https://trac.example.com/ticket"

# Most people find that having every change in Trac result in a
# notification is too noisy -- in particular, when someone goes
# through recategorizing a bunch of tickets, that can often be noisy
# and annoying.  We solve this issue by only sending a notification
# for changes to the fields listed below.
#
# Total list of possible fields is:
# (priority, milestone, cc, owner, keywords, component, severity,
#  type, versions, description, resolution, summary, comment)
#
# The following is the list of fields which can be changed without
# triggering a Humbug notification; change these to match your team's
# workflow.
TRAC_NOTIFY_FIELDS = ["description", "summary", "resolution", "comment",
                      "owner"]

## If properly installed, the Humbug API should be in your import
## path, but if not, set a custom path below
HUMBUG_API_PATH = None

# This should not need to change unless you have a custom Humbug subdomain.
HUMBUG_SITE = "https://api.zulip.com"

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


# Humbug trac plugin -- sends humbugs when tickets change.
#
# Install by copying this file and humbug_trac_config.py to the trac
# plugins/ subdirectory, customizing the constants in
# humbug_trac_config.py, and then adding "humbug_trac" to the
# components section of the conf/trac.ini file, like so:
#
# [components]
# humbug_trac = enabled
#
# You may then need to restart trac (or restart Apache) for the bot
# (or changes to the bot) to actually be loaded by trac.

from trac.core import Component, implements
from trac.ticket import ITicketChangeListener
import sys
import os.path
sys.path.insert(0, os.path.dirname(__file__))
import humbug_trac_config as config

if config.HUMBUG_API_PATH is not None:
    sys.path.append(config.HUMBUG_API_PATH)

import humbug
client = humbug.Client(
    email=config.HUMBUG_USER,
    site=config.HUMBUG_SITE,
    api_key=config.HUMBUG_API_KEY)

def markdown_ticket_url(ticket, heading="ticket"):
    return "[%s #%s](%s/%s)" % (heading, ticket.id, config.TRAC_BASE_TICKET_URL, ticket.id)

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
            "to": config.STREAM_FOR_NOTIFICATIONS,
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
        if not (set(old_values.keys()).intersection(set(config.TRAC_NOTIFY_FIELDS)) or
                (comment and "comment" in set(config.TRAC_NOTIFY_FIELDS))):
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright Â© 2013 Humbug, Inc.
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


# Change these values to configure authentication for the plugin
HUMBUG_USER = "git-bot@example.com"
HUMBUG_API_KEY = "0123456789abcdef0123456789abcdef"

# commit_notice_destination() lets you customize where commit notices
# are sent to with the full power of a Python function.
#
# It takes the following arguments:
# * repo   = the name of the git repository
# * branch = the name of the branch that was pushed to
# * commit = the commit id
#
# Returns a dictionary encoding the stream and subject to send the
# notification to (or None to send no notification).
#
# The default code below will send every commit pushed to "master" to
# * stream "commits"
# * subject "deploy => master" (using a pretty unicode right arrow)
# And similarly for branch "test-post-receive" (for use when testing).
def commit_notice_destination(repo, branch, commit):
    if branch in ["master", "test-post-receive"]:
        return dict(stream  = "commits",
                    subject = u"deploy \u21D2 %s" % (branch,))

    # Return None for cases where you don't want a notice sent
    return None

## If properly installed, the Humbug API should be in your import
## path, but if not, set a custom path below
HUMBUG_API_PATH = None

# This should not need to change unless you have a custom Humbug subdomain.
HUMBUG_SITE = "https://api.zulip.com"

#!/usr/bin/python

import subprocess
import sys
import logging
import dateutil.parser
import pytz
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def run(args, dry_run=False):
    if dry_run:
        print "Would have run: " + " ".join(args)
        return ""

    p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode:
        logger.error("Could not invoke %s\nstdout: %s\nstderror: %s"
                     % (args[0], stdout, stderr))
        sys.exit(1)
    return stdout

# Only run if we're the master
if run(['psql', '-t', '-c', 'select pg_is_in_recovery()']).strip() != 'f':
    sys.exit(0)

run(['env-wal-e', 'backup-push', '/var/lib/postgresql/9.1/main'])

backups = {}
lines = run(['env-wal-e', 'backup-list']).split("\n")
for line in lines[1:]:
    if line:
        backup_name, date, _, _ = line.split()
        backups[dateutil.parser.parse(date)] = backup_name

one_month_ago = datetime.now(tz=pytz.utc) - timedelta(days=30)
for date in sorted(backups.keys(), reverse=True):
    if date < one_month_ago:
        run(['env-wal-e', 'delete', '--confirm', 'before', backups[date]])
        # Because we're going from most recent to least recent, we
        # only have to do one delete operation
        break

from __future__ import absolute_import

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, UserManager, \
    PermissionsMixin
from zephyr.lib.cache import cache_with_key, update_user_profile_cache, \
    user_profile_by_id_cache_key, user_profile_by_email_cache_key, \
    update_user_presence_cache, generic_bulk_cached_fetch
from zephyr.lib.utils import make_safe_digest
from django.db import transaction, IntegrityError
from zephyr.lib import bugdown
from zephyr.lib.avatar import gravatar_hash, avatar_url
from django.utils import timezone
from django.contrib.sessions.models import Session
from zephyr.lib.timestamp import datetime_to_timestamp
from django.db.models.signals import post_save
import zlib

from bitfield import BitField
import pylibmc
import ujson

MAX_SUBJECT_LENGTH = 60
MAX_MESSAGE_LENGTH = 10000

# Doing 1000 memcached requests to get_display_recipient is quite slow,
# so add a local cache as well as the memcached cache.
recipient_cache = {}
def get_display_recipient(recipient):
    if settings.TEST_SUITE:
        # The test suite expects all caching to be turned off
        return get_display_recipient_memcached(recipient)
    if recipient.id not in recipient_cache:
        recipient_cache[recipient.id] = get_display_recipient_memcached(recipient)
    return recipient_cache[recipient.id]

@cache_with_key(lambda self: 'display_recipient_dict:%d' % (self.id,),
                timeout=3600*24*7)
def get_display_recipient_memcached(recipient):
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
                                            .order_by('email'))
    return [{'email': user_profile.email,
             'domain': user_profile.realm.domain,
             'full_name': user_profile.full_name,
             'short_name': user_profile.short_name,
             'id': user_profile.id} for user_profile in user_profile_list]

class Realm(models.Model):
    domain = models.CharField(max_length=40, db_index=True, unique=True)
    restricted_to_domain = models.BooleanField(default=True)

    def __repr__(self):
        return (u"<Realm: %s %s>" % (self.domain, self.id)).encode("utf-8")
    def __str__(self):
        return self.__repr__()

    class Meta:
        permissions = (
            ('administer', "Administer a realm"),
        )

# These functions should only be used on email addresses that have
# been validated via django.core.validators.validate_email
#
# Note that we need to use some care, since can you have multiple @-signs; e.g.
# "tabbott@test"@zulip.com
# is valid email address
def email_to_username(email):
    return "@".join(email.split("@")[:-1])

def email_to_domain(email):
    return email.split("@")[-1]

class UserProfile(AbstractBaseUser, PermissionsMixin):
    # Fields from models.AbstractUser minus last_name and first_name,
    # which we don't use; email is modified to make it indexed and unique.
    email = models.EmailField(blank=False, db_index=True, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_bot = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    bot_owner = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

    USERNAME_FIELD = 'email'
    MAX_NAME_LENGTH = 100

    # Our custom site-specific fields
    full_name = models.CharField(max_length=MAX_NAME_LENGTH)
    short_name = models.CharField(max_length=MAX_NAME_LENGTH)
    pointer = models.IntegerField()
    last_pointer_updater = models.CharField(max_length=64)
    realm = models.ForeignKey(Realm)
    api_key = models.CharField(max_length=32)
    enable_desktop_notifications = models.BooleanField(default=True)
    enable_sounds = models.BooleanField(default=True)
    enter_sends = models.NullBooleanField(default=False)
    enable_offline_email_notifications = models.BooleanField(default=True)
    last_reminder = models.DateTimeField(default=timezone.now, null=True)
    rate_limits = models.CharField(default="", max_length=100) # comma-separated list of range:max pairs

    # Hours to wait before sending another email to a user
    EMAIL_REMINDER_WAITPERIOD = 24

    AVATAR_FROM_GRAVATAR = 'G'
    AVATAR_FROM_USER = 'U'
    AVATAR_FROM_SYSTEM = 'S'
    AVATAR_SOURCES = (
            (AVATAR_FROM_GRAVATAR, 'Hosted by Gravatar'),
            (AVATAR_FROM_USER, 'Uploaded by user'),
            (AVATAR_FROM_SYSTEM, 'System generated'),
    )
    avatar_source = models.CharField(default=AVATAR_FROM_GRAVATAR, choices=AVATAR_SOURCES, max_length=1)

    TUTORIAL_WAITING  = 'W'
    TUTORIAL_STARTED  = 'S'
    TUTORIAL_FINISHED = 'F'
    TUTORIAL_STATES   = ((TUTORIAL_WAITING,  "Waiting"),
                         (TUTORIAL_STARTED,  "Started"),
                         (TUTORIAL_FINISHED, "Finished"))

    tutorial_status = models.CharField(default=TUTORIAL_WAITING, choices=TUTORIAL_STATES, max_length=1)
    # Contains serialized JSON of the form:
    #    [("step 1", true), ("step 2", false)]
    # where the second element of each tuple is if the step has been
    # completed.
    onboarding_steps = models.TextField(default=ujson.dumps([]))

    objects = UserManager()

    def __repr__(self):
        return (u"<UserProfile: %s %s>" % (self.email, self.realm)).encode("utf-8")
    def __str__(self):
        return self.__repr__()

# Make sure we flush the UserProfile object from our memcached
# whenever we save it.
post_save.connect(update_user_profile_cache, sender=UserProfile)

class PreregistrationUser(models.Model):
    email = models.EmailField()
    referred_by = models.ForeignKey(UserProfile, null=True)
    streams = models.ManyToManyField('Stream', null=True)
    invited_at = models.DateTimeField(auto_now=True)

    # status: whether an object has been confirmed.
    #   if confirmed, set to confirmation.settings.STATUS_ACTIVE
    status = models.IntegerField(default=0)

class MitUser(models.Model):
    email = models.EmailField(unique=True)
    # status: whether an object has been confirmed.
    #   if confirmed, set to confirmation.settings.STATUS_ACTIVE
    status = models.IntegerField(default=0)

class Stream(models.Model):
    MAX_NAME_LENGTH = 30
    name = models.CharField(max_length=MAX_NAME_LENGTH, db_index=True)
    realm = models.ForeignKey(Realm, db_index=True)
    invite_only = models.NullBooleanField(default=False)

    def __repr__(self):
        return (u"<Stream: %s>" % (self.name,)).encode("utf-8")
    def __str__(self):
        return self.__repr__()

    def is_public(self):
        # For every realm except for legacy realms on prod (aka those
        # older than realm id 68 with some exceptions), we enable
        # historical messages for all streams that are not invite-only.
        return ((not settings.DEPLOYED or self.realm.domain in
                 ["zulip.com"] or self.realm.id > 68)
                and not self.invite_only)

    class Meta:
        unique_together = ("name", "realm")

    @classmethod
    def create(cls, name, realm):
        stream = cls(name=name, realm=realm)
        stream.save()

        recipient = Recipient.objects.create(type_id=stream.id,
                                             type=Recipient.STREAM)
        return (stream, recipient)

def valid_stream_name(name):
    return name != ""

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
        return (u"<Recipient: %s (%d, %s)>" % (display_recipient, self.type_id, self.type)).encode("utf-8")

class Client(models.Model):
    name = models.CharField(max_length=30, db_index=True, unique=True)

def get_client_cache_key(name):
    return 'get_client:%s' % (make_safe_digest(name),)

@cache_with_key(get_client_cache_key, timeout=3600*24*7)
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

def get_stream_cache_key(stream_name, realm):
    if isinstance(realm, Realm):
        realm_id = realm.id
    else:
        realm_id = realm
    return "stream_by_realm_and_name:%s:%s" % (
        realm_id, make_safe_digest(stream_name.strip().lower()))

# get_stream_backend takes either a realm id or a realm
@cache_with_key(get_stream_cache_key, timeout=3600*24*7)
def get_stream_backend(stream_name, realm):
    if isinstance(realm, Realm):
        realm_id = realm.id
    else:
        realm_id = realm
    return Stream.objects.select_related("realm").get(
        name__iexact=stream_name.strip(), realm_id=realm_id)

# get_stream takes either a realm id or a realm
def get_stream(stream_name, realm):
    try:
        return get_stream_backend(stream_name, realm)
    except Stream.DoesNotExist:
        return None

def bulk_get_streams(realm, stream_names):
    if isinstance(realm, Realm):
        realm_id = realm.id
    else:
        realm_id = realm

    def fetch_streams_by_name(stream_names):
        # This should be just
        #
        # Stream.objects.select_related("realm").filter(name__iexact__in=stream_names,
        #                                               realm_id=realm_id)
        #
        # But chaining __in and __iexact doesn't work with Django's
        # ORM, so we have the following hack to construct the relevant where clause
        if len(stream_names) == 0:
            return []
        upper_list = ", ".join(["UPPER(%s)"] * len(stream_names))
        where_clause = "UPPER(zephyr_stream.name::text) IN (%s)" % (upper_list,)
        return Stream.objects.select_related("realm").filter(realm_id=realm_id).extra(
            where=[where_clause],
            params=stream_names)

    return generic_bulk_cached_fetch(lambda stream_name: get_stream_cache_key(stream_name, realm),
                                     fetch_streams_by_name,
                                     [stream_name.lower() for stream_name in stream_names],
                                     id_fetcher=lambda stream: stream.name.lower())

def get_recipient_cache_key(type, type_id):
    return "get_recipient:%s:%s" % (type, type_id,)

@cache_with_key(get_recipient_cache_key, timeout=3600*24*7)
def get_recipient(type, type_id):
    return Recipient.objects.get(type_id=type_id, type=type)

def bulk_get_recipients(type, type_ids):
    def cache_key_function(type_id):
        return get_recipient_cache_key(type, type_id)
    def query_function(type_ids):
        return Recipient.objects.filter(type=type, type_id__in=type_ids)

    return generic_bulk_cached_fetch(cache_key_function, query_function, type_ids,
                                     id_fetcher=lambda recipient: recipient.type_id)

# NB: This function is currently unused, but may come in handy.
def linebreak(string):
    return string.replace('\n\n', '<p/>').replace('\n', '<br/>')

def extract_message_dict(message_str):
    return ujson.loads(zlib.decompress(message_str))

def stringify_message_dict(message_dict):
    return zlib.compress(ujson.dumps(message_dict))

def to_dict_cache_key_id(message_id, apply_markdown):
    return 'message_dict:%d:%d' % (message_id, apply_markdown)

def to_dict_cache_key(message, apply_markdown):
    return to_dict_cache_key_id(message.id, apply_markdown)

class Message(models.Model):
    sender = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    subject = models.CharField(max_length=MAX_SUBJECT_LENGTH, db_index=True)
    content = models.TextField()
    rendered_content = models.TextField(null=True)
    rendered_content_version = models.IntegerField(null=True)
    pub_date = models.DateTimeField('date published', db_index=True)
    sending_client = models.ForeignKey(Client)
    last_edit_time = models.DateTimeField(null=True)
    edit_history = models.TextField(null=True)

    def __repr__(self):
        display_recipient = get_display_recipient(self.recipient)
        return (u"<Message: %s / %s / %r>" % (display_recipient, self.subject, self.sender)).encode("utf-8")
    def __str__(self):
        return self.__repr__()

    def render_markdown(self, content):
        """Return HTML for given markdown. Bugdown may add properties to the
        message object such as `mentions_user_ids` and `mentions_wildcard`.
        These are only on this Django object and are not saved in the
        database.
        """

        self.mentions_wildcard = False
        self.mentions_user_ids = set()

        return bugdown.convert(content, self.sender.realm.domain, self)

    def set_rendered_content(self, rendered_content, save = False):
        """Set the content on the message.
        """

        self.rendered_content = rendered_content
        self.rendered_content_version = bugdown.version

        if self.rendered_content is not None:
            if save:
                self.save(update_fields=["rendered_content", "rendered_content_version"])
            return True
        else:
            return False

    def maybe_render_content(self, save = False):
        """Render the markdown if there is no existing rendered_content"""
        if self.rendered_content_version < bugdown.version or self.rendered_content is None:
            return self.set_rendered_content(self.render_markdown(self.content), save)
        else:
            return True

    def to_dict(self, apply_markdown):
        return extract_message_dict(self.to_dict_json(apply_markdown))

    @cache_with_key(to_dict_cache_key, timeout=3600*24)
    def to_dict_json(self, apply_markdown):
        return stringify_message_dict(self.to_dict_uncached(apply_markdown))

    def to_dict_uncached(self, apply_markdown):
        display_recipient = get_display_recipient(self.recipient)
        if self.recipient.type == Recipient.STREAM:
            display_type = "stream"
        elif self.recipient.type in (Recipient.HUDDLE, Recipient.PERSONAL):
            display_type = "private"
            if len(display_recipient) == 1:
                # add the sender in if this isn't a message between
                # someone and his self, preserving ordering
                recip = {'email': self.sender.email,
                         'domain': self.sender.realm.domain,
                         'full_name': self.sender.full_name,
                         'short_name': self.sender.short_name,
                         'id': self.sender.id};
                if recip['email'] < display_recipient[0]['email']:
                    display_recipient = [recip, display_recipient[0]]
                elif recip['email'] > display_recipient[0]['email']:
                    display_recipient = [display_recipient[0], recip]
        else:
            display_type = self.recipient.type_name()

        obj = dict(
            id                = self.id,
            sender_email      = self.sender.email,
            sender_full_name  = self.sender.full_name,
            sender_short_name = self.sender.short_name,
            sender_domain     = self.sender.realm.domain,
            sender_id         = self.sender.id,
            type              = display_type,
            display_recipient = display_recipient,
            recipient_id      = self.recipient.id,
            subject           = self.subject,
            timestamp         = datetime_to_timestamp(self.pub_date),
            gravatar_hash     = gravatar_hash(self.sender.email), # Deprecated June 2013
            avatar_url        = avatar_url(self.sender),
            client            = self.sending_client.name)

        obj['subject_links'] = bugdown.subject_links(self.sender.realm.domain.lower(), self.subject)

        if self.last_edit_time != None:
            obj['last_edit_timestamp'] = datetime_to_timestamp(self.last_edit_time)
            obj['edit_history'] = ujson.loads(self.edit_history)

        if apply_markdown:
            self.maybe_render_content(save = True)
            if self.rendered_content is not None:
                obj['content'] = self.rendered_content
            else:
                obj['content'] = '<p>[Zulip note: Sorry, we could not understand the formatting of your message]</p>'

            obj['content_type'] = 'text/html'
        else:
            obj['content'] = self.content
            obj['content_type'] = 'text/x-markdown'

        return obj

    def to_log_dict(self):
        return dict(
            id                = self.id,
            sender_email      = self.sender.email,
            sender_domain     = self.sender.realm.domain,
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
    ALL_FLAGS = ['read', 'starred', 'collapsed', 'mentioned', 'wildcard_mentioned']
    flags = BitField(flags=ALL_FLAGS, default=0)

    class Meta:
        unique_together = ("user_profile", "message")

    def __repr__(self):
        display_recipient = get_display_recipient(self.message.recipient)
        return (u"<UserMessage: %s / %s (%s)>" % (display_recipient, self.user_profile.email, self.flags_list())).encode("utf-8")

    def flags_list(self):
        return [flag for flag in self.flags.keys() if getattr(self.flags, flag).is_set]

def parse_usermessage_flags(val):
    flags = []
    mask = 1
    for flag in UserMessage.ALL_FLAGS:
        if val & mask:
            flags.append(flag)
        mask <<= 1
    return flags

class Subscription(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    active = models.BooleanField(default=True)
    in_home_view = models.NullBooleanField(default=True)

    DEFAULT_STREAM_COLOR = "#c2c2c2"
    color = models.CharField(max_length=10, default=DEFAULT_STREAM_COLOR)
    notifications = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user_profile", "recipient")

    def __repr__(self):
        return (u"<Subscription: %r -> %s>" % (self.user_profile, self.recipient)).encode("utf-8")
    def __str__(self):
        return self.__repr__()

@cache_with_key(user_profile_by_id_cache_key, timeout=3600*24*7)
def get_user_profile_by_id(uid):
    return UserProfile.objects.select_related().get(id=uid)

@cache_with_key(user_profile_by_email_cache_key, timeout=3600*24*7)
def get_user_profile_by_email(email):
    return UserProfile.objects.select_related().get(email__iexact=email)

def get_prereg_user_by_email(email):
    # A user can be invited many times, so only return the result of the latest
    # invite.
    return PreregistrationUser.objects.filter(email__iexact=email).latest("invited_at")

class Huddle(models.Model):
    # TODO: We should consider whether using
    # CommaSeparatedIntegerField would be better.
    huddle_hash = models.CharField(max_length=40, db_index=True, unique=True)

def get_huddle_hash(id_list):
    id_list = sorted(set(id_list))
    hash_key = ",".join(str(x) for x in id_list)
    return make_safe_digest(hash_key)

def huddle_hash_cache_key(huddle_hash):
    return "huddle_by_hash:%s" % (huddle_hash,)

def get_huddle(id_list):
    huddle_hash = get_huddle_hash(id_list)
    return get_huddle_backend(huddle_hash, id_list)

@cache_with_key(lambda huddle_hash, id_list: huddle_hash_cache_key(huddle_hash), timeout=3600*24*7)
def get_huddle_backend(huddle_hash, id_list):
    (huddle, created) = Huddle.objects.get_or_create(huddle_hash=huddle_hash)
    if created:
        with transaction.commit_on_success():
            recipient = Recipient.objects.create(type_id=huddle.id,
                                                 type=Recipient.HUDDLE)
            subs_to_create = [Subscription(recipient=recipient,
                                           user_profile=get_user_profile_by_id(user_profile_id))
                              for user_profile_id in id_list]
            Subscription.objects.bulk_create(subs_to_create)
    return huddle

def get_realm(domain):
    try:
        return Realm.objects.get(domain__iexact=domain.strip())
    except Realm.DoesNotExist:
        return None

def clear_database():
    pylibmc.Client(['127.0.0.1']).flush_all()
    for model in [Message, Stream, UserProfile, Recipient,
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

class UserPresence(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    client = models.ForeignKey(Client)

    # Valid statuses
    ACTIVE = 1
    IDLE = 2

    timestamp = models.DateTimeField('presence changed')
    status = models.PositiveSmallIntegerField(default=ACTIVE)

    def to_dict(self):
        if self.status == UserPresence.ACTIVE:
            presence_val = 'active'
        elif self.status == UserPresence.IDLE:
            presence_val = 'idle'

        return {'client'   : self.client.name,
                'status'   : presence_val,
                'timestamp': datetime_to_timestamp(self.timestamp)}

    @staticmethod
    def status_from_string(status):
        if status == 'active':
            status_val = UserPresence.ACTIVE
        elif status == 'idle':
            status_val = UserPresence.IDLE
        else:
            status_val = None

        return status_val

    class Meta:
        unique_together = ("user_profile", "client")

# Flush the cached user status_dict whenever a user's presence
# changes
post_save.connect(update_user_presence_cache, sender=UserPresence)

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
    DEFAULT_STREAM_COLOR = "#c2c2c2"

    subscription = models.ForeignKey(Subscription)
    color = models.CharField(max_length=10)

import re
from django.contrib.staticfiles.finders import FileSystemFinder

class ExcludeUnminifiedMixin(object):
    """ Excludes unminified copies of our JavaScript code, templates
    and stylesheets, so that these sources don't end up getting served
    in production. """

    def list(self, ignore_patterns):
        # We can't use ignore_patterns because the patterns are
        # applied to just the file part, not the entire path
        excluded = '^(js|styles|templates)/'

        # source-map/ should also not be included.
        # However, we work around that by moving it later,
        # in tools/update-prod-static.

        super_class = super(ExcludeUnminifiedMixin, self)
        for path, storage in super_class.list(ignore_patterns):
            if not re.search(excluded, path):
                yield path, storage

class HumbugFinder(ExcludeUnminifiedMixin, FileSystemFinder):
    pass

from __future__ import absolute_import

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import QueryDict
from django.http.multipartparser import MultiPartParser
from zephyr.models import UserProfile, get_client, get_user_profile_by_email
from zephyr.lib.response import json_error, json_unauthorized
from django.utils.timezone import now
from django.conf import settings
import ujson
from StringIO import StringIO
from zephyr.lib.queue import queue_json_publish
from zephyr.lib.timestamp import datetime_to_timestamp
from zephyr.lib.utils import statsd
from zephyr.exceptions import RateLimited
from zephyr.lib.rate_limiter import incr_ratelimit, is_ratelimited, \
     api_calls_left
from functools import wraps
import base64
import logging
import cProfile

class _RespondAsynchronously(object):
    pass

# Return RespondAsynchronously from an @asynchronous view if the
# response will be provided later by calling handler.humbug_finish(),
# or has already been provided this way. We use this for longpolling
# mode.
RespondAsynchronously = _RespondAsynchronously()

def asynchronous(method):
    @wraps(method)
    def wrapper(request, *args, **kwargs):
        return method(request, handler=request._tornado_handler, *args, **kwargs)
    if getattr(method, 'csrf_exempt', False):
        wrapper.csrf_exempt = True
    return wrapper

def update_user_activity(request, user_profile):
    # update_active_status also pushes to rabbitmq, and it seems
    # redundant to log that here as well.
    if request.META["PATH_INFO"] == '/json/update_active_status':
        return
    event={'type': 'user_activity',
           'query': request.META["PATH_INFO"],
           'user_profile_id': user_profile.id,
           'time': datetime_to_timestamp(now()),
           'client': request.client.name}
    # TODO: It's possible that this should call process_user_activity
    # from zephyr.lib.actions for maximal consistency.
    queue_json_publish("user_activity", event, lambda event: None)

# I like the all-lowercase name better
require_post = require_POST

default_clients = {}

def process_client(request, user_profile, default):
    if 'client' in request.REQUEST:
        request.client = get_client(request.REQUEST['client'])
    else:
        if default not in default_clients:
            default_clients[default] = get_client(default)
        request.client = default_clients[default]

    update_user_activity(request, user_profile)

def validate_api_key(email, api_key):
    try:
        user_profile = get_user_profile_by_email(email)
    except UserProfile.DoesNotExist:
        raise JsonableError("Invalid user: %s" % (email,))
    if api_key != user_profile.api_key:
        raise JsonableError("Invalid API key for user '%s'" % (email,))
    if not user_profile.is_active:
        raise JsonableError("User account is not active")
    return user_profile

# authenticated_api_view will add the authenticated user's user_profile to
# the view function's arguments list, since we have to look it up
# anyway.
def authenticated_api_view(view_func):
    @csrf_exempt
    @require_post
    @has_request_variables
    @wraps(view_func)
    def _wrapped_view_func(request, email=REQ, api_key=REQ('api-key'),
                           *args, **kwargs):
        user_profile = validate_api_key(email, api_key)
        request.user = user_profile
        request._email = user_profile.email
        process_client(request, user_profile, "API")
        # Apply rate limiting
        limited_func = rate_limit()(view_func)
        return limited_func(request, user_profile, *args, **kwargs)
    return _wrapped_view_func

def authenticated_rest_api_view(view_func):
    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        # First try block attempts to get the credentials we need to do authentication
        try:
            # Grab the base64-encoded authentication string, decode it, and split it into
            # the email and API key
            auth_type, encoded_value = request.META['HTTP_AUTHORIZATION'].split()
            # case insensitive per RFC 1945
            if auth_type.lower() != "basic":
                return json_error("Only Basic authentication is supported.")
            email, api_key = base64.b64decode(encoded_value).split(":")
        except ValueError:
            return json_error("Invalid authorization header for basic auth")
        except KeyError:
            return json_unauthorized("Missing authorization header for basic auth")

        # Now we try to do authentication or die
        try:
            user_profile = validate_api_key(email, api_key)
        except JsonableError, e:
            return json_unauthorized(e.error)
        request.user = user_profile
        request._email = user_profile.email
        process_client(request, user_profile, "API")
        # Apply rate limiting
        limited_func = rate_limit()(view_func)
        return limited_func(request, user_profile, *args, **kwargs)
    return _wrapped_view_func

def process_as_post(view_func):
    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        # Adapted from django/http/__init__.py.
        # So by default Django doesn't populate request.POST for anything besides
        # POST requests. We want this dict populated for PATCH/PUT, so we have to
        # do it ourselves.
        #
        # This will not be required in the future, a bug will be filed against
        # Django upstream.

        if not request.POST:
            # Only take action if POST is empty.
            if request.META.get('CONTENT_TYPE', '').startswith('multipart'):
                request.POST = MultiPartParser(request.META, StringIO(request.body),
                        [], request.encoding).parse()[0]
            else:
                request.POST = QueryDict(request.body, encoding=request.encoding)

        return view_func(request, *args, **kwargs)

    return _wrapped_view_func

def authenticate_log_and_execute_json(request, view_func, *args, **kwargs):
    if not request.user.is_authenticated():
        return json_error("Not logged in", status=401)
    user_profile = request.user
    process_client(request, user_profile, "website")
    request._email = user_profile.email
    update_user_activity(request, user_profile)
    return view_func(request, user_profile, *args, **kwargs)

# Checks if the request is a POST request and that the user is logged
# in.  If not, return an error (the @login_required behavior of
# redirecting to a login page doesn't make sense for json views)
def authenticated_json_post_view(view_func):
    @require_post
    @has_request_variables
    @wraps(view_func)
    def _wrapped_view_func(request,
                           *args, **kwargs):
        return authenticate_log_and_execute_json(request, view_func, *args, **kwargs)
    return _wrapped_view_func

def authenticated_json_view(view_func):
    @wraps(view_func)
    def _wrapped_view_func(request,
                           *args, **kwargs):
        return authenticate_log_and_execute_json(request, view_func, *args, **kwargs)
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
        request._email = "internal"
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

class JsonableError(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return self.to_json_error_msg()

    def to_json_error_msg(self):
        return self.error

class RequestVariableMissingError(JsonableError):
    def __init__(self, var_name):
        self.var_name = var_name

    def to_json_error_msg(self):
        return "Missing '%s' argument" % (self.var_name,)

class RequestVariableConversionError(JsonableError):
    def __init__(self, var_name, bad_value):
        self.var_name = var_name
        self.bad_value = bad_value

    def to_json_error_msg(self):
        return "Bad value for '%s': %s" % (self.var_name, self.bad_value)

# Used in conjunction with @has_request_variables, below
class REQ(object):
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
# instance of the REQ class.  That paramter will then be automatically
# populated from the HTTP request.  The request object must be the
# first argument to the decorated function.
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
    if default_param_values is None:
        default_param_values = []

    post_params = []

    for (name, value) in zip(default_param_names, default_param_values):
        if isinstance(value, REQ):
            value.func_var_name = name
            if value.post_var_name is None:
                value.post_var_name = name
            post_params.append(value)
        elif value == REQ:
            # If the function definition does not actually instantiate
            # a REQ object but instead uses the REQ class itself as a
            # value, we instantiate it as a convenience
            post_var = value(name)
            post_var.func_var_name = name
            post_params.append(post_var)

    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        for param in post_params:
            if param.func_var_name in kwargs:
                continue

            default_assigned = False
            try:
                val = request.REQUEST[param.post_var_name]
            except KeyError:
                if param.default is REQ.NotSpecified:
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

def json_to_foo(json, type):
    data = ujson.loads(json)
    if not isinstance(data, type):
        raise ValueError("argument is not a %s" % (type().__class__.__name__))
    return data

def json_to_dict(json):
    return json_to_foo(json, dict)

def json_to_list(json):
    return json_to_foo(json, list)

def json_to_bool(json):
    return json_to_foo(json, bool)

def statsd_increment(counter, val=1):
    """Increments a statsd counter on completion of the
    decorated function.

    Pass the name of the counter to this decorator-returning function."""
    def wrapper(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            ret = func(*args, **kwargs)
            statsd.incr(counter, val)
            return ret
        return wrapped_func
    return wrapper

def rate_limit_user(request, user, domain):
    """Returns whether or not a user was rate limited. Will raise a RateLimited exception
    if the user has been rate limited, otherwise returns and modifies request to contain
    the rate limit information"""

    ratelimited, time = is_ratelimited(user, domain)
    request._ratelimit_applied_limits = True
    request._ratelimit_secs_to_freedom = time
    request._ratelimit_over_limit = ratelimited
    # Abort this request if the user is over her rate limits
    if ratelimited:
        statsd.incr("ratelimiter.limited.%s" % user.id)
        raise RateLimited()

    incr_ratelimit(user, domain)
    calls_remaining, time_reset = api_calls_left(user, domain)

    request._ratelimit_remaining = calls_remaining
    request._ratelimit_secs_to_freedom = time_reset

def rate_limit(domain='all'):
    """Rate-limits a view. Takes an optional 'domain' param if you wish to rate limit different
    types of API calls independently.

    Returns a decorator"""
    def wrapper(func):
        @wraps(func)
        def wrapped_func(request, *args, **kwargs):
            # Don't rate limit requests from Django that come from our own servers,
            # and don't rate-limit dev instances
            no_limits = False
            if request.client and request.client.name.lower() == 'internal' and \
               (request.META['REMOTE_ADDR'] in ['::1', '127.0.0.1'] or settings.DEBUG):
                no_limits = True

            if no_limits:
                return func(request, *args, **kwargs)

            try:
                user = request.user
            except:
                user = None

            # Rate-limiting data is stored in redis
            # We also only support rate-limiting authenticated
            # views right now.
            # TODO(leo) - implement per-IP non-authed rate limiting
            if not settings.RATE_LIMITING or not user:
                if not user:
                    logging.error("Requested rate-limiting on %s but user is not authenticated!" % \
                                     func.__name__)
                return func(request, *args, **kwargs)

            rate_limit_user(request, user, domain)

            return func(request, *args, **kwargs)
        return wrapped_func
    return wrapper

def profiled(func):
    """
    This decorator should obviously be used only in a dev environment.
    It works best when surrounding a function that you expect to be
    called once.  One strategy is to write a test case in zephyr/tests.py
    and wrap the test case with the profiled decorator.

    You can run a single test case like this:

        # edit zephyr/tests.py and place @profiled above the test case below
        ./tools/test-backend zephyr.RateLimitTests.test_ratelimit_decrease

    Then view the results like this:

        ./tools/show-profile-results.py test_ratelimit_decrease.profile

    """
    @wraps(func)
    def wrapped_func(*args, **kwargs):
        fn = func.__name__ + ".profile"
        prof = cProfile.Profile()
        retval = prof.runcall(func, *args, **kwargs)
        prof.dump_stats(fn)
        return retval
    return wrapped_func

from __future__ import absolute_import

from django.conf import settings
from zephyr.models import get_client

from zephyr.decorator import asynchronous, authenticated_api_view, \
    authenticated_json_post_view, internal_notify_view, RespondAsynchronously, \
    has_request_variables, to_non_negative_int, json_to_bool, json_to_list, \
    authenticated_rest_api_view, REQ

from zephyr.lib.response import json_success, json_error
from zephyr.middleware import async_request_restart
from zephyr.tornado_callbacks import \
    get_user_pointer, fetch_stream_messages, fetch_user_messages, \
    add_stream_receive_callback, add_user_receive_callback, \
    add_pointer_update_callback, process_notification

from zephyr.lib.cache_helpers import cache_get_message
from zephyr.lib.event_queue import allocate_client_descriptor, get_client_descriptor

import ujson
import socket

@internal_notify_view
def notify(request):
    process_notification(ujson.loads(request.POST['data']))
    return json_success()

@authenticated_json_post_view
def json_get_updates(request, user_profile):
    return get_updates_backend(request, user_profile,
                               client=request.client, apply_markdown=True)

@authenticated_api_view
def api_get_messages(request, user_profile):
    return get_messages_backend(request, user_profile)

def get_messages_backend(request, user_profile):
    return get_updates_backend(request, user_profile, client=request.client)

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
        ret['server_generation'] = settings.SERVER_GENERATION
    if new_pointer is not None:
        ret['new_pointer'] = new_pointer

    return ret

def return_messages_immediately(user_profile, last,
                                client_server_generation,
                                client_pointer, dont_block,
                                stream_name, **kwargs):
    update_types = []
    new_pointer = None
    if dont_block:
        update_types.append("nonblocking_request")

    if (client_server_generation is not None and
        client_server_generation != settings.SERVER_GENERATION):
        update_types.append("client_reload")

    ptr = get_user_pointer(user_profile.id)
    if (client_pointer is not None and ptr > client_pointer):
        new_pointer = ptr
        update_types.append("pointer_update")

    if last is not None:
        if stream_name is not None:
            message_ids = fetch_stream_messages(user_profile.realm.id, stream_name, last)
        else:
            message_ids = fetch_user_messages(user_profile.id, last)
        messages = map(cache_get_message, message_ids)

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

# Note: We allow any stream name at all here! Validation and
# authorization (is the stream "public") are handled by the caller of
# notify new_message. If a user makes a get_updates request for a
# nonexistent or non-public stream, they won't get an error -- they'll
# just never receive any messages.
@asynchronous
@has_request_variables
def get_updates_backend(request, user_profile, handler=None,
                        last = REQ(converter=to_non_negative_int, default=None),
                        client_server_generation = REQ(whence='server_generation', default=None,
                                                        converter=int),
                        client_pointer = REQ(whence='pointer', converter=int, default=None),
                        dont_block = REQ(converter=json_to_bool, default=False),
                        stream_name = REQ(default=None),
                        apply_markdown = REQ(default=False, converter=json_to_bool),
                        **kwargs):
    resp = return_messages_immediately(user_profile, last,
                                       client_server_generation,
                                       client_pointer,
                                       dont_block, stream_name,
                                       apply_markdown=apply_markdown, **kwargs)
    if resp is not None:
        handler.humbug_finish(resp, request, apply_markdown)

        # We have already invoked handler.humbug_finish(), so we bypass the usual view
        # response path.  We are "responding asynchronously" except that it
        # already happened.  This is slightly weird.
        return RespondAsynchronously

    # Enter long-polling mode.
    #
    # Instead of responding to the client right away, leave our connection open
    # and return to the Tornado main loop.  One of the notify_* views will
    # eventually invoke one of these callbacks, which will send the delayed
    # response.

    def cb(**cb_kwargs):
        async_request_restart(request)
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
                    handler.humbug_finish({"result": "success",
                                           "msg": "",
                                           'update_types': []},
                                          request, apply_markdown)
                    return

            kwargs.update(cb_kwargs)
            res = format_updates_response(user_profile=user_profile,
                                          client_server_generation=client_server_generation,
                                          apply_markdown=apply_markdown,
                                          **kwargs)
            handler.humbug_finish(res, request, apply_markdown)
        except socket.error:
            pass

    if stream_name is not None:
        add_stream_receive_callback(user_profile.realm.id, stream_name, handler.async_callback(cb))
    else:
        add_user_receive_callback(user_profile, handler.async_callback(cb))
    if client_pointer is not None:
        add_pointer_update_callback(user_profile, handler.async_callback(cb))

    # runtornado recognizes this special return value.
    return RespondAsynchronously

@authenticated_json_post_view
def json_get_events(request, user_profile):
    return get_events_backend(request, user_profile, apply_markdown=True)

@asynchronous
@has_request_variables
def get_events_backend(request, user_profile, handler = None,
                       user_client = REQ(converter=get_client, default=None),
                       last_event_id = REQ(converter=int, default=None),
                       queue_id = REQ(default=None),
                       apply_markdown = REQ(default=False, converter=json_to_bool),
                       event_types = REQ(default=None, converter=json_to_list),
                       dont_block = REQ(default=False, converter=json_to_bool)):
    if user_client is None:
        user_client = request.client

    if queue_id is None:
        if dont_block:
            client = allocate_client_descriptor(user_profile.id, event_types,
                                                user_client, apply_markdown)
            queue_id = client.event_queue.id
        else:
            return json_error("Missing 'queue_id' argument")
    else:
        if last_event_id is None:
            return json_error("Missing 'last_event_id' argument")
        client = get_client_descriptor(queue_id)
        if client is None:
            return json_error("Bad event queue id: %s" % (queue_id,))
        if user_profile.id != client.user_profile_id:
            return json_error("You are not authorized to get events from this queue")
        client.event_queue.prune(last_event_id)
        client.disconnect_handler()

    if not client.event_queue.empty() or dont_block:
        return json_success({'events': client.event_queue.contents(),
                             'queue_id': queue_id})

    handler._request = request
    client.connect_handler(handler)

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
from __future__ import absolute_import

import operator

from django.utils     import timezone
from django.db.models import Q
from datetime         import datetime, timedelta
from zephyr.models    import Realm, UserMessage, get_user_profile_by_email

# Each domain has a maximum age for retained messages.
#
# FIXME: Move this into the database.
max_age = {
    'customer1.invalid': timedelta(days=31),
}

domain_cache = {}

def should_expunge_from_log(msg, now):
    """Should a particular log entry be expunged?

       msg: a log entry dict
       now: current time for purposes of determining log entry age"""

    # This function will be called many times, but we want to compare all
    # entries against a consistent "current time".  So the caller passes
    # that time as a parameter.

    if msg.get('type') not in ('stream', 'huddle', 'personal'):
        # Keep all metadata changes like realm_created, subscription_added,
        # etc.
        return False

    user_email = msg['sender_email']
    domain = domain_cache.get(user_email)
    if not domain:
        domain = get_user_profile_by_email(user_email).realm.domain
        domain_cache[user_email] = domain

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

from __future__ import absolute_import

import logging
import traceback
import platform

from django.core import mail
from django.utils.log import AdminEmailHandler
from django.views.debug import ExceptionReporter, get_exception_reporter_filter

def format_record(record):
    """
    Given a Django error LogRecord, format and return the interesting details,
    for use by notification mechanisms like Humbug and e-mail.
    """
    subject = '%s: %s' % (platform.node(), record.getMessage())

    if record.exc_info:
        stack_trace = ''.join(traceback.format_exception(*record.exc_info))
    else:
        stack_trace = 'No stack trace available'

    try:
        user_profile = record.request.user
        user_info = "%s (%s)" % (user_profile.full_name, user_profile.email)
    except Exception:
        # Error was triggered by an anonymous user.
        user_info = "Anonymous user (not logged in)"

    return (subject, stack_trace, user_info)

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
        from zephyr.lib.actions import internal_send_message


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
            request_repr = "Log record message:\n%s" % (record.getMessage(),)

        subject, stack_trace, user_info = format_record(record)

        try:
            internal_send_message("error-bot@zulip.com",
                    "stream", "errors", self.format_subject(subject),
                    "Error generated by %s\n\n~~~~ pytb\n%s\n\n~~~~\n%s" % (
                    user_info, stack_trace, request_repr))
        except:
            # If this breaks, complain loudly but don't pass the traceback up the stream
            # However, we *don't* want to use logging.exception since that could trigger a loop.
            logging.warning("Reporting an exception triggered an exception!", exc_info=True)

    def format_subject(self, subject):
        """
        Escape CR and LF characters, and limit length to MAX_SUBJECT_LENGTH.
        """
        from zephyr.models import MAX_SUBJECT_LENGTH
        formatted_subject = subject.replace('\n', '\\n').replace('\r', '\\r')
        return formatted_subject[:MAX_SUBJECT_LENGTH]

class HumbugAdminEmailHandler(AdminEmailHandler):
    """An exception log handler that emails log entries to site admins.

    If the request is passed as the first argument to the log record,
    request data will be provided in the email report.
    """
    def emit(self, record):
        try:
            request = record.request
            filter = get_exception_reporter_filter(request)
            request_repr = filter.get_request_repr(request)
        except Exception:
            request = None
            request_repr = "Log record message:\n%s" % (record.getMessage(),)

        subject, stack_trace, user_info = format_record(record)
        message = "Error generated by %s\n\n%s\n\n%s" % (user_info, stack_trace,
                                                         request_repr)

        try:
            reporter = ExceptionReporter(request, is_email=True, *record.exc_info)
            html_message = self.include_html and reporter.get_traceback_html() or None
        except Exception:
            html_message = None
        mail.mail_admins(self.format_subject(subject), message, fail_silently=True,
                         html_message=html_message)


from __future__ import absolute_import

from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import SetPasswordForm

from humbug import settings
from zephyr.models import Realm, get_user_profile_by_email, UserProfile
from zephyr.lib.actions import do_change_password

def is_inactive(value):
    try:
        if get_user_profile_by_email(value).is_active:
            raise ValidationError(u'%s is already active' % value)
    except UserProfile.DoesNotExist:
        pass

SIGNUP_STRING = '<a href="https://zulip.com/signup">Sign up</a> to find out when Zulip is ready for you.'

def has_valid_realm(value):
    try:
        Realm.objects.get(domain=value.split("@")[-1])
    except Realm.DoesNotExist:
        raise ValidationError(mark_safe(u'Registration is not currently available for your domain. ' + SIGNUP_STRING))

def isnt_mit(value):
    if "@mit.edu" in value:
        raise ValidationError(mark_safe(u'Zulip for MIT is by invitation only. ' + SIGNUP_STRING))

class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, max_length=100)
    terms = forms.BooleanField(required=True)

class ToSForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    terms = forms.BooleanField(required=True)

class HomepageForm(forms.Form):
    # This form is sort of important, because it determines whether users
    # can register for our product. Be careful when modifying the validators.
    if settings.ALLOW_REGISTER:
        email = forms.EmailField()
    else:
        validators = [has_valid_realm, isnt_mit, is_inactive]
        email = forms.EmailField(validators=validators)

class LoggingSetPasswordForm(SetPasswordForm):
    def save(self, commit=True):
        do_change_password(self.user, self.cleaned_data['new_password1'],
                           log=True, commit=commit)
        return self.user

class CreateBotForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()

from __future__ import absolute_import

from django.conf import settings
import ujson

def add_settings(request):
    return {
        'full_navbar':   settings.FULL_NAVBAR,
    }

def add_metrics(request):
    return {
        'mixpanel_token': settings.MIXPANEL_TOKEN,
        'enable_metrics': ujson.dumps(settings.DEPLOYED),
    }

from django.conf import settings
from django.contrib.staticfiles.storage import CachedFilesMixin, StaticFilesStorage
from pipeline.storage import PipelineMixin

class AddHeaderMixin(object):
    def post_process(self, paths, dry_run=False, **kwargs):
        if dry_run:
            return

        with open(settings.STATIC_HEADER_FILE) as header_file:
            header = header_file.read().decode(settings.FILE_CHARSET)

        # A dictionary of path to tuples of (old_path, new_path,
        # processed).  The return value of this method is the values
        # of this dictionary
        ret_dict = {}

        for name in paths:
            storage, path = paths[name]

            if not path.startswith('min/') or not path.endswith('.css'):
                ret_dict[path] = (path, path, False)
                continue

            # Prepend the header
            with storage.open(path) as orig_file:
                orig_contents = orig_file.read().decode(settings.FILE_CHARSET)

            storage.delete(path)

            with storage.open(path, 'w') as new_file:
                new_file.write(header + orig_contents)

            ret_dict[path] = (path, path, True)

        super_class = super(AddHeaderMixin, self)
        if hasattr(super_class, 'post_process'):
            super_ret = super_class.post_process(paths, dry_run, **kwargs)
        else:
            super_ret = []

        # Merge super class's return value with ours
        for val in super_ret:
            old_path, new_path, processed = val
            if processed:
                ret_dict[old_path] = val

        return ret_dict.itervalues()


class HumbugStorage(PipelineMixin, AddHeaderMixin, CachedFilesMixin,
        StaticFilesStorage):
    pass

from django.core.exceptions import PermissionDenied

class RateLimited(PermissionDenied):
    def __init__(self, msg=""):
        super(RateLimited, self).__init__(msg)

from __future__ import absolute_import

# Defer importing until later to avoid circular imports

def openid_failure_handler(request, message, status=403, template_name=None, exception=None):
    # We ignore template_name in this function

    from django_openid_auth.views import default_render_failure

    return default_render_failure(request, message, status=403, template_name="openid_error.html", exception=None)

from __future__ import absolute_import

from django.views.debug import SafeExceptionReporterFilter
from django.http import build_request_repr

class HumbugExceptionReporterFilter(SafeExceptionReporterFilter):
    def get_post_parameters(self, request):
        filtered_post = SafeExceptionReporterFilter.get_post_parameters(self, request).copy()
        filtered_vars = ['content', 'secret', 'password', 'key', 'api-key', 'subject', 'stream',
                         'subscriptions', 'to', 'csrfmiddlewaretoken']

        for var in filtered_vars:
            if var in filtered_post:
                filtered_post[var] = '**********'
        return filtered_post
    def get_request_repr(self, request):
        if request is None:
            return repr(None)
        else:
            return build_request_repr(request,
                                      POST_override=self.get_post_parameters(request),
                                      COOKIES_override="**********",
                                      META_override="**********")

from __future__ import absolute_import

from django.conf import settings
from zephyr.lib.response import json_error
from django.db import connection
from zephyr.lib.utils import statsd
from zephyr.lib.cache import get_memcached_time, get_memcached_requests
from zephyr.lib.bugdown import get_bugdown_time, get_bugdown_requests
from zephyr.exceptions import RateLimited

import logging
import time

logger = logging.getLogger('humbug.requests')

def async_request_stop(request):
    request._time_stopped = time.time()
    request._memcached_time_stopped = get_memcached_time()
    request._memcached_requests_stopped = get_memcached_requests()
    request._bugdown_time_stopped = get_bugdown_time()
    request._bugdown_requests_stopped = get_bugdown_requests()

def async_request_restart(request):
    request._time_restarted = time.time()
    request._memcached_time_restarted = get_memcached_time()
    request._memcached_requests_restarted = get_memcached_requests()
    request._bugdown_time_restarted = get_bugdown_time()
    request._bugdown_requests_restarted = get_bugdown_requests()

class LogRequests(object):
    def process_request(self, request):
        request._time_started = time.time()
        request._memcached_time_start = get_memcached_time()
        request._memcached_requests_start = get_memcached_requests()
        request._bugdown_time_start = get_bugdown_time()
        request._bugdown_requests_start = get_bugdown_requests()
        connection.queries = []

    def process_response(self, request, response):
        def timedelta_ms(timedelta):
            return timedelta * 1000

        def format_timedelta(timedelta):
            if (timedelta >= 1):
                return "%.1fs" % (timedelta)
            return "%.0fms" % (timedelta_ms(timedelta),)

        # For statsd timer name
        if request.path == '/':
            statsd_path = 'webreq'
        else:
            statsd_path = "webreq.%s" % (request.path[1:].replace('/', '.'),)


        # The reverse proxy might have sent us the real external IP
        remote_ip = request.META.get('HTTP_X_REAL_IP')
        if remote_ip is None:
            remote_ip = request.META['REMOTE_ADDR']

        time_delta = -1
        # A time duration of -1 means the StartLogRequests middleware
        # didn't run for some reason
        optional_orig_delta = ""
        if hasattr(request, '_time_started'):
            time_delta = time.time() - request._time_started
        if hasattr(request, "_time_stopped"):
            orig_time_delta = time_delta
            time_delta = ((request._time_stopped - request._time_started) +
                          (time.time() - request._time_restarted))
            optional_orig_delta = " (lp: %s)" % (format_timedelta(orig_time_delta),)
        memcached_output = ""
        if hasattr(request, '_memcached_time_start'):
            memcached_time_delta = get_memcached_time() - request._memcached_time_start
            memcached_count_delta = get_memcached_requests() - request._memcached_requests_start
            if hasattr(request, "_memcached_requests_stopped"):
                # (now - restarted) + (stopped - start) = (now - start) + (stopped - restarted)
                memcached_time_delta += (request._memcached_time_stopped -
                                         request._memcached_time_restarted)
                memcached_count_delta += (request._memcached_requests_stopped -
                                          request._memcached_requests_restarted)

            if (memcached_time_delta > 0.005):
                memcached_output = " (mem: %s/%s)" % (format_timedelta(memcached_time_delta),
                                                      memcached_count_delta)

            statsd.timing("%s.memcached.time" % (statsd_path,), timedelta_ms(memcached_time_delta))
            statsd.incr("%s.memcached.querycount" % (statsd_path,), memcached_count_delta)

        bugdown_output = ""
        if hasattr(request, '_bugdown_time_start'):
            bugdown_time_delta = get_bugdown_time() - request._bugdown_time_start
            bugdown_count_delta = get_bugdown_requests() - request._bugdown_requests_start
            if hasattr(request, "_bugdown_requests_stopped"):
                # (now - restarted) + (stopped - start) = (now - start) + (stopped - restarted)
                bugdown_time_delta += (request._bugdown_time_stopped -
                                       request._bugdown_time_restarted)
                bugdown_count_delta += (request._bugdown_requests_stopped -
                                        request._bugdown_requests_restarted)

            if (bugdown_time_delta > 0.005):
                bugdown_output = " (md: %s/%s)" % (format_timedelta(bugdown_time_delta),
                                                   bugdown_count_delta)

                statsd.timing("%s.markdown.time" % (statsd_path,), timedelta_ms(bugdown_time_delta))
                statsd.incr("%s.markdown.count" % (statsd_path,), bugdown_count_delta)

        # Get the amount of time spent doing database queries
        db_time_output = ""
        if len(connection.queries) > 0:
            query_time = sum(float(query.get('time', 0)) for query in connection.queries)
            db_time_output = " (db: %s/%sq)" % (format_timedelta(query_time),
                                                len(connection.queries))

            # Log ms, db ms, and num queries to statsd
            statsd.timing("%s.dbtime" % (statsd_path,), timedelta_ms(query_time))
            statsd.incr("%s.dbq" % (statsd_path, ), len(connection.queries))
            statsd.timing("%s.total" % (statsd_path,), timedelta_ms(time_delta))

        # Get the requestor's email address and client, if available.
        try:
            email = request._email
        except Exception:
            email = "unauth"
        try:
            client = request.client.name
        except Exception:
            client = "?"

        logger.info('%-15s %-7s %3d %5s%s%s%s%s %s (%s via %s)' %
                    (remote_ip, request.method, response.status_code,
                     format_timedelta(time_delta), optional_orig_delta,
                     memcached_output, bugdown_output,
                     db_time_output, request.get_full_path(), email, client))

        # Log some additional data whenever we return certain 40x errors
        if 400 <= response.status_code < 500 and response.status_code not in [401, 404, 405]:
            content = response.content
            if len(content) > 100:
                content = "[content more than 100 characters]"
            logger.info('status=%3d, data=%s, uid=%s' % (response.status_code, content, email))

        return response

class JsonErrorHandler(object):
    def process_exception(self, request, exception):
        if hasattr(exception, 'to_json_error_msg') and callable(exception.to_json_error_msg):
            return json_error(exception.to_json_error_msg())
        return None

# Monkeypatch in time tracking to the Django non-debug cursor
# Code comes from CursorDebugWrapper
def wrapper_execute(self, action, sql, params=()):
    self.set_dirty()
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

        from zephyr.lib.rate_limiter import max_api_calls
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

from __future__ import absolute_import

from django.conf import settings
from zephyr.models import Message, UserProfile, UserMessage, \
    Recipient, Stream, get_stream, get_user_profile_by_id

from zephyr.decorator import JsonableError
from zephyr.lib.cache_helpers import cache_get_message
from zephyr.lib.queue import queue_json_publish
from zephyr.lib.event_queue import get_client_descriptors_for_user

import os
import sys
import time
import logging
import requests
import ujson
import subprocess
import collections
from django.db import connection

class Callbacks(object):
    # A user received a message. The key is user_profile.id.
    TYPE_USER_RECEIVE = 0

    # A stream received a message. The key is a tuple
    #   (realm_id, lowercased stream name).
    # See comment attached to the global stream_messages for why.
    # Callers of this callback need to be careful to provide
    # a lowercased stream name.
    TYPE_STREAM_RECEIVE = 1

    # A user's pointer was updated. The key is user_profile.id.
    TYPE_POINTER_UPDATE = 2

    TYPE_MAX = 3

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

callbacks_table = Callbacks()

def add_user_receive_callback(user_profile, cb):
    callbacks_table.add(user_profile.id, Callbacks.TYPE_USER_RECEIVE, cb)

def add_stream_receive_callback(realm_id, stream_name, cb):
    callbacks_table.add((realm_id, stream_name.lower()), Callbacks.TYPE_STREAM_RECEIVE, cb)

def add_pointer_update_callback(user_profile, cb):
    callbacks_table.add(user_profile.id, Callbacks.TYPE_POINTER_UPDATE, cb)

# in-process caching mechanism for tracking usermessages
#
# user table:   Map user_profile_id => [deque of message ids he received]
#
# We don't use all the features of a deque -- the important ones are:
# * O(1) insert of new highest message id
# * O(k) read of highest k message ids
# * Automatic maximum size support.
#
# stream table: Map (realm_id, lowercased stream name) => [deque of message ids it received]
#
# Why don't we index by the stream_id? Because the client will make a
# request that specifies a particular realm and stream name, and since
# we're running within tornado, we don't want to have to do a database
# lookup to find the matching entry in this table.

mtables = {
    'user': {},
    'stream': {},
}

USERMESSAGE_CACHE_COUNT = 25000
STREAMMESSAGE_CACHE_COUNT = 5000
cache_minimum_id = sys.maxint
def initialize_user_messages():
    global cache_minimum_id
    try:
        cache_minimum_id = Message.objects.all().order_by("-id")[0].id - USERMESSAGE_CACHE_COUNT
    except Message.DoesNotExist:
        cache_minimum_id = 1

    # These next few lines implement the following Django ORM
    # algorithm using raw SQL:
    ## for um in UserMessage.objects.filter(message_id__gte=cache_minimum_id).order_by("message"):
    ##     add_user_message(um.user_profile_id, um.message_id)
    # We do this because marshalling the Django objects is very
    # inefficient; total time consumed with the raw SQL is about
    # 600ms, vs. 3000ms-5000ms if we go through the ORM.
    cursor = connection.cursor()
    cursor.execute("SELECT user_profile_id, message_id from zephyr_usermessage " +
                   "where message_id >= %s order by message_id", [cache_minimum_id])
    for row in cursor.fetchall():
        (user_profile_id, message_id) = row
        add_user_message(user_profile_id, message_id)

    streams = {}
    for stream in Stream.objects.select_related().all():
        streams[stream.id] = stream
    for m in (Message.objects.only("id", "recipient").select_related("recipient")
              .filter(id__gte=cache_minimum_id + (USERMESSAGE_CACHE_COUNT - STREAMMESSAGE_CACHE_COUNT),
                      recipient__type=Recipient.STREAM).order_by("id")):
        stream = streams[m.recipient.type_id]
        add_stream_message(stream.realm.id, stream.name, m.id)

    if not settings.DEPLOYED and not settings.TEST_SUITE:
        # Filling the memcached cache is a little slow, so do it in a child process.
        # For DEPLOYED cases, we run this from restart_server.
        subprocess.Popen(["python", os.path.join(os.path.dirname(__file__), "..", "manage.py"),
                          "fill_memcached_caches"])

def add_user_message(user_profile_id, message_id):
    add_table_message("user", user_profile_id, message_id)

def add_stream_message(realm_id, stream_name, message_id):
    add_table_message("stream", (realm_id, stream_name.lower()), message_id)

def add_table_message(table, key, message_id):
    if cache_minimum_id == sys.maxint:
        initialize_user_messages()
    mtables[table].setdefault(key, collections.deque(maxlen=400))
    mtables[table][key].appendleft(message_id)

def fetch_user_messages(user_profile_id, last):
    return fetch_table_messages("user", user_profile_id, last)

def fetch_stream_messages(realm_id, stream_name, last):
    return fetch_table_messages("stream", (realm_id, stream_name.lower()), last)

def fetch_table_messages(table, key, last):
    if cache_minimum_id == sys.maxint:
        initialize_user_messages()

    # We need to initialize the deque here for any new users or
    # streams that were created since Tornado was started
    mtables[table].setdefault(key, collections.deque(maxlen=400))

    # We need to do this check after initialize_user_messages has been called.
    if len(mtables[table][key]) == 0:
        # Since the request contains a value of "last", we can assume
        # that the relevant user or stream has actually received a
        # message, which means that mtabes[table][key] will not remain
        # empty after the below completes.
        #
        # Thus, we will run this code at most once per key (user or
        # stream that is being lurked on).  Further, we only do this
        # query for those keys that have not received a message since
        # cache_minimum_id.  So we can afford to do a database query
        # from Tornado in this case.
        if table == "user":
            logging.info("tornado: Doing database query for user %d" % (key,),)
            for um in reversed(UserMessage.objects.filter(user_profile_id=key).order_by('-message')[:400]):
                add_user_message(um.user_profile_id, um.message_id)
        elif table == "stream":
            logging.info("tornado: Doing database query for stream %s" % (key,))
            (realm_id, stream_name) = key
            stream = get_stream(stream_name, realm_id)
            # If a buggy client submits a "last" value with a nonexistent stream,
            # do nothing (and proceed to longpoll) rather than crashing.
            if stream is not None:
                recipient = Recipient.objects.get(type=Recipient.STREAM, type_id=stream.id)
                for m in Message.objects.only("id", "recipient").filter(recipient=recipient).order_by("id")[:400]:
                    add_stream_message(realm_id, stream_name, m.id)

    if len(mtables[table][key]) == 0:
        # Check the our assumption above that there are messages here.
        # If false, this may just mean a misbehaving client submitted
        # "last" even though it has no messages (in which case we
        # should proceed with longpolling by falling through).  But it
        # could also be a server bug, so we log a warning.
        logging.warning("Unexpected empty message queue for key %s!" % (key,))
    elif last < mtables[table][key][-1]:
        # The user's client has a way-too-old value for 'last'
        # (presumably 400 messages old), we should return an error

        # The error handler for get_updates in zephyr.js parses this
        # message. If you change this message, you must update that
        # error handler.
        raise JsonableError("last value of %d too old!  Minimum valid is %d!" %
                            (last, mtables[table][key][-1]))

    message_list = []
    for message_id in mtables[table][key]:
        if message_id <= last:
            return reversed(message_list)
        message_list.append(message_id)
    return []

# The user receives this message
def user_receive_message(user_profile_id, message):
    add_user_message(user_profile_id, message.id)
    callbacks_table.call(user_profile_id, Callbacks.TYPE_USER_RECEIVE,
                         messages=[message], update_types=["new_messages"])

# The stream receives this message
def stream_receive_message(realm_id, stream_name, message):
    add_stream_message(realm_id, stream_name, message.id)
    callbacks_table.call((realm_id, stream_name.lower()),
                         Callbacks.TYPE_STREAM_RECEIVE,
                         messages=[message], update_types=["new_messages"])

# Simple caching implementation module for user pointers
#
# TODO: Write something generic in cache.py to support this
# functionality?  The current primitives there don't support storing
# to the cache.
user_pointers = {}
def get_user_pointer(user_profile_id):
    if user_pointers == {}:
        # Once, on startup, fill in the user_pointers table with
        # everyone's current pointers
        for u in UserProfile.objects.all():
            user_pointers[u.id] = u.pointer
    if user_profile_id not in user_pointers:
        # This is a new user created since Tornado was started, so
        # they will have an initial pointer of -1.
        return -1
    return user_pointers[user_profile_id]

def set_user_pointer(user_profile_id, pointer):
    user_pointers[user_profile_id] = pointer

def update_pointer(user_profile_id, new_pointer):
    set_user_pointer(user_profile_id, new_pointer)
    callbacks_table.call(user_profile_id, Callbacks.TYPE_POINTER_UPDATE,
                         new_pointer=new_pointer,
                         update_types=["pointer_update"])

    event = dict(type='pointer', pointer=new_pointer)
    for client in get_client_descriptors_for_user(user_profile_id):
        if client.accepts_event_type(event['type']):
            client.add_event(event.copy())


def receives_offline_notifications(user_profile_id):
    user_profile = get_user_profile_by_id(user_profile_id)
    return (user_profile.enable_offline_email_notifications and
            not user_profile.is_bot)

def build_offline_notification_event(user_profile_id, message_id):
    return {"user_profile_id": user_profile_id,
            "message_id": message_id,
            "timestamp": time.time()}

def missedmessage_hook(user_profile_id, queue, last_for_client):
    # Only process missedmessage hook when the last queue for a
    # client has been garbage collected
    if not last_for_client:
        return

    # If a user has gone offline but has unread messages
    # received in the idle time, send them a missed
    # message email
    if not receives_offline_notifications(user_profile_id):
        return

    message_ids = []
    for event in queue.event_queue.contents():
        if not event['type'] == 'message' or not event['flags']:
            continue

        if 'mentioned' in event['flags'] and not 'read' in event['flags']:
            message_ids.append(event['message']['id'])

    for msg_id in message_ids:
        event = build_offline_notification_event(user_profile_id, msg_id)
        queue_json_publish("missedmessage_emails", event, lambda event: None)

def process_new_message(data):
    message = cache_get_message(data['message'])

    message_dict_markdown = message.to_dict(True)
    message_dict_no_markdown = message.to_dict(False)

    for user_data in data['users']:
        user_profile_id = user_data['id']
        flags = user_data.get('flags', [])

        user_receive_message(user_profile_id, message)

        for client in get_client_descriptors_for_user(user_profile_id):
            # The below prevents (Zephyr) mirroring loops.
            if client.accepts_event_type('message') and not \
                    ('mirror' in message.sending_client.name and
                     message.sending_client == client.client_type):
                if client.apply_markdown:
                    message_dict = message_dict_markdown
                else:
                    message_dict = message_dict_no_markdown
                event = dict(type='message', message=message_dict, flags=flags)
                client.add_event(event)

        # If the recipient was offline and the message was a single or group PM to him
        # or she was @-notified potentially notify more immediately
        received_pm = message.recipient.type in (Recipient.PERSONAL, Recipient.HUDDLE) and \
                        user_profile_id != message.sender.id
        mentioned = 'mentioned' in flags
        idle = len(get_client_descriptors_for_user(user_profile_id)) == 0
        if (received_pm or mentioned) and idle:
            if receives_offline_notifications(user_profile_id):
                event = build_offline_notification_event(user_profile_id, message.id)

                # We require RabbitMQ to do this, as we can't call the email handler
                # from the Tornado process. So if there's no rabbitmq support do nothing
                queue_json_publish("missedmessage_emails", event, lambda event: None)

    if 'stream_name' in data:
        stream_receive_message(data['realm_id'], data['stream_name'], message)

def process_event(data):
    event = data['event']
    for user_profile_id in data['users']:
        for client in get_client_descriptors_for_user(user_profile_id):
            if client.accepts_event_type(event['type']):
                client.add_event(event.copy())

def process_notification(data):
    if 'type' not in data:
        # Generic event that doesn't need special handling
        process_event(data)
    elif data['type'] == 'new_message':
        process_new_message(data)
    elif data['type'] == 'pointer_update':
        update_pointer(data['user'], data['new_pointer'])
    else:
        raise JsonableError('bad notification type ' + data['type'])

# Runs in the Django process to send a notification to Tornado.
#
# We use JSON rather than bare form parameters, so that we can represent
# different types and for compatibility with non-HTTP transports.

def send_notification_http(data):
    if settings.TORNADO_SERVER:
        requests.post(settings.TORNADO_SERVER + '/notify_tornado', data=dict(
                data   = ujson.dumps(data),
                secret = settings.SHARED_SECRET))
    else:
        process_notification(data)

def send_notification(data):
    return queue_json_publish("notify_tornado", data, send_notification_http)

from __future__ import absolute_import

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext, loader
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.core import validators
from django.contrib.auth.views import login as django_login_page, \
    logout_then_login as django_logout_then_login
from django.db.models import Q, F
from django.core.mail import send_mail, mail_admins, EmailMessage
from django.db import transaction
from zephyr.models import Message, UserProfile, Stream, Subscription, \
    Recipient, Realm, UserMessage, bulk_get_recipients, \
    PreregistrationUser, get_client, MitUser, UserActivity, \
    MAX_SUBJECT_LENGTH, get_stream, bulk_get_streams, UserPresence, \
    get_recipient, valid_stream_name, to_dict_cache_key, to_dict_cache_key_id, \
    extract_message_dict, stringify_message_dict, parse_usermessage_flags, \
    email_to_domain, email_to_username
from zephyr.lib.actions import do_remove_subscription, bulk_remove_subscriptions, \
    do_change_password, create_mit_user_if_needed, do_change_full_name, \
    do_change_enable_desktop_notifications, do_change_enter_sends, do_change_enable_sounds, \
    do_send_confirmation_email, do_activate_user, do_create_user, check_send_message, \
    do_change_subscription_property, internal_send_message, \
    create_stream_if_needed, gather_subscriptions, subscribed_to_stream, \
    update_user_presence, bulk_add_subscriptions, update_message_flags, \
    recipient_for_emails, extract_recipients, do_events_register, \
    get_status_dict, do_change_enable_offline_email_notifications, \
    do_update_onboarding_steps, do_update_message, internal_prep_message, \
    do_send_messages, do_add_subscription, get_default_subs, do_deactivate, \
    user_email_is_unique, do_invite_users
from zephyr.lib.create_user import random_api_key
from zephyr.forms import RegistrationForm, HomepageForm, ToSForm, CreateBotForm, \
    is_inactive, isnt_mit
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django_openid_auth.views import default_render_failure, login_complete
from openid.consumer.consumer import SUCCESS as openid_SUCCESS
from openid.extensions import ax

from zephyr.decorator import require_post, \
    authenticated_api_view, authenticated_json_post_view, \
    has_request_variables, authenticated_json_view, \
    to_non_negative_int, json_to_dict, json_to_list, json_to_bool, \
    JsonableError, get_user_profile_by_email, \
    authenticated_rest_api_view, process_as_post, REQ, rate_limit_user
from zephyr.lib.query import last_n
from zephyr.lib.avatar import avatar_url
from zephyr.lib.upload import upload_message_image, upload_avatar_image
from zephyr.lib.response import json_success, json_error, json_response, json_method_not_allowed
from zephyr.lib.cache import cache_get_many, cache_set_many, \
    generic_bulk_cached_fetch
from zephyr.lib.unminify import SourceMap
from zephyr.lib.queue import queue_json_publish
from zephyr.lib.utils import statsd
from zephyr import tornado_callbacks
from django.db import connection

from confirmation.models import Confirmation

import subprocess
import datetime
import ujson
import simplejson
import re
import urllib
import os
import base64
import time
import logging
from os import path
from functools import wraps
from collections import defaultdict

from defusedxml.ElementTree import fromstring as xml_fromstring

def list_to_streams(streams_raw, user_profile, autocreate=False, invite_only=False):
    """Converts plaintext stream names to a list of Streams, validating input in the process

    For each stream name, we validate it to ensure it meets our requirements for a proper
    stream name: that is, that it is shorter than 30 characters and passes valid_stream_name.

    We also ensure the stream is visible to the user_profile who made the request; a call
    to list_to_streams will fail if one of the streams is invite_only and user_profile
    is not already on the stream.

    This function in autocreate mode should be atomic: either an exception will be raised
    during a precheck, or all the streams specified will have been created if applicable.

    @param streams_raw The list of stream names to process
    @param user_profile The user for whom we are retreiving the streams
    @param autocreate Whether we should create streams if they don't already exist
    @param invite_only Whether newly created streams should have the invite_only bit set
    """
    streams = []
    # Validate all streams, getting extant ones, then get-or-creating the rest.
    stream_set = set(stream_name.strip() for stream_name in streams_raw)
    rejects = []
    for stream_name in stream_set:
        if len(stream_name) > Stream.MAX_NAME_LENGTH:
            raise JsonableError("Stream name (%s) too long." % (stream_name,))
        if not valid_stream_name(stream_name):
            raise JsonableError("Invalid stream name (%s)." % (stream_name,))

    existing_streams = bulk_get_streams(user_profile.realm, stream_set)

    for stream_name in stream_set:
        stream = existing_streams.get(stream_name.lower())
        if stream is None:
            rejects.append(stream_name)
        else:
            streams.append(stream)
            # Verify we can access the stream.  Note that this part
            # does not use a bulk query, and thus will perform poorly
            # if a user queries a lot of invite-only streams.
            if stream.invite_only and not subscribed_to_stream(user_profile, stream):
                raise JsonableError("Unable to access invite-only stream (%s)." % stream.name)
    if autocreate:
        for stream_name in rejects:
            stream, created = create_stream_if_needed(user_profile.realm,
                                                 stream_name,
                                                 invite_only=invite_only)
            streams.append(stream)
    elif rejects:
        raise JsonableError("Stream(s) (%s) do not exist" % ", ".join(rejects))

    return streams

def send_signup_message(sender, signups_stream, user_profile, internal=False):
    if internal:
        # When this is done using manage.py vs. the web interface
        internal_blurb = " **INTERNAL SIGNUP** "
    else:
        internal_blurb = " "

    internal_send_message(sender,
            "stream", signups_stream, user_profile.realm.domain,
            "%s <`%s`> just signed up for Zulip!%s(total: **%i**)" % (
                user_profile.full_name,
                user_profile.email,
                internal_blurb,
                UserProfile.objects.filter(realm=user_profile.realm,
                                           is_active=True).count(),
                )
            )

def notify_new_user(user_profile, internal=False):
    send_signup_message("new-user-bot@zulip.com", "signups", user_profile, internal)
    statsd.gauge("users.signups.%s" % (user_profile.realm.domain.replace('.', '_')), 1, delta=True)

class PrincipalError(JsonableError):
    def __init__(self, principal):
        self.principal = principal

    def to_json_error_msg(self):
        return ("User not authorized to execute queries on behalf of '%s'"
                % (self.principal,))

def principal_to_user_profile(agent, principal):
    principal_doesnt_exist = False
    try:
        principal_user_profile = get_user_profile_by_email(principal)
    except UserProfile.DoesNotExist:
        principal_doesnt_exist = True

    if (principal_doesnt_exist
        or agent.realm.domain == 'mit.edu'
        or agent.realm != principal_user_profile.realm):
        # We have to make sure we don't leak information about which users
        # are registered for Humbug in a different realm.  We could do
        # something a little more clever and check the domain part of the
        # principal to maybe give a better error message
        raise PrincipalError(principal)

    return principal_user_profile

METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH')

# Import the Tornado REST views that are used by rest_dispatch
from zephyr.tornadoviews import get_events_backend, get_updates_backend

@csrf_exempt
def rest_dispatch(request, **kwargs):
    supported_methods = {}
    # duplicate kwargs so we can mutate the original as we go
    for arg in list(kwargs):
        if arg in METHODS:
            supported_methods[arg] = kwargs[arg]
            del kwargs[arg]
    if request.method in supported_methods.keys():
        target_function = globals()[supported_methods[request.method]]
        # We want to support authentication by both cookies (web client)
        # and API keys (API clients). In the former case, we want to
        # do a check to ensure that CSRF etc is honored, but in the latter
        # we can skip all of that.
        #
        # Security implications of this portion of the code are minimal,
        # as we should worst-case fail closed if we miscategorise a request.
        if request.user.is_authenticated():
            # Authenticated via sessions framework, only CSRF check needed
            target_function = csrf_protect(authenticated_json_view(target_function))
        else:
            # Wrap function with decorator to authenticate the user before
            # proceeding
            target_function = authenticated_rest_api_view(target_function)
        if request.method not in ["GET", "POST"]:
            # process_as_post needs to be the outer decorator, because
            # otherwise we might access and thus cache a value for
            # request.REQUEST.
            target_function = process_as_post(target_function)
        return target_function(request, **kwargs)
    return json_method_not_allowed(supported_methods.keys())

@require_post
@has_request_variables
def beta_signup_submission(request, name=REQ, email=REQ,
                           company=REQ, count=REQ, product=REQ):
    content = """Name: %s
Email: %s
Company: %s
# users: %s
Currently using: %s""" % (name, email, company, count, product,)
    subject = "Interest in Zulip: %s" % (company,)
    from_email = '"%s" <humbug+signups@humbughq.com>' % (name,)
    to_email = '"Zulip Signups" <humbug+signups@humbughq.com>'
    headers = {'Reply-To' : '"%s" <%s>' % (name, email,)}
    msg = EmailMessage(subject, content, from_email, [to_email], headers=headers)
    msg.send()
    return json_success()

@require_post
def accounts_register(request):
    key = request.POST['key']
    confirmation = Confirmation.objects.get(confirmation_key=key)
    prereg_user = confirmation.content_object
    email = prereg_user.email
    mit_beta_user = isinstance(confirmation.content_object, MitUser)

    validators.validate_email(email)
    # If someone invited you, you are joining their realm regardless
    # of your e-mail address.
    #
    # MitUsers can't be referred and don't have a referred_by field.
    if not mit_beta_user and prereg_user.referred_by:
        domain = prereg_user.referred_by.realm.domain
    else:
        domain = email_to_domain(email)

    try:
        if mit_beta_user:
            # MIT users already exist, but are supposed to be inactive.
            is_inactive(email)
        else:
            # Other users should not already exist at all.
            user_email_is_unique(email)
    except ValidationError:
        return HttpResponseRedirect(reverse('django.contrib.auth.views.login') + '?email=' + urllib.quote_plus(email))

    if request.POST.get('from_confirmation'):
        form = RegistrationForm()
    else:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            password   = form.cleaned_data['password']
            full_name  = form.cleaned_data['full_name']
            short_name = email_to_username(email)
            (realm, _) = Realm.objects.get_or_create(domain=domain)
            first_in_realm = len(UserProfile.objects.filter(realm=realm)) == 0

            # FIXME: sanitize email addresses and fullname
            if mit_beta_user:
                user_profile = get_user_profile_by_email(email)
                do_activate_user(user_profile)
                do_change_password(user_profile, password)
                do_change_full_name(user_profile, full_name)
            else:
                user_profile = do_create_user(email, password, realm, full_name, short_name)
                # We want to add the default subs list iff there were no subs
                # specified when the user was invited.
                streams = prereg_user.streams.all()
                if len(streams) == 0:
                    streams = get_default_subs(user_profile)
                for stream in streams:
                    do_add_subscription(user_profile, stream)

                if prereg_user.referred_by is not None:
                    # This is a cross-realm private message.
                    internal_send_message("new-user-bot@zulip.com",
                            "private", prereg_user.referred_by.email, user_profile.realm.domain,
                            "%s <`%s`> accepted your invitation to join Zulip!" % (
                                user_profile.full_name,
                                user_profile.email,
                                )
                            )
            # Mark any other PreregistrationUsers that are STATUS_ACTIVE as inactive
            # so we can find the PreregistrationUser that we are actually working
            # with here
            PreregistrationUser.objects.filter(email=email)             \
                                       .exclude(id=prereg_user.id)      \
                                       .update(status=0)

            notify_new_user(user_profile)
            queue_json_publish(
                    "signups",
                    {
                        'EMAIL': email,
                        'merge_vars': {
                            'NAME': full_name,
                            'REALM': domain,
                            'OPTIN_IP': request.META['REMOTE_ADDR'],
                            'OPTIN_TIME': datetime.datetime.isoformat(datetime.datetime.now()),
                        },
                    },
                    lambda event: None)

            login(request, authenticate(username=email, password=password))

            if first_in_realm:
                return HttpResponseRedirect(reverse('zephyr.views.initial_invite_page'))
            else:
                return HttpResponseRedirect(reverse('zephyr.views.home'))

    return render_to_response('zephyr/register.html',
            {'form': form,
             'company_name': domain,
             'email': email,
             'key': key,
             'gafyd_name': request.POST.get('gafyd_name', False),
            },
        context_instance=RequestContext(request))

@login_required(login_url = settings.HOME_NOT_LOGGED_IN)
def accounts_accept_terms(request):
    email = request.user.email
    domain = email_to_domain(email)
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
                        ["all@zulip.com"])
            do_change_full_name(request.user, full_name)
            return redirect(home)

    else:
        form = ToSForm()
    return render_to_response('zephyr/accounts_accept_terms.html',
        { 'form': form, 'company_name': domain, 'email': email },
        context_instance=RequestContext(request))

def api_endpoint_docs(request):
    raw_calls = open('templates/zephyr/api_content.json', 'r').read()
    calls = ujson.loads(raw_calls)
    langs = set()
    for call in calls:
        for example_type in ('request', 'response'):
            for lang in call.get('example_' + example_type, []):
                langs.add(lang)
    return render_to_response(
            'zephyr/api_endpoints.html', {
                'content': calls,
                'langs': langs,
                },
        context_instance=RequestContext(request))

@authenticated_json_post_view
@has_request_variables
def json_invite_users(request, user_profile, invitee_emails=REQ):
    # Validation
    if settings.ALLOW_REGISTER == False:
        try:
            isnt_mit(user_profile.email)
        except ValidationError:
            return json_error("Invitations are not enabled for MIT at this time.")

    if not invitee_emails:
        return json_error("You must specify at least one email address.")

    invitee_emails = set(re.split(r'[, \n]', invitee_emails))

    stream_names = request.POST.getlist('stream')
    if not stream_names:
        return json_error("You must specify at least one stream for invitees to join.")

    streams = []
    for stream_name in stream_names:
        stream = get_stream(stream_name, user_profile.realm)
        if stream is None:
            return json_error("Stream does not exist: %s. No invites were sent." % stream_name)
        streams.append(stream)

    ret_error, error_data = do_invite_users(user_profile, invitee_emails, streams)

    if ret_error is not None:
        return json_error(data=error_data, msg=ret_error)
    else:
        return json_success()

def handle_openid_errors(request, issue, openid_response=None):
    if issue == "Unknown user":
        if openid_response is not None and openid_response.status == openid_SUCCESS:
            ax_response = ax.FetchResponse.fromSuccessResponse(openid_response)
            google_email = openid_response.getSigned('http://openid.net/srv/ax/1.0', 'value.email')
            full_name = " ".join((
                    ax_response.get('http://axschema.org/namePerson/first')[0],
                    ax_response.get('http://axschema.org/namePerson/last')[0]))
            form = HomepageForm({'email': google_email})
            request.verified_email = None
            if form.is_valid():
                # Construct a PreregistrationUser object and send the user over to
                # the confirmation view.
                prereg_user = PreregistrationUser(email=google_email)
                prereg_user.save()
                return redirect("".join((
                    "/",
                    # Split this so we only get the part after the /
                    Confirmation.objects.get_link_for_object(prereg_user).split("/", 3)[3],
                    '?gafyd_name=',
                    urllib.quote_plus(full_name))))
            else:
                return render_to_response('zephyr/accounts_home.html', {'form': form})
    return default_render_failure(request, issue)

def process_openid_login(request):
    return login_complete(request, render_failure=handle_openid_errors)

def login_page(request, **kwargs):
    template_response = django_login_page(request, **kwargs)
    try:
        template_response.context_data['email'] = request.GET['email']
    except KeyError:
        pass
    return template_response

@authenticated_json_post_view
@has_request_variables
def json_bulk_invite_users(request, user_profile, invitee_emails=REQ(converter=json_to_list)):
    invitee_emails = set(invitee_emails)
    streams = get_default_subs(user_profile)

    ret_error, error_data = do_invite_users(user_profile, invitee_emails, streams)

    if ret_error is not None:
        return json_error(data=error_data, msg=ret_error)
    else:
        return json_success()

@login_required(login_url = settings.HOME_NOT_LOGGED_IN)
def initial_invite_page(request):
    user = request.user
    # Only show the bulk-invite page for the first user in a realm
    domain_count = len(UserProfile.objects.filter(realm=user.realm))
    if domain_count > 1:
        return redirect('zephyr.views.home')

    params = {'company_name': user.realm.domain}

    if (user.realm.restricted_to_domain):
        params['invite_suffix'] = user.realm.domain

    return render_to_response('zephyr/initial_invite_page.html', params,
                              context_instance=RequestContext(request))

@require_post
def logout_then_login(request, **kwargs):
    return django_logout_then_login(request, kwargs)

def accounts_home(request):
    if request.method == 'POST':
        form = HomepageForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            prereg_user = PreregistrationUser(email=email)
            prereg_user.save()
            Confirmation.objects.send_confirmation(prereg_user, email)
            return HttpResponseRedirect(reverse('send_confirm', kwargs={'email': email}))
        try:
            email = request.POST['email']
            # Note: We don't check for uniqueness
            is_inactive(email)
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

    user_profile = request.user

    register_ret = do_events_register(user_profile, get_client("website"),
                                      apply_markdown=True)
    user_has_messages = (register_ret['max_message_id'] != -1)

    # Reset our don't-spam-users-with-email counter since the
    # user has since logged in
    if not user_profile.last_reminder is None:
        user_profile.last_reminder = None
        user_profile.save(update_fields=["last_reminder"])

    # Brand new users get the tutorial
    needs_tutorial = settings.TUTORIAL_ENABLED and \
        user_profile.tutorial_status != UserProfile.TUTORIAL_FINISHED

    if user_profile.pointer == -1 and user_has_messages:
        # Put the new user's pointer at the bottom
        #
        # This improves performance, because we limit backfilling of messages
        # before the pointer.  It's also likely that someone joining an
        # organization is interested in recent messages more than the very
        # first messages on the system.

        user_profile.pointer = register_ret['max_message_id']
        user_profile.last_pointer_updater = request.session.session_key

    # Pass parameters to the client-side JavaScript code.
    # These end up in a global JavaScript Object named 'page_params'.
    page_params = simplejson.encoder.JSONEncoderForHTML().encode(dict(
        debug_mode            = settings.DEBUG,
        poll_timeout          = settings.POLL_TIMEOUT,
        have_initial_messages = user_has_messages,
        stream_list           = register_ret['subscriptions'],
        unsubbed_info         = register_ret['unsubscribed'],
        people_list           = register_ret['realm_users'],
        initial_pointer       = register_ret['pointer'],
        initial_presences     = register_ret['presences'],
        initial_servertime    = time.time(), # Used for calculating relative presence age
        fullname              = user_profile.full_name,
        email                 = user_profile.email,
        domain                = user_profile.realm.domain,
        enter_sends           = user_profile.enter_sends,
        needs_tutorial        = needs_tutorial,
        desktop_notifications_enabled =
            user_profile.enable_desktop_notifications,
        sounds_enabled =
            user_profile.enable_sounds,
        enable_offline_email_notifications =
            user_profile.enable_offline_email_notifications,
        event_queue_id        = register_ret['queue_id'],
        last_event_id         = register_ret['last_event_id'],
        max_message_id        = register_ret['max_message_id'],
        onboarding_steps      = ujson.loads(user_profile.onboarding_steps),
        staging               = settings.STAGING_DEPLOYED or not settings.DEPLOYED
    ))

    statsd.incr('views.home')

    try:
        isnt_mit(user_profile.email)
        show_invites = True
    except ValidationError:
        show_invites = settings.ALLOW_REGISTER

    # For the CUSTOMER4 student realm, only let instructors (who have
    # @customer4.invalid addresses) invite new users.
    if ((user_profile.realm.domain == "users.customer4.invalid") and
        (not user_profile.email.lower().endswith("@customer4.invalid"))):
        show_invites = False

    return render_to_response('zephyr/index.html',
                              {'user_profile': user_profile,
                               'page_params' : page_params,
                               'avatar_url': avatar_url(user_profile),
                               'nofontface': is_buggy_ua(request.META["HTTP_USER_AGENT"]),
                               'show_debug':
                                   settings.DEBUG and ('show_debug' in request.GET),
                               'show_invites': show_invites
                               },
                              context_instance=RequestContext(request))

def is_buggy_ua(agent):
    """Discrimiate CSS served to clients based on User Agent

    Due to QTBUG-3467, @font-face is not supported in QtWebKit.
    This may get fixed in the future, but for right now we can
    just serve the more conservative CSS to all our desktop apps.
    """
    return ("Humbug Desktop/" in agent or "Zulip Desktop/" in agent) and \
        not "Macintosh" in agent

def get_pointer_backend(request, user_profile):
    return json_success({'pointer': user_profile.pointer})

@authenticated_api_view
def api_update_pointer(request, user_profile):
    return update_pointer_backend(request, user_profile)

@authenticated_json_post_view
def json_update_pointer(request, user_profile):
    return update_pointer_backend(request, user_profile)

@has_request_variables
def update_pointer_backend(request, user_profile,
                           pointer=REQ(converter=to_non_negative_int)):
    if pointer <= user_profile.pointer:
        return json_success()

    prev_pointer = user_profile.pointer
    user_profile.pointer = pointer
    user_profile.save(update_fields=["pointer"])

    if request.client.name.lower() in ['android', 'iphone']:
        # TODO (leo)
        # Until we handle the new read counts in the mobile apps natively,
        # this is a shim that will mark as read any messages up until the
        # pointer move
        UserMessage.objects.filter(user_profile=user_profile,
                                   message__id__gt=prev_pointer,
                                   message__id__lte=pointer,
                                   flags=~UserMessage.flags.read)        \
                           .update(flags=F('flags').bitor(UserMessage.flags.read))

    if settings.TORNADO_SERVER:
        tornado_callbacks.send_notification(dict(
            type            = 'pointer_update',
            user            = user_profile.id,
            new_pointer     = pointer))

    return json_success()

@authenticated_json_post_view
def json_get_old_messages(request, user_profile):
    return get_old_messages_backend(request, user_profile)

@authenticated_api_view
@has_request_variables
def api_get_old_messages(request, user_profile,
                         apply_markdown=REQ(default=False,
                                            converter=ujson.loads)):
    return get_old_messages_backend(request, user_profile,
                                    apply_markdown=apply_markdown)

class BadNarrowOperator(Exception):
    def __init__(self, desc):
        self.desc = desc

    def to_json_error_msg(self):
        return 'Invalid narrow operator: ' + self.desc

class NarrowBuilder(object):
    def __init__(self, user_profile, prefix):
        self.user_profile = user_profile
        self.prefix = prefix

    def __call__(self, query, operator, operand):
        # We have to be careful here because we're letting users call a method
        # by name! The prefix 'by_' prevents it from colliding with builtin
        # Python __magic__ stuff.
        method_name = 'by_' + operator.replace('-', '_')
        if method_name == 'by_search':
            return self.do_search(query, operand)
        method = getattr(self, method_name, None)
        if method is None:
            raise BadNarrowOperator('unknown operator ' + operator)
        return query.filter(method(operand))

    # Wrapper for Q() which adds self.prefix to all the keys
    def pQ(self, **kwargs):
        return Q(**dict((self.prefix + key, kwargs[key]) for key in kwargs.keys()))

    def by_is(self, operand):
        if operand == 'private':
            return (self.pQ(recipient__type=Recipient.PERSONAL) |
                    self.pQ(recipient__type=Recipient.HUDDLE))
        elif operand == 'starred':
            return Q(flags=UserMessage.flags.starred)
        elif operand == 'mentioned':
            return Q(flags=UserMessage.flags.mentioned)
        raise BadNarrowOperator("unknown 'is' operand " + operand)

    def by_stream(self, operand):
        stream = get_stream(operand, self.user_profile.realm)
        if stream is None:
            raise BadNarrowOperator('unknown stream ' + operand)

        if self.user_profile.realm.domain == "mit.edu":
            # MIT users expect narrowing to "social" to also show messages to /^(un)*social(.d)*$/
            # (unsocial, ununsocial, social.d, etc)
            m = re.search(r'^(?:un)*(.+?)(?:\.d)*$', stream.name, re.IGNORECASE)
            if m:
                base_stream_name = m.group(1)
            else:
                base_stream_name = stream.name

            matching_streams = Stream.objects.filter(realm=self.user_profile.realm,
                                                     name__iregex=r'^(un)*%s(\.d)*$' % (re.escape(base_stream_name),))
            matching_stream_ids = [matching_stream.id for matching_stream in matching_streams]
            recipients = bulk_get_recipients(Recipient.STREAM, matching_stream_ids).values()
            return self.pQ(recipient__in=recipients)

        recipient = get_recipient(Recipient.STREAM, type_id=stream.id)
        return self.pQ(recipient=recipient)

    def by_topic(self, operand):
        if self.user_profile.realm.domain == "mit.edu":
            # MIT users expect narrowing to topic "foo" to also show messages to /^foo(.d)*$/
            # (foo, foo.d, foo.d.d, etc)
            m = re.search(r'^(.*?)(?:\.d)*$', operand, re.IGNORECASE)
            if m:
                base_topic = m.group(1)
            else:
                base_topic = operand

            # Additionally, MIT users expect the empty instance and
            # instance "personal" to be the same.
            if base_topic in ('', 'personal', '(instance "")'):
                regex = r'^(|personal|\(instance ""\))(\.d)*$'
            else:
                regex = r'^%s(\.d)*$' % (re.escape(base_topic),)

            return self.pQ(subject__iregex=regex)

        return self.pQ(subject__iexact=operand)

    def by_sender(self, operand):
        return self.pQ(sender__email__iexact=operand)

    def by_near(self, operand):
        return Q()

    def by_id(self, operand):
        return self.pQ(id=operand)

    def by_pm_with(self, operand):
        if ',' in operand:
            # Huddle
            try:
                emails = [e.strip() for e in operand.split(',')]
                recipient = recipient_for_emails(emails, False,
                    self.user_profile, self.user_profile)
            except ValidationError:
                raise BadNarrowOperator('unknown recipient ' + operand)
            return self.pQ(recipient=recipient)
        else:
            # Personal message
            self_recipient = get_recipient(Recipient.PERSONAL, type_id=self.user_profile.id)
            if operand == self.user_profile.email:
                # Personals with self
                return self.pQ(recipient__type=Recipient.PERSONAL,
                          sender=self.user_profile, recipient=self_recipient)

            # Personals with other user; include both directions.
            try:
                narrow_profile = get_user_profile_by_email(operand)
            except UserProfile.DoesNotExist:
                raise BadNarrowOperator('unknown user ' + operand)

            narrow_recipient = get_recipient(Recipient.PERSONAL, narrow_profile.id)
            return ((self.pQ(sender=narrow_profile) & self.pQ(recipient=self_recipient)) |
                    (self.pQ(sender=self.user_profile) & self.pQ(recipient=narrow_recipient)))

    def do_search(self, query, operand):
        if "postgres" in settings.DATABASES["default"]["ENGINE"]:
            tsquery = "plainto_tsquery('humbug.english_us_search', %s)"
            where = "search_tsvector @@ " + tsquery
            match_content = "ts_headline('humbug.english_us_search', rendered_content, " \
                + tsquery + ", 'StartSel=\"<span class=\"\"highlight\"\">\", StopSel=</span>, " \
                "HighlightAll=TRUE')"
            # We HTML-escape the subject in Postgres to avoid doing a server round-trip
            match_subject = "ts_headline('humbug.english_us_search', escape_html(subject), " \
                + tsquery + ", 'StartSel=\"<span class=\"\"highlight\"\">\", StopSel=</span>, " \
                "HighlightAll=TRUE')"

            # Do quoted string matching.  We really want phrase
            # search here so we can ignore punctuation and do
            # stemming, but there isn't a standard phrase search
            # mechanism in Postgres
            for term in re.findall('"[^"]+"|\S+', operand):
                if term[0] == '"' and term[-1] == '"':
                    term = term[1:-1]
                    query = query.filter(self.pQ(content__icontains=term) |
                                         self.pQ(subject__icontains=term))

            return query.extra(select={'match_content': match_content,
                                       'match_subject': match_subject},
                               where=[where],
                               select_params=[operand, operand], params=[operand])
        else:
            for word in operand.split():
                query = query.filter(self.pQ(content__icontains=word) |
                                     self.pQ(subject__icontains=word))
            return query


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

def is_public_stream(request, stream, realm):
    if not valid_stream_name(stream):
        raise JsonableError("Invalid stream name")
    stream = get_stream(stream, realm)
    if stream is None:
        return False
    return stream.is_public()

@has_request_variables
def get_old_messages_backend(request, user_profile,
                             anchor = REQ(converter=int),
                             num_before = REQ(converter=to_non_negative_int),
                             num_after = REQ(converter=to_non_negative_int),
                             narrow = REQ('narrow', converter=narrow_parameter, default=None),
                             apply_markdown=REQ(default=True,
                                                converter=ujson.loads)):
    include_history = False
    if narrow is not None:
        for operator, operand in narrow:
            if operator == "stream":
                if is_public_stream(request, operand, user_profile.realm):
                    include_history = True
        # Disable historical messages if the user is narrowing to show
        # only starred messages (or anything else that's a property on
        # the UserMessage table).  There cannot be historical messages
        # in these cases anyway.
        for operator, operand in narrow:
            if operator == "is" and operand == "starred":
                include_history = False

    if include_history:
        prefix = ""
        query = Message.objects.only("id").order_by('id')
    else:
        prefix = "message__"
        # Conceptually this query should be
        #   UserMessage.objects.filter(user_profile=user_profile).order_by('message')
        #
        # However, our do_search code above requires that there be a
        # unique 'rendered_content' row in the query, so we need to
        # somehow get the 'message' table into the query without
        # actually fetching all the rows from the message table (since
        # doing so would cause Django to consume a lot of resources
        # rendering them).  The following achieves these objectives.
        query = UserMessage.objects.select_related("message").only("flags", "id", "message__id") \
            .filter(user_profile=user_profile).order_by('message')

    num_extra_messages = 1
    is_search = False

    if narrow is None:
        use_raw_query = True
    else:
        use_raw_query = False
        num_extra_messages = 0
        build = NarrowBuilder(user_profile, prefix)
        for operator, operand in narrow:
            if operator == 'search':
                is_search = True
            query = build(query, operator, operand)

    def add_prefix(**kwargs):
        return dict((prefix + key, kwargs[key]) for key in kwargs.keys())

    # We add 1 to the number of messages requested if no narrow was
    # specified to ensure that the resulting list always contains the
    # anchor message.  If a narrow was specified, the anchor message
    # might not match the narrow anyway.
    if num_after != 0:
        num_after += num_extra_messages
    else:
        num_before += num_extra_messages

    before_result = []
    after_result = []
    if num_before != 0:
        before_anchor = anchor
        if num_after != 0:
            # Don't include the anchor in both the before query and the after query
            before_anchor = anchor - 1
        if use_raw_query:
            cursor = connection.cursor()
            # These queries should always be the same as what we would do
            # in the !include_history case.
            cursor.execute("SELECT zephyr_message.id, zephyr_usermessage.flags FROM " +
                           "zephyr_usermessage INNER JOIN zephyr_message ON " +
                           "zephyr_message.id = zephyr_usermessage.message_id " +
                           "WHERE zephyr_usermessage.user_profile_id = %s and zephyr_message.id <= %s " +
                           "ORDER BY message_id DESC LIMIT %s", [user_profile.id, before_anchor, num_before])
            before_result = reversed(cursor.fetchall())
        else:
            before_result = last_n(num_before, query.filter(**add_prefix(id__lte=before_anchor)))
    if num_after != 0:
        if use_raw_query:
            cursor = connection.cursor()
            # These queries should always be the same as what we would do
            # in the !include_history case.
            cursor.execute("SELECT zephyr_message.id, zephyr_usermessage.flags FROM " +
                           "zephyr_usermessage INNER JOIN zephyr_message ON " +
                           "zephyr_message.id = zephyr_usermessage.message_id " +
                           "WHERE zephyr_usermessage.user_profile_id = %s and zephyr_message.id >= %s " +
                           "ORDER BY message_id LIMIT %s", [user_profile.id, anchor, num_after])
            after_result = cursor.fetchall()
        else:
            after_result = query.filter(**add_prefix(id__gte=anchor))[:num_after]
    query_result = list(before_result) + list(after_result)

    # The following is a little messy, but ensures that the code paths
    # are similar regardless of the value of include_history.  The
    # 'user_messages' dictionary maps each message to the user's
    # UserMessage object for that message, which we will attach to the
    # rendered message dict before returning it.  We attempt to
    # bulk-fetch rendered message dicts from memcached using the
    # 'messages' list.
    search_fields = dict()
    message_ids = []
    user_message_flags = {}
    if use_raw_query:
        for row in query_result:
            (message_id, flags_val) = row
            user_message_flags[message_id] = parse_usermessage_flags(flags_val)
            message_ids.append(message_id)
    elif include_history:
        user_message_flags = dict((user_message.message_id, user_message.flags_list()) for user_message in
                                  UserMessage.objects.filter(user_profile=user_profile,
                                                             message__in=query_result))
        for message in query_result:
            message_ids.append(message.id)
            if user_message_flags.get(message.id) is None:
                user_message_flags[message.id] = ["read", "historical"]
            if is_search:
                search_fields[message.id] = dict([('match_subject', message.match_subject),
                                                  ('match_content', message.match_content)])
    else:
        user_message_flags = dict((user_message.message_id, user_message.flags_list())
                                  for user_message in query_result)
        for user_message in query_result:
            message_ids.append(user_message.message_id)
            if is_search:
                search_fields[user_message.message_id] = \
                    dict([('match_subject', user_message.match_subject),
                          ('match_content', user_message.match_content)])

    message_dicts = generic_bulk_cached_fetch(lambda message_id: to_dict_cache_key_id(message_id, apply_markdown),
                                              lambda needed_ids: Message.objects.select_related().filter(id__in=needed_ids),
                                              message_ids,
                                              cache_transformer=lambda x: x.to_dict_uncached(apply_markdown),
                                              extractor=extract_message_dict,
                                              setter=stringify_message_dict)

    message_list = []
    for message_id in message_ids:
        msg_dict = message_dicts[message_id]
        msg_dict.update({"flags": user_message_flags[message_id]})
        msg_dict.update(search_fields.get(message_id, {}))
        message_list.append(msg_dict)

    statsd.incr('loaded_old_messages', len(message_list))
    ret = {'messages': message_list,
           "result": "success",
           "msg": ""}
    return json_success(ret)

def generate_client_id():
    return base64.b16encode(os.urandom(16)).lower()

@authenticated_json_post_view
def json_get_profile(request, user_profile):
    return get_profile_backend(request, user_profile)

@authenticated_api_view
def api_get_profile(request, user_profile):
    return get_profile_backend(request, user_profile)

def get_profile_backend(request, user_profile):
    result = dict(pointer        = user_profile.pointer,
                  client_id      = generate_client_id(),
                  max_message_id = -1)

    messages = Message.objects.filter(usermessage__user_profile=user_profile).order_by('-id')[:1]
    if messages:
        result['max_message_id'] = messages[0].id

    return json_success(result)

@authenticated_json_post_view
@has_request_variables
def json_update_flags(request, user_profile, messages=REQ('messages', converter=json_to_list),
                      operation=REQ('op'), flag=REQ('flag'),
                      all=REQ('all', converter=json_to_bool, default=False)):
    update_message_flags(user_profile, operation, flag, messages, all)
    return json_success({'result': 'success',
                         'messages': messages,
                         'msg': ''})

@authenticated_api_view
def api_send_message(request, user_profile):
    return send_message_backend(request, user_profile)

@authenticated_json_post_view
def json_send_message(request, user_profile):
    return send_message_backend(request, user_profile)

@authenticated_json_post_view
@has_request_variables
def json_change_enter_sends(request, user_profile,
                            enter_sends=REQ('enter_sends', json_to_bool)):
    do_change_enter_sends(user_profile, enter_sends)
    return json_success()

@authenticated_json_post_view
@has_request_variables
def json_update_onboarding_steps(request, user_profile,
                                 onboarding_steps=REQ(converter=json_to_list,
                                                      default=[])):
    do_update_onboarding_steps(user_profile, onboarding_steps)
    return json_success()

# Currently tabbott/extra@mit.edu is our only superuser.  TODO: Make
# this a real superuser security check.
def is_super_user_api(request):
    return request.user.is_authenticated() and request.user.email == "tabbott/extra@mit.edu"

def mit_to_mit(user_profile, email):
    # Are the sender and recipient both @mit.edu addresses?
    # We have to handle this specially, inferring the domain from the
    # e-mail address, because the recipient may not existing in Humbug
    # and we may need to make a stub MIT user on the fly.
    try:
        validators.validate_email(email)
    except ValidationError:
        return False

    domain = email_to_domain(email)

    return user_profile.realm.domain == "mit.edu" and domain == "mit.edu"

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
        if not mit_to_mit(user_profile, email):
            return (False, None)

    # Create users for the referenced users, if needed.
    for email in referenced_users:
        create_mit_user_if_needed(user_profile.realm, email)

    sender = get_user_profile_by_email(sender_email)
    return (True, sender)

@authenticated_json_post_view
@has_request_variables
def json_tutorial_status(request, user_profile, status=REQ('status')):
    if status == 'started':
        user_profile.tutorial_status = UserProfile.TUTORIAL_STARTED
    elif status == 'finished':
        user_profile.tutorial_status = UserProfile.TUTORIAL_FINISHED
    user_profile.save(update_fields=["tutorial_status"])

    return json_success()

@authenticated_json_post_view
def json_update_message(request, user_profile):
    return update_message_backend(request, user_profile)

@authenticated_json_post_view
@has_request_variables
def json_fetch_raw_message(request, user_profile,
                           message_id=REQ(converter=to_non_negative_int)):
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return json_error("No such message")

    if message.sender != user_profile:
        return json_error("Message was not sent by you")

    return json_success({"raw_content": message.content})

@has_request_variables
def update_message_backend(request, user_profile,
                           message_id=REQ(converter=to_non_negative_int),
                           subject=REQ(default=None),
                           content=REQ(default=None)):
    if subject is None and content is None:
        return json_error("Nothing to change")
    do_update_message(user_profile, message_id, subject, content)
    return json_success()

# We do not @require_login for send_message_backend, since it is used
# both from the API and the web service.  Code calling
# send_message_backend should either check the API key or check that
# the user is logged in.
@has_request_variables
def send_message_backend(request, user_profile,
                         message_type_name = REQ('type'),
                         message_to = REQ('to', converter=extract_recipients),
                         forged = REQ(default=False),
                         subject_name = REQ('subject', lambda x: x.strip(), None),
                         message_content = REQ('content')):
    client = request.client
    is_super_user = is_super_user_api(request)
    if forged and not is_super_user:
        return json_error("User not authorized for this query")

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

    ret = check_send_message(sender, client, message_type_name, message_to,
                             subject_name, message_content, forged=forged,
                             forged_timestamp = request.POST.get('time'),
                             forwarder_user_profile=user_profile)
    if ret is not None:
        return json_error(ret)
    return json_success()

@authenticated_api_view
def api_get_public_streams(request, user_profile):
    return get_public_streams_backend(request, user_profile)

@authenticated_json_post_view
def json_get_public_streams(request, user_profile):
    return get_public_streams_backend(request, user_profile)

def get_public_streams_backend(request, user_profile):
    if user_profile.realm.domain == "mit.edu" and not is_super_user_api(request):
        return json_error("User not authorized for this query")

    # Only get streams someone is currently subscribed to
    subs_filter = Subscription.objects.filter(active=True).values('recipient_id')
    stream_ids = Recipient.objects.filter(
        type=Recipient.STREAM, id__in=subs_filter).values('type_id')
    streams = sorted({"name": stream.name} for stream in
                     Stream.objects.filter(id__in = stream_ids,
                                           realm=user_profile.realm,
                                           invite_only=False))
    return json_success({"streams": streams})

@authenticated_api_view
def api_list_subscriptions(request, user_profile):
    return list_subscriptions_backend(request, user_profile)

def list_subscriptions_backend(request, user_profile):
    return json_success({"subscriptions": gather_subscriptions(user_profile)[0]})

@authenticated_json_post_view
def json_list_subscriptions(request, user_profile):
    all_subs = gather_subscriptions(user_profile)
    return json_success({"subscriptions": all_subs[0], "unsubscribed": all_subs[1]})

@transaction.commit_on_success
@has_request_variables
def update_subscriptions_backend(request, user_profile,
                                 delete=REQ(converter=json_to_list, default=[]),
                                 add=REQ(converter=json_to_list, default=[])):
    if not add and not delete:
        return json_error('Nothing to do. Specify at least one of "add" or "delete".')

    json_dict = {}
    for method, items in ((add_subscriptions_backend, add), (remove_subscriptions_backend, delete)):
        response = method(request, user_profile, streams_raw=items)
        if response.status_code != 200:
            transaction.rollback()
            return response
        json_dict.update(ujson.loads(response.content))
    return json_success(json_dict)

@authenticated_api_view
def api_remove_subscriptions(request, user_profile):
    return remove_subscriptions_backend(request, user_profile)

@authenticated_json_post_view
def json_remove_subscriptions(request, user_profile):
    return remove_subscriptions_backend(request, user_profile)

@has_request_variables
def remove_subscriptions_backend(request, user_profile,
                                 streams_raw = REQ("subscriptions", json_to_list)):

    streams = list_to_streams(streams_raw, user_profile)

    result = dict(removed=[], not_subscribed=[])
    (removed, not_subscribed) = bulk_remove_subscriptions([user_profile], streams)
    for (subscriber, stream) in removed:
        result["removed"].append(stream.name)
    for (subscriber, stream) in not_subscribed:
        result["not_subscribed"].append(stream.name)

    return json_success(result)

@authenticated_api_view
def api_add_subscriptions(request, user_profile):
    return add_subscriptions_backend(request, user_profile)

@authenticated_json_post_view
def json_add_subscriptions(request, user_profile):
    return add_subscriptions_backend(request, user_profile)

@has_request_variables
def add_subscriptions_backend(request, user_profile,
                              streams_raw = REQ('subscriptions', json_to_list),
                              invite_only = REQ('invite_only', json_to_bool, default=False),
                              principals = REQ('principals', json_to_list, default=None),):

    stream_names = []
    for stream in streams_raw:
        if not isinstance(stream, dict):
            return json_error("Malformed request")
        stream_name = stream["name"].strip()
        if len(stream_name) > Stream.MAX_NAME_LENGTH:
            return json_error("Stream name (%s) too long." % (stream_name,))
        if not valid_stream_name(stream_name):
            return json_error("Invalid stream name (%s)." % (stream_name,))
        stream_names.append(stream_name)

    if principals is not None:
        subscribers = set(principal_to_user_profile(user_profile, principal) for principal in principals)
    else:
        subscribers = [user_profile]

    streams = list_to_streams(stream_names, user_profile, autocreate=True, invite_only=invite_only)

    (subscribed, already_subscribed) = bulk_add_subscriptions(streams, subscribers)

    result = dict(subscribed=defaultdict(list), already_subscribed=defaultdict(list))
    for (subscriber, stream) in subscribed:
        result["subscribed"][subscriber.email].append(stream.name)
    for (subscriber, stream) in already_subscribed:
        result["already_subscribed"][subscriber.email].append(stream.name)

    private_streams = dict((stream.name, stream.invite_only) for stream in streams)

    # Inform the user if someone else subscribed them to stuff
    if principals and result["subscribed"]:
        notifications = []
        for email, subscriptions in result["subscribed"].iteritems():
            if email == user_profile.email:
                # Don't send a Humbug if you invited yourself.
                continue

            if len(subscriptions) == 1:
                msg = ("Hi there!  We thought you'd like to know that %s just "
                       "subscribed you to the%s stream '%s'"
                       % (user_profile.full_name,
                          " **invite-only**" if private_streams[subscriptions[0]] else "",
                          subscriptions[0]))
            else:
                msg = ("Hi there!  We thought you'd like to know that %s just "
                       "subscribed you to the following streams: \n\n"
                       % (user_profile.full_name,))
                for stream in subscriptions:
                    msg += "* %s%s\n" % (
                        stream,
                        " (**invite-only**)" if private_streams[stream] else "")
            msg += "\nYou can see historical content on a non-invite-only stream by narrowing to it."
            notifications.append(internal_prep_message("notification-bot@zulip.com",
                                                       "private", email, "", msg))
        do_send_messages(notifications)

    result["subscribed"] = dict(result["subscribed"])
    result["already_subscribed"] = dict(result["already_subscribed"])
    return json_success(result)

@authenticated_api_view
def api_get_members(request, user_profile):
    return get_members_backend(request, user_profile)

@authenticated_json_post_view
def json_get_members(request, user_profile):
    return get_members_backend(request, user_profile)

def get_members_backend(request, user_profile):
    members = [{"full_name": profile.full_name,
                "email": profile.email} for profile in \
                   UserProfile.objects.select_related().filter(realm=user_profile.realm)]
    return json_success({'members': members})

@authenticated_api_view
def api_get_subscribers(request, user_profile):
    return get_subscribers_backend(request, user_profile)

@authenticated_json_post_view
def json_get_subscribers(request, user_profile):
    return get_subscribers_backend(request, user_profile)

@authenticated_json_post_view
def json_upload_file(request, user_profile):
    if len(request.FILES) == 0:
        return json_error("You must specify a file to upload")
    if len(request.FILES) != 1:
        return json_error("You may only upload one file at a time")

    user_file = request.FILES.values()[0]
    uri = upload_message_image(request, user_file, user_profile)
    return json_success({'uri': uri})

@has_request_variables
def get_subscribers_backend(request, user_profile, stream_name=REQ('stream')):
    if user_profile.realm.domain == "mit.edu":
        return json_error("You cannot get subscribers in this realm")

    stream = get_stream(stream_name, user_profile.realm)
    if stream is None:
        return json_error("Stream does not exist: %s" % stream_name)

    if stream.invite_only and not subscribed_to_stream(user_profile, stream):
        return json_error("Unable to retrieve subscribers for invite-only stream")

    subscriptions = Subscription.objects.filter(recipient__type=Recipient.STREAM,
                                                recipient__type_id=stream.id,
                                                active=True).select_related()

    return json_success({'subscribers': [subscription.user_profile.email
                                         for subscription in subscriptions]})

@authenticated_json_post_view
@has_request_variables
def json_change_settings(request, user_profile, full_name=REQ,
                         old_password=REQ, new_password=REQ,
                         confirm_password=REQ,
                         # enable_desktop_notification needs to default to False
                         # because browsers POST nothing for an unchecked checkbox
                         enable_desktop_notifications=REQ(converter=lambda x: x == "on",
                                                          default=False),
                         enable_sounds=REQ(converter=lambda x: x == "on",
                                                          default=False),
                         enable_offline_email_notifications=REQ(converter=lambda x: x == "on",
                                                                default=False)):
    if new_password != "" or confirm_password != "":
        if new_password != confirm_password:
            return json_error("New password must match confirmation password!")
        if not authenticate(username=user_profile.email, password=old_password):
            return json_error("Wrong password!")
        do_change_password(user_profile, new_password)

    result = {}
    if user_profile.full_name != full_name and full_name.strip() != "":
        new_full_name = full_name.strip()
        if len(new_full_name) > UserProfile.MAX_NAME_LENGTH:
            return json_error("Name too long!")
        do_change_full_name(user_profile, new_full_name)
        result['full_name'] = new_full_name

    if user_profile.enable_desktop_notifications != enable_desktop_notifications:
        do_change_enable_desktop_notifications(user_profile, enable_desktop_notifications)
        result['enable_desktop_notifications'] = enable_desktop_notifications

    if user_profile.enable_sounds != enable_sounds:
        do_change_enable_sounds(user_profile, enable_sounds)
        result['enable_sounds'] = enable_sounds

    if user_profile.enable_offline_email_notifications != enable_offline_email_notifications:
        do_change_enable_offline_email_notifications(user_profile, enable_offline_email_notifications)
        result['enable_offline_email_notifications'] = enable_offline_email_notifications

    return json_success(result)

@authenticated_json_post_view
@has_request_variables
def json_stream_exists(request, user_profile, stream=REQ):
    return stream_exists_backend(request, user_profile, stream)

def stream_exists_backend(request, user_profile, stream_name):
    if not valid_stream_name(stream_name):
        return json_error("Invalid characters in stream name")
    stream = get_stream(stream_name, user_profile.realm)
    result = {"exists": bool(stream)}
    if stream is not None:
        recipient = get_recipient(Recipient.STREAM, stream.id)
        result["subscribed"] = Subscription.objects.filter(user_profile=user_profile,
                                                           recipient=recipient,
                                                           active=True).exists()
        return json_success(result) # results are ignored for HEAD requests
    return json_response(data=result, status=404)

def get_subscription_or_die(stream_name, user_profile):
    stream = get_stream(stream_name, user_profile.realm)
    if not stream:
        raise JsonableError("Invalid stream %s" % (stream.name,))
    recipient = get_recipient(Recipient.STREAM, stream.id)
    subscription = Subscription.objects.filter(user_profile=user_profile,
                                               recipient=recipient, active=True)

    if not subscription.exists():
        raise JsonableError("Not subscribed to stream %s" % (stream_name,))

    return subscription

@authenticated_json_view
@has_request_variables
def json_subscription_property(request, user_profile, stream_name=REQ,
                               property=REQ):
    """
    This is the entry point to accessing or changing subscription
    properties.
    """
    property_converters = dict(color=lambda x: x,
                               in_home_view=json_to_bool,
                               notifications=json_to_bool)
    if property not in property_converters:
        return json_error("Unknown subscription property: %s" % (property,))

    sub = get_subscription_or_die(stream_name, user_profile)[0]
    if request.method == "GET":
        return json_success({'stream_name': stream_name,
                             'value': getattr(sub, property)})
    elif request.method == "POST":
        @has_request_variables
        def do_set_property(request,
                            value=REQ(converter=property_converters[property])):
            do_change_subscription_property(user_profile, sub, stream_name,
                                            property, value)
        do_set_property(request)
        return json_success()
    else:
        return json_error("Invalid verb")

@csrf_exempt
@require_post
@has_request_variables
def api_fetch_api_key(request, username=REQ, password=REQ):
    user_profile = authenticate(username=username, password=password)
    if user_profile is None:
        return json_error("Your username or password is incorrect.", status=403)
    if not user_profile.is_active:
        return json_error("Your account has been disabled.", status=403)
    return json_success({"api_key": user_profile.api_key})

@authenticated_json_post_view
@has_request_variables
def json_fetch_api_key(request, user_profile, password=REQ):
    if not user_profile.check_password(password):
        return json_error("Your username or password is incorrect.")
    return json_success({"api_key": user_profile.api_key})

class ActivityTable(object):
    def __init__(self, client_name, queries, default_tab=False):
        self.default_tab = default_tab
        self.has_pointer = False
        self.rows = {}

        def do_url(query_name, url):
            for record in UserActivity.objects.filter(
                    query=url,
                    client__name__startswith=client_name).select_related():
                row = self.rows.setdefault(record.user_profile.email,
                                           {'realm': record.user_profile.realm.domain,
                                            'full_name': record.user_profile.full_name,
                                            'email': record.user_profile.email})
                row[query_name + '_count'] = record.count
                row[query_name + '_last' ] = record.last_visit

        for query_name, urls in queries:
            if 'pointer' in query_name:
                self.has_pointer = True
            for url in urls:
                do_url(query_name, url)

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
    return request.user.realm.domain == 'zulip.com'

@login_required(login_url = settings.HOME_NOT_LOGGED_IN)
def get_activity(request):
    if not can_view_activity(request):
        return HttpResponseRedirect(reverse('zephyr.views.login_page'))

    web_queries = (
        ("get_updates",    ["/json/get_updates", "/json/get_events"]),
        ("send_message",   ["/json/send_message"]),
        ("update_pointer", ["/json/update_pointer"]),
    )

    api_queries = (
        ("get_updates",  ["/api/v1/get_messages", "/api/v1/messages/latest", "/api/v1/events"]),
        ("send_message", ["/api/v1/send_message"]),
    )

    return render_to_response('zephyr/activity.html',
        { 'data': {
            'Website': ActivityTable('website',       web_queries, default_tab=True),
            'Mirror':  ActivityTable('zephyr_mirror', api_queries),
            'API':     ActivityTable('API',           api_queries),
            'Android': ActivityTable('Android',       api_queries),
            'iPhone':  ActivityTable('iPhone',        api_queries)
        }}, context_instance=RequestContext(request))

def build_message_from_gitlog(user_profile, name, ref, commits, before, after, url, pusher):
    short_ref = re.sub(r'^refs/heads/', '', ref)
    subject = name

    if re.match(r'^0+$', after):
        content = "%s deleted branch %s" % (pusher,
                                            short_ref)
    elif len(commits) == 0:
        content = ("%s [force pushed](%s) to branch %s.  Head is now %s"
                   % (pusher,
                      url,
                      short_ref,
                      after[:7]))
    else:
        content = ("%s [pushed](%s) to branch %s\n\n"
                   % (pusher,
                      url,
                      short_ref))
        num_commits = len(commits)
        max_commits = 10
        truncated_commits = commits[:max_commits]
        for commit in truncated_commits:
            short_id = commit['id'][:7]
            (short_commit_msg, _, _) = commit['message'].partition("\n")
            content += "* [%s](%s): %s\n" % (short_id, commit['url'],
                                             short_commit_msg)
        if (num_commits > max_commits):
            content += ("\n[and %d more commits]"
                        % (num_commits - max_commits,))

    return (subject, content)

@authenticated_api_view
@has_request_variables
def api_github_landing(request, user_profile, event=REQ,
                       payload=REQ(converter=json_to_dict),
                       branches=REQ(default=''),
                       stream=REQ(default='')):
    # TODO: this should all be moved to an external bot
    repository = payload['repository']

    if not stream:
        stream = 'commits'

    # CUSTOMER18 has requested not to get pull request notifications
    if event == 'pull_request' and user_profile.realm.domain not in ['customer18.invalid', 'zulip.com']:
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
        # This is a bit hackish, but is basically so that CUSTOMER18 doesn't
        # get spammed when people commit to non-master all over the place.
        # Long-term, this will be replaced by some GitHub configuration
        # option of which branches to notify on.
        if short_ref != 'master' and user_profile.realm.domain in ['customer18.invalid', 'zulip.com']:
            return json_success()

        if branches:
            # If we are given a whitelist of branches, then we silently ignore
            # any push notification on a branch that is not in our whitelist.
            if short_ref not in re.split('[\s,;|]+', branches):
                return json_success()


        subject, content = build_message_from_gitlog(user_profile, repository['name'],
                                                     payload['ref'], payload['commits'],
                                                     payload['before'], payload['after'],
                                                     payload['compare'],
                                                     payload['pusher']['name'])
    else:
        # We don't handle other events even though we get notified
        # about them
        return json_success()

    subject = elide_subject(subject)

    request.client = get_client("github_bot")
    return send_message_backend(request, user_profile,
                                message_type_name="stream",
                                message_to=[stream],
                                forged=False, subject_name=subject,
                                message_content=content)

def elide_subject(subject):
    if len(subject) > MAX_SUBJECT_LENGTH:
        subject = subject[:57].rstrip() + '...'
    return subject

@csrf_exempt
def api_jira_webhook(request):
    try:
        api_key = request.GET['api_key']
    except (AttributeError, KeyError):
        return json_error("Missing api_key parameter.")

    try:
        payload = ujson.loads(request.body)
    except ValueError:
        return json_error("Malformed JSON input")

    try:
        stream = request.GET['stream']
    except (AttributeError, KeyError):
        stream = 'jira'

    try:
        user_profile = UserProfile.objects.get(api_key=api_key)
        request.user = user_profile
    except UserProfile.DoesNotExist:
        return json_error("Failed to find user with API key: %s" % (api_key,))

    rate_limit_user(request, user_profile, domain='all')

    def get_in(payload, keys, default=''):
        try:
            for key in keys:
                payload = payload[key]
        except (AttributeError, KeyError):
            return default
        return payload

    event = payload.get('webhookEvent')
    author = get_in(payload, ['user', 'displayName'])
    issueId = get_in(payload, ['issue', 'key'])
    # Guess the URL as it is not specified in the payload
    # We assume that there is a /browse/BUG-### page
    # from the REST url of the issue itself
    baseUrl = re.match("(.*)\/rest\/api/.*", get_in(payload, ['issue', 'self']))
    if baseUrl and len(baseUrl.groups()):
        issue = "[%s](%s/browse/%s)" % (issueId, baseUrl.group(1), issueId)
    else:
        issue = issueId
    title = get_in(payload, ['issue', 'fields', 'summary'])
    priority = get_in(payload, ['issue', 'fields', 'priority', 'name'])
    assignee = get_in(payload, ['assignee', 'displayName'], 'no one')
    subject = "%s: %s" % (issueId, title)

    if event == 'jira:issue_created':
        content = "%s **created** %s priority %s, assigned to **%s**:\n\n> %s" % \
                  (author, issue, priority, assignee, title)
    elif event == 'jira:issue_deleted':
        content = "%s **deleted** %s!" % \
                  (author, issue)
    elif event == 'jira:issue_updated':
        # Reassigned, commented, reopened, and resolved events are all bundled
        # into this one 'updated' event type, so we try to extract the meaningful
        # event that happened
        content = "%s **updated** %s:\n\n" % (author, issue)
        changelog = get_in(payload, ['changelog',])
        comment = get_in(payload, ['comment', 'body'])

        if changelog != '':
            # Use the changelog to display the changes, whitelist types we accept
            items = changelog.get('items')
            for item in items:
                field = item.get('field')
                if field in ('status', 'assignee'):
                    content += "* Changed %s from **%s** to **%s**\n" % (field, item.get('fromString'), item.get('toString'))

        if comment != '':
            content += "\n> %s" % (comment,)
    elif 'transition' in payload:
        from_status = get_in(payload, ['transition', 'from_status'])
        to_status = get_in(payload, ['transition', 'to_status'])
        content = "%s **transitioned** %s from %s to %s" % (author, issue, from_status, to_status)
    else:
        # Unknown event type
        if not settings.TEST_SUITE:
            logging.warning("Got JIRA event type we don't understand: %s" % (event,))
        return json_error("Unknown JIRA event type")

    subject = elide_subject(subject)

    ret = check_send_message(user_profile, get_client("API"), "stream", [stream], subject, content)
    if ret is not None:
        return json_error(ret)
    return json_success()

@csrf_exempt
def api_pivotal_webhook(request):
    try:
        api_key = request.GET['api_key']
        stream = request.GET['stream']
    except (AttributeError, KeyError):
        return json_error("Missing api_key or stream parameter.")

    try:
        user_profile = UserProfile.objects.get(api_key=api_key)
        request.user = user_profile
    except UserProfile.DoesNotExist:
        return json_error("Failed to find user with API key: %s" % (api_key,))

    rate_limit_user(request, user_profile, domain='all')

    payload = xml_fromstring(request.body)

    def get_text(attrs):
        start = payload
        try:
            for attr in attrs:
                start = start.find(attr)
            return start.text
        except AttributeError:
            return ""

    try:
        event_type = payload.find('event_type').text
        description = payload.find('description').text
        project_id = payload.find('project_id').text
        story_id = get_text(['stories', 'story', 'id'])
        # Ugh, the URL in the XML data is not a clickable url that works for the user
        # so we try to build one that the user can actually click on
        url = "https://www.pivotaltracker.com/s/projects/%s/stories/%s" % (project_id, story_id)

        # Pivotal doesn't tell us the name of the story, but it's usually in the
        # description in quotes as the first quoted string
        name_re = re.compile(r'[^"]+"([^"]+)".*')
        match = name_re.match(description)
        if match and len(match.groups()):
            name = match.group(1)
        else:
            name = "Story changed" # Failed for an unknown reason, show something
        more_info = " [(view)](%s)" % (url,)

        if event_type == 'story_update':
            subject = name
            content = description + more_info
        elif event_type == 'note_create':
            subject = "Comment added"
            content = description +  more_info
        elif event_type == 'story_create':
            issue_desc = get_text(['stories', 'story', 'description'])
            issue_type = get_text(['stories', 'story', 'story_type'])
            issue_status = get_text(['stories', 'story', 'current_state'])
            estimate = get_text(['stories', 'story', 'estimate'])
            if estimate != '':
                estimate = " worth %s story points" % (estimate,)
            subject = name
            content = "%s (%s %s%s):\n\n> %s\n\n%s" % (description,
                                                       issue_status,
                                                       issue_type,
                                                       estimate,
                                                       issue_desc,
                                                       more_info)

    except AttributeError:
        return json_error("Failed to extract data from Pivotal XML response")

    subject = elide_subject(subject)

    ret = check_send_message(user_profile, get_client("API"), "stream", [stream], subject, content)
    if ret is not None:
        return json_error(ret)
    return json_success()

# Beanstalk's web hook UI rejects url with a @ in the username section of a url
# So we ask the user to replace them with %40
# We manually fix the username here before passing it along to @authenticated_rest_api_view
def beanstalk_decoder(view_func):
    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        try:
            auth_type, encoded_value = request.META['HTTP_AUTHORIZATION'].split()
            if auth_type.lower() == "basic":
                email, api_key = base64.b64decode(encoded_value).split(":")
                email = email.replace('%40', '@')
                request.META['HTTP_AUTHORIZATION'] = "Basic %s" % (base64.b64encode("%s:%s" % (email, api_key)))
        except:
            pass

        return view_func(request, *args, **kwargs)

    return _wrapped_view_func

@csrf_exempt
@beanstalk_decoder
@authenticated_rest_api_view
@has_request_variables
def api_beanstalk_webhook(request, user_profile,
                          payload=REQ(converter=json_to_dict)):
    # Beanstalk supports both SVN and git repositories
    # We distinguish between the two by checking for a
    # 'uri' key that is only present for git repos
    git_repo = 'uri' in payload
    if git_repo:
        # To get a linkable url,
        subject, content = build_message_from_gitlog(user_profile, payload['repository']['name'],
                                                     payload['ref'], payload['commits'],
                                                     payload['before'], payload['after'],
                                                     payload['repository']['url'],
                                                     payload['pusher_name'])
    else:
        author = payload.get('author_full_name')
        url = payload.get('changeset_url')
        revision = payload.get('revision')
        (short_commit_msg, _, _) = payload.get('message').partition("\n")

        subject = "svn r%s" % (revision,)
        content = "%s pushed [revision %s](%s):\n\n> %s" % (author, revision, url, short_commit_msg)

    subject = elide_subject(subject)

    ret = check_send_message(user_profile, get_client("API"), "stream", ["commits"], subject, content)
    if ret is not None:
        return json_error(ret)
    return json_success()

@csrf_exempt
@has_request_variables
def api_newrelic_webhook(request, alert=REQ(converter=json_to_dict, default=None),
                             deployment=REQ(converter=json_to_dict, default=None)):
    try:
        api_key = request.GET['api_key']
        stream = request.GET['stream']
    except (AttributeError, KeyError):
        return json_error("Missing api_key or stream parameter.")

    try:
        user_profile = UserProfile.objects.get(api_key=api_key)
        request.user = user_profile
    except UserProfile.DoesNotExist:
        return json_error("Failed to find user with API key: %s" % (api_key,))

    rate_limit_user(request, user_profile, domain='all')

    if alert:
        # Use the message as the subject because it stays the same for
        # "opened", "acknowledged", and "closed" messages that should be
        # grouped.
        subject = alert['message']
        content = "%(long_description)s\n[View alert](%(alert_url)s)" % (alert)
    elif deployment:
        subject = "%s deploy" % (deployment['application_name'])
        content = """`%(revision)s` deployed by **%(deployed_by)s**
%(description)s

%(changelog)s""" % (deployment)
    else:
        return json_error("Unknown webhook request")

    subject = elide_subject(subject)
    ret = check_send_message(user_profile, get_client("API"), "stream", [stream], subject, content)
    if ret is not None:
        return json_error(ret)
    return json_success()

def get_status_list(requesting_user_profile):
    return {'presences': get_status_dict(requesting_user_profile),
            'server_timestamp': time.time()}

@authenticated_json_post_view
@has_request_variables
def json_update_active_status(request, user_profile, status=REQ):
    status_val = UserPresence.status_from_string(status)
    if status_val is None:
        raise JsonableError("Invalid presence status: %s" % (status,))
    else:
        update_user_presence(user_profile, request.client, now(), status_val)

    ret = get_status_list(user_profile)
    if user_profile.realm.domain == "mit.edu":
        try:
            # We renamed /api/v1/get_messages to /api/v1/events
            try:
                activity = UserActivity.objects.get(user_profile = user_profile,
                                                    query="/api/v1/events",
                                                    client__name="zephyr_mirror")
            except UserActivity.DoesNotExist:
                activity = UserActivity.objects.get(user_profile = user_profile,
                                                    query="/api/v1/get_messages",
                                                    client__name="zephyr_mirror")

            ret['zephyr_mirror_active'] = \
                (activity.last_visit.replace(tzinfo=None) >
                 datetime.datetime.utcnow() - datetime.timedelta(minutes=5))
        except UserActivity.DoesNotExist:
            ret['zephyr_mirror_active'] = False

    return json_success(ret)

@authenticated_json_post_view
def json_get_active_statuses(request, user_profile):
    return json_success(get_status_list(user_profile))

# Read the source map information for decoding JavaScript backtraces
js_source_map = None
if not (settings.DEBUG or settings.TEST_SUITE):
    js_source_map = SourceMap(path.join(
        settings.DEPLOY_ROOT, 'prod-static/source-map'))

@authenticated_json_post_view
@has_request_variables
def json_report_error(request, user_profile, message=REQ, stacktrace=REQ,
                      ui_message=REQ(converter=json_to_bool), user_agent=REQ,
                      href=REQ,
                      more_info=REQ(converter=json_to_dict, default=None)):
    subject = "error for %s" % (user_profile.email,)
    if ui_message:
        subject = "User-visible browser " + subject
    else:
        subject = "Browser " + subject

    if js_source_map:
        stacktrace = js_source_map.annotate_stacktrace(stacktrace)

    body = ("Message:\n%s\n\nStacktrace:\n%s\n\nUser agent: %s\nhref: %s\n"
            "User saw error in UI: %s\n"
            % (message, stacktrace, user_agent, href, ui_message))

    body += "Server path: %s\n" % (settings.DEPLOY_ROOT,)
    try:
        body += "Deployed version: %s" % (
            subprocess.check_output(["git", "log", "HEAD^..HEAD", "--oneline"]),)
    except Exception:
        body += "Could not determine current git commit ID.\n"

    if more_info is not None:
        body += "\nAdditional information:"
        for (key, value) in more_info.iteritems():
            body += "\n  %s: %s" % (key, value)

    mail_admins(subject, body)
    return json_success()

@authenticated_json_post_view
def json_events_register(request, user_profile):
    return events_register_backend(request, user_profile)

# Does not need to be authenticated because it's called from rest_dispatch
@has_request_variables
def api_events_register(request, user_profile,
                        apply_markdown=REQ(default=False, converter=json_to_bool)):
    return events_register_backend(request, user_profile,
                                   apply_markdown=apply_markdown)

@has_request_variables
def events_register_backend(request, user_profile, apply_markdown=True,
                            event_types=REQ(converter=json_to_list, default=None)):
    ret = do_events_register(user_profile, request.client, apply_markdown,
                             event_types)
    return json_success(ret)

@authenticated_json_post_view
def json_messages_in_narrow(request, user_profile):
    return messages_in_narrow_backend(request, user_profile)

@has_request_variables
def messages_in_narrow_backend(request, user_profile, msg_ids = REQ(converter=json_to_list),
                               narrow = REQ(converter=narrow_parameter)):
    # Note that this function will only work on messages the user
    # actually received

    query = UserMessage.objects.select_related("message") \
                               .filter(user_profile=user_profile, message__id__in=msg_ids)
    build = NarrowBuilder(user_profile, "message__")
    for operator, operand in narrow:
        query = build(query, operator, operand)

    return json_success({"messages": dict((msg.message.id,
                                           {'match_subject': msg.match_subject,
                                            'match_content': msg.match_content})
                                          for msg in query.iterator())})

def deactivate_user_backend(request, user_profile, email):
    try:
        target = get_user_profile_by_email(email)
    except UserProfile.DoesNotExist:
        return json_error('No such user')

    if target.bot_owner != user_profile and not user_profile.has_perm('administer', user_profile.realm):
        return json_error('Insufficient permission')

    do_deactivate(target)
    return json_success({})

@has_request_variables
def update_bot_backend(request, user_profile, email, full_name=REQ):
    # TODO:
    #   1) Validate data
    #   2) Support avatar changes
    try:
        bot = get_user_profile_by_email(email)
    except:
        return json_error('No such user')

    if bot.bot_owner != user_profile and not user_profile.has_perm('administer', user_profile.realm):
        return json_error('Insufficient permission')

    do_change_full_name(bot, full_name)

    bot_avatar_url = None

    if len(request.FILES) == 0:
        pass
    elif len(request.FILES) == 1:
        user_file = request.FILES.values()[0]
        upload_avatar_image(user_file, user_profile, bot.email)
        avatar_source = UserProfile.AVATAR_FROM_USER
        bot.avatar_source = avatar_source
        bot.save()
        bot_avatar_url = avatar_url(bot)
    else:
        return json_error("You may only upload one file at a time")

    json_result = dict(
        full_name = full_name,
        avatar_url = bot_avatar_url
    )
    return json_success(json_result)

@has_request_variables
def regenerate_bot_api_key(request, user_profile, email):
    try:
        bot = get_user_profile_by_email(email)
    except:
        return json_error('No such user')

    if bot.bot_owner != user_profile and not user_profile.has_perm('administer', user_profile.realm):
        return json_error('Insufficient permission')

    bot.api_key = random_api_key()
    bot.save()
    json_result = dict(
        api_key = bot.api_key
    )
    return json_success(json_result)

@authenticated_json_post_view
@has_request_variables
def json_create_bot(request, user_profile, full_name=REQ, short_name=REQ):
    short_name += "-bot"
    email = short_name + "@" + user_profile.realm.domain
    form = CreateBotForm({'full_name': full_name, 'email': email})
    if not form.is_valid():
        # We validate client-side as well
        return json_error('Bad name or username')

    try:
        get_user_profile_by_email(email)
        return json_error("Username already in use")
    except UserProfile.DoesNotExist:
        pass

    if len(request.FILES) == 0:
        avatar_source = UserProfile.AVATAR_FROM_GRAVATAR
    elif len(request.FILES) != 1:
        return json_error("You may only upload one file at a time")
    else:
        user_file = request.FILES.values()[0]
        upload_avatar_image(user_file, user_profile, email)
        avatar_source = UserProfile.AVATAR_FROM_USER

    bot_profile = do_create_user(email, '', user_profile.realm, full_name,
                                 short_name, True, True,
                                 user_profile, avatar_source)
    json_result = dict(
            api_key=bot_profile.api_key,
            avatar_url=avatar_url(bot_profile)
    )
    return json_success(json_result)

@authenticated_json_post_view
def json_get_bots(request, user_profile):
    bot_profiles = UserProfile.objects.filter(is_bot=True, is_active=True,
                                              bot_owner=user_profile)
    bot_profiles = bot_profiles.order_by('date_joined')

    def bot_info(bot_profile):
        return dict(
                username   = bot_profile.email,
                full_name  = bot_profile.full_name,
                api_key    = bot_profile.api_key,
                avatar_url = avatar_url(bot_profile)
        )

    return json_success({'bots': map(bot_info, bot_profiles)})

from django.template import Node, Library, TemplateSyntaxError
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

register = Library()

class MinifiedJSNode(Node):
    def __init__(self, sourcefile):
        self.sourcefile = sourcefile

    def render(self, context):
        if settings.DEBUG:
            scripts = settings.JS_SPECS[self.sourcefile]['source_filenames']
        else:
            scripts = [settings.JS_SPECS[self.sourcefile]['output_filename']]
        script_urls = [staticfiles_storage.url(script) for script in scripts]
        script_tags = ['<script type="text/javascript" src="%s" charset="utf-8"></script>'
                % url for url in script_urls]
        return '\n'.join(script_tags)


@register.tag
def minified_js(parser, token):
    try:
        tag_name, sourcefile = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError("%s tag requires an argument" % tag_name)
    if not (sourcefile[0] == sourcefile[-1] and sourcefile[0] in ('"', "'")):
        raise TemplateSyntaxError("%s tag should be quoted" % tag_name)

    sourcefile = sourcefile[1:-1]
    if sourcefile not in settings.JS_SPECS:
        raise TemplateSyntaxError("%s tag invalid argument: no JS file %s"
                % (tag_name, sourcefile))
    return MinifiedJSNode(sourcefile)


# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Message.last_edit_time'
        db.add_column(u'zephyr_message', 'last_edit_time',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'Message.edit_history'
        db.add_column(u'zephyr_message', 'edit_history',
                      self.gf('django.db.models.fields.TextField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Message.last_edit_time'
        db.delete_column(u'zephyr_message', 'last_edit_time')

        # Deleting field 'Message.edit_history'
        db.delete_column(u'zephyr_message', 'edit_history')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'edit_history': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'onboarding_steps': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserProfile.enable_offline_email_notifications'
        db.add_column(u'zephyr_userprofile', 'enable_offline_email_notifications',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=True)

        # Adding field 'UserProfile.last_reminder'
        db.add_column(u'zephyr_userprofile', 'last_reminder',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=True)


    def backwards(self, orm):
        # Deleting field 'UserProfile.enable_offline_email_notifications'
        db.delete_column(u'zephyr_userprofile', 'enable_offline_email_notifications')

        # Deleting field 'UserProfile.last_reminder'
        db.delete_column(u'zephyr_userprofile', 'last_reminder')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings

class Migration(SchemaMigration):

    def forwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return

        # This is a translation of django.util.html.escape
        db.execute("""CREATE FUNCTION escape_html(text) RETURNS text IMMUTABLE
                      LANGUAGE 'sql' AS $$ SELECT replace(replace(replace(
                      replace(replace($1, '&', '&amp;'), '<', '&lt;'), '>',
                      '&gt;'), '"', '&quot;'), '''', '&#39;'); $$""")

    def backwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return

        db.execute("DROP FUNCTION escape_html(text)")

    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserProfile.rate_limits'
        db.add_column(u'zephyr_userprofile', 'rate_limits',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=100),
                      keep_default=True)

        # Set up some initial overrides
        try:
            user = orm.UserProfile.objects.get(email='tabbott/extra@mit.edu')
            user.rate_limits = "1:100" # 100 calls/sec for the tabbott mirror user
            user.save()
        except:
            pass


    def backwards(self, orm):
        # Deleting field 'UserProfile.rate_limits'
        db.delete_column(u'zephyr_userprofile', 'rate_limits')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'edit_history': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True'}),
            'onboarding_steps': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'rate_limits': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'UserProfile.last_reminder'
        db.alter_column(u'zephyr_userprofile', 'last_reminder', self.gf('django.db.models.fields.DateTimeField')(null=True))

    def backwards(self, orm):

        # Changing field 'UserProfile.last_reminder'
        db.alter_column(u'zephyr_userprofile', 'last_reminder', self.gf('django.db.models.fields.DateTimeField')())

    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'edit_history': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True'}),
            'onboarding_steps': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.start_transaction()

        db.execute("CREATE TABLE fts_update_log (id SERIAL PRIMARY KEY, message_id INTEGER NOT NULL)")
        db.execute("CREATE FUNCTION do_notify_fts_update_log() RETURNS trigger "
                   "LANGUAGE plpgsql AS $$ BEGIN NOTIFY fts_update_log; RETURN NEW; END $$")
        db.execute("CREATE TRIGGER fts_update_log_notify AFTER INSERT ON fts_update_log "
                   "FOR EACH STATEMENT EXECUTE PROCEDURE do_notify_fts_update_log()")

        db.execute("CREATE FUNCTION append_to_fts_update_log() RETURNS trigger "
                   "LANGUAGE plpgsql AS $$ "
                   "BEGIN INSERT INTO fts_update_log (message_id) VALUES (NEW.id); RETURN NEW; END "
                   "$$")
        db.execute("CREATE TRIGGER zephyr_message_update_search_tsvector_async "
                   "BEFORE INSERT OR UPDATE OF subject, rendered_content ON zephyr_message "
                   "FOR EACH ROW EXECUTE PROCEDURE append_to_fts_update_log()")

        db.execute("DROP TRIGGER zephyr_message_update_search_tsvector ON zephyr_message")

        db.commit_transaction()

    def backwards(self, orm):
        db.start_transaction()

        db.execute("CREATE TRIGGER zephyr_message_update_search_tsvector "
                   "BEFORE INSERT OR UPDATE OF subject, rendered_content ON zephyr_message "
                   "FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger(search_tsvector, "
                   "'humbug.english_us_search', subject, rendered_content)")

        db.execute("DROP TRIGGER zephyr_message_update_search_tsvector_async ON zephyr_message")
        db.execute("DROP FUNCTION append_to_fts_update_log()")
        db.execute("DROP TRIGGER fts_update_log_notify ON fts_update_log")
        db.execute("DROP FUNCTION do_notify_fts_update_log()")
        db.execute("DROP TABLE fts_update_log")

        db.commit_transaction()

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'edit_history': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'avatar_source': ('django.db.models.fields.CharField', [], {'default': "'G'", 'max_length': '1'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True'}),
            'onboarding_steps': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'rate_limits': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserProfile.is_superuser'
        db.add_column(u'zephyr_userprofile', 'is_superuser',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=True)

        # Adding M2M table for field groups on 'UserProfile'
        db.create_table(u'zephyr_userprofile_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm[u'zephyr.userprofile'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(u'zephyr_userprofile_groups', ['userprofile_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'UserProfile'
        db.create_table(u'zephyr_userprofile_user_permissions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm[u'zephyr.userprofile'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(u'zephyr_userprofile_user_permissions', ['userprofile_id', 'permission_id'])


    def backwards(self, orm):
        # Deleting field 'UserProfile.is_superuser'
        db.delete_column(u'zephyr_userprofile', 'is_superuser')

        # Removing M2M table for field groups on 'UserProfile'
        db.delete_table('zephyr_userprofile_groups')

        # Removing M2M table for field user_permissions on 'UserProfile'
        db.delete_table('zephyr_userprofile_user_permissions')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'edit_history': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'avatar_source': ('django.db.models.fields.CharField', [], {'default': "'G'", 'max_length': '1'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True'}),
            'onboarding_steps': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'rate_limits': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Subscription.color'
        db.add_column(u'zephyr_subscription', 'color',
                      self.gf('django.db.models.fields.CharField')(default='#c2c2c2', max_length=10),
                      keep_default=False)
        if "postgres" in settings.DATABASES["default"]["ENGINE"]:
            db.execute("ALTER TABLE zephyr_subscription ALTER COLUMN color SET DEFAULT '#c2c2c2'")


    def backwards(self, orm):
        # Deleting field 'Subscription.color'
        db.delete_column(u'zephyr_subscription', 'color')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.conf import settings
import time

class Migration(DataMigration):

    def forwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return

        db.start_transaction()
        db.execute("DROP TRIGGER zephyr_message_update_search_tsvector ON zephyr_message")
        db.execute("""CREATE TRIGGER zephyr_message_update_search_tsvector
                      BEFORE INSERT OR UPDATE OF subject, rendered_content ON zephyr_message
                      FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger(search_tsvector,
                      'humbug.english_us_search', subject, rendered_content)""")
        db.commit_transaction()

        (min_id, max_id) = db.execute("SELECT MIN(id), MAX(id) FROM zephyr_message")[0]
        if min_id is not None:
            self.set_search_tsvector('humbug.english_us_search', 'rendered_content',
                                     min_id, max_id)

    def set_search_tsvector(self, config, column, min_id, max_id):
        lower_bound = min_id
        batch_size = 1000
        query = ("UPDATE zephyr_message SET "
                 + "search_tsvector = to_tsvector(%s, "
                 + "subject || ' ' || " + column + ") "
                 + "WHERE id >= %s AND id < %s")
        for upper_bound in xrange(min_id + batch_size, max_id + batch_size, batch_size):
            db.start_transaction()
            db.execute(query,
                       params=[config, lower_bound, upper_bound])
            db.commit_transaction()
            lower_bound = upper_bound
            time.sleep(1)

    def backwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return

        db.start_transaction()
        db.execute("DROP TRIGGER zephyr_message_update_search_tsvector ON zephyr_message")
        db.execute("""CREATE TRIGGER zephyr_message_update_search_tsvector
                      BEFORE INSERT OR UPDATE ON zephyr_message FOR EACH ROW
                      EXECUTE PROCEDURE tsvector_update_trigger(search_tsvector,
                      'pg_catalog.english', subject, content)""");
        db.commit_transaction()

        (min_id, max_id) = db.execute("SELECT MIN(id), MAX(id) FROM zephyr_message")[0]
        if min_id is not None:
            self.set_search_tsvector('pg_catalog.english', 'content',
                                     min_id, max_id)

    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']
    symmetrical = True


# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        orm.UserProfile.objects.all().update(tutorial_status="F")

    def backwards(self, orm):
        "Write your backwards methods here."

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
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
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
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
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
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
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
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
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
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']"})
        },
        'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Client']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']"})
        },
        'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['zephyr']
    symmetrical = True

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'UserProfile', fields ['email']
        db.create_index(u'zephyr_userprofile', ['email'])

        # Adding unique constraint on 'UserProfile', fields ['email']
        db.create_unique(u'zephyr_userprofile', ['email'])


    def backwards(self, orm):
        # Removing unique constraint on 'UserProfile', fields ['email']
        db.delete_unique(u'zephyr_userprofile', ['email'])

        # Removing index on 'UserProfile', fields ['email']
        db.delete_index(u'zephyr_userprofile', ['email'])


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['zephyr']
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings

class Migration(SchemaMigration):

    def forwards(self, orm):
        db.execute("ALTER TEXT SEARCH DICTIONARY english_us_hunspell (StopWords = humbug_english)")

    def backwards(self, orm):
        db.execute("ALTER TEXT SEARCH DICTIONARY english_us_hunspell (StopWords = english)")

    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'edit_history': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'avatar_source': ('django.db.models.fields.CharField', [], {'default': "'G'", 'max_length': '1'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True'}),
            'onboarding_steps': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'rate_limits': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserProfile.avatar_source'
        db.add_column(u'zephyr_userprofile', 'avatar_source',
                      self.gf('django.db.models.fields.CharField')(default='G', max_length=1),
                      keep_default=True)


    def backwards(self, orm):
        # Deleting field 'UserProfile.avatar_source'
        db.delete_column(u'zephyr_userprofile', 'avatar_source')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'edit_history': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'avatar_source': ('django.db.models.fields.CharField', [], {'default': "'G'", 'max_length': '1'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True'}),
            'onboarding_steps': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'rate_limits': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserProfile.enable_sounds'
        db.add_column(u'zephyr_userprofile', 'enable_sounds',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=True)


    def backwards(self, orm):
        # Deleting field 'UserProfile.enable_sounds'
        db.delete_column(u'zephyr_userprofile', 'enable_sounds')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings

class Migration(SchemaMigration):

    def forwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return

        db.execute("""CREATE TEXT SEARCH DICTIONARY english_us_hunspell (template = ispell,
                      DictFile = en_us, AffFile = en_us, StopWords = english)""")
        db.execute("CREATE TEXT SEARCH CONFIGURATION humbug.english_us_search (COPY=pg_catalog.english)")
        db.execute("""ALTER TEXT SEARCH CONFIGURATION humbug.english_us_search ALTER MAPPING FOR
                      asciiword, asciihword, hword_asciipart, word, hword, hword_part
                      WITH english_us_hunspell, english_stem""")

    def backwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return

        db.execute("DROP TEXT SEARCH CONFIGURATION humbug.english_us_search")
        db.execute("DROP TEXT SEARCH DICTIONARY english_us_hunspell")

    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.execute("DROP INDEX IF EXISTS zephyr_message_full_text_idx")

    def backwards(self, orm):
        pass

    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'edit_history': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_edit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'avatar_source': ('django.db.models.fields.CharField', [], {'default': "'G'", 'max_length': '1'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True'}),
            'onboarding_steps': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'rate_limits': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserProfile.tutorial_status'
        db.add_column('zephyr_userprofile', 'tutorial_status',
                      self.gf('django.db.models.fields.CharField')(default='W', max_length=1),
                      keep_default=False)


        if "postgres" in settings.DATABASES["default"]["ENGINE"]:
            db.execute("ALTER TABLE zephyr_userprofile ALTER COLUMN tutorial_status SET DEFAULT 'W'")

    def backwards(self, orm):
        # Deleting field 'UserProfile.tutorial_status'
        db.delete_column('zephyr_userprofile', 'tutorial_status')


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
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
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
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
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
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
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
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
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
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']"})
        },
        'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Client']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.UserProfile']"})
        },
        'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Realm'
        db.create_table(u'zephyr_realm', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
            ('restricted_to_domain', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'zephyr', ['Realm'])

        # Adding model 'UserProfile'
        db.create_table(u'zephyr_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('pointer', self.gf('django.db.models.fields.IntegerField')()),
            ('last_pointer_updater', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('realm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Realm'])),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('enable_desktop_notifications', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('enter_sends', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
        ))
        db.send_create_signal(u'zephyr', ['UserProfile'])

        # Adding model 'PreregistrationUser'
        db.create_table(u'zephyr_preregistrationuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('referred_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'], null=True)),
            ('invited_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'zephyr', ['PreregistrationUser'])

        # Adding M2M table for field streams on 'PreregistrationUser'
        db.create_table(u'zephyr_preregistrationuser_streams', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('preregistrationuser', models.ForeignKey(orm[u'zephyr.preregistrationuser'], null=False)),
            ('stream', models.ForeignKey(orm[u'zephyr.stream'], null=False))
        ))
        db.create_unique(u'zephyr_preregistrationuser_streams', ['preregistrationuser_id', 'stream_id'])

        # Adding model 'MitUser'
        db.create_table(u'zephyr_mituser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'zephyr', ['MitUser'])

        # Adding model 'Stream'
        db.create_table(u'zephyr_stream', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30, db_index=True)),
            ('realm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Realm'])),
            ('invite_only', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
        ))
        db.send_create_signal(u'zephyr', ['Stream'])

        # Adding unique constraint on 'Stream', fields ['name', 'realm']
        db.create_unique(u'zephyr_stream', ['name', 'realm_id'])

        # Adding model 'Recipient'
        db.create_table(u'zephyr_recipient', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('type', self.gf('django.db.models.fields.PositiveSmallIntegerField')(db_index=True)),
        ))
        db.send_create_signal(u'zephyr', ['Recipient'])

        # Adding unique constraint on 'Recipient', fields ['type', 'type_id']
        db.create_unique(u'zephyr_recipient', ['type', 'type_id'])

        # Adding model 'Client'
        db.create_table(u'zephyr_client', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30, db_index=True)),
        ))
        db.send_create_signal(u'zephyr', ['Client'])

        # Adding model 'Message'
        db.create_table(u'zephyr_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Recipient'])),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=60, db_index=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('rendered_content', self.gf('django.db.models.fields.TextField')(null=True)),
            ('rendered_content_version', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('sending_client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Client'])),
        ))
        db.send_create_signal(u'zephyr', ['Message'])

        # Adding model 'UserMessage'
        db.create_table(u'zephyr_usermessage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Message'])),
            ('archived', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('flags', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
        ))
        db.send_create_signal(u'zephyr', ['UserMessage'])

        # Adding unique constraint on 'UserMessage', fields ['user_profile', 'message']
        db.create_unique(u'zephyr_usermessage', ['user_profile_id', 'message_id'])

        # Adding model 'Subscription'
        db.create_table(u'zephyr_subscription', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Recipient'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('in_home_view', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'zephyr', ['Subscription'])

        # Adding unique constraint on 'Subscription', fields ['user_profile', 'recipient']
        db.create_unique(u'zephyr_subscription', ['user_profile_id', 'recipient_id'])

        # Adding model 'Huddle'
        db.create_table(u'zephyr_huddle', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('huddle_hash', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40, db_index=True)),
        ))
        db.send_create_signal(u'zephyr', ['Huddle'])

        # Adding model 'UserActivity'
        db.create_table(u'zephyr_useractivity', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Client'])),
            ('query', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('count', self.gf('django.db.models.fields.IntegerField')()),
            ('last_visit', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'zephyr', ['UserActivity'])

        # Adding unique constraint on 'UserActivity', fields ['user_profile', 'client', 'query']
        db.create_unique(u'zephyr_useractivity', ['user_profile_id', 'client_id', 'query'])

        # Adding model 'UserPresence'
        db.create_table(u'zephyr_userpresence', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Client'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal(u'zephyr', ['UserPresence'])

        # Adding unique constraint on 'UserPresence', fields ['user_profile', 'client']
        db.create_unique(u'zephyr_userpresence', ['user_profile_id', 'client_id'])

        # Adding model 'DefaultStream'
        db.create_table(u'zephyr_defaultstream', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('realm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Realm'])),
            ('stream', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Stream'])),
        ))
        db.send_create_signal(u'zephyr', ['DefaultStream'])

        # Adding unique constraint on 'DefaultStream', fields ['realm', 'stream']
        db.create_unique(u'zephyr_defaultstream', ['realm_id', 'stream_id'])

        # Adding model 'StreamColor'
        db.create_table(u'zephyr_streamcolor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subscription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Subscription'])),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal(u'zephyr', ['StreamColor'])

        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return
        # we do not populate search_tsvector, as the data which you'd normally populate it is empty (which would be a NO-OP).
        # Also, we populate it in a later migration.
        db.execute("ALTER TABLE zephyr_message ADD COLUMN search_tsvector tsvector")
        if len(db.execute("""SELECT relname FROM pg_class
                             WHERE relname = 'zephyr_message_search_tsvector'""")) != 0:
            print "Not creating index because it already exists"
        else:
            db.execute("""CREATE INDEX zephyr_message_search_tsvector ON zephyr_message
                          USING gin(search_tsvector)""")
        db.execute("""CREATE TRIGGER zephyr_message_update_search_tsvector
                      BEFORE INSERT OR UPDATE ON zephyr_message FOR EACH ROW
                      EXECUTE PROCEDURE tsvector_update_trigger(search_tsvector,
                      'pg_catalog.english', subject, content)""");

    def backwards(self, orm):
        # Removing unique constraint on 'DefaultStream', fields ['realm', 'stream']
        db.delete_unique(u'zephyr_defaultstream', ['realm_id', 'stream_id'])

        # Removing unique constraint on 'UserPresence', fields ['user_profile', 'client']
        db.delete_unique(u'zephyr_userpresence', ['user_profile_id', 'client_id'])

        # Removing unique constraint on 'UserActivity', fields ['user_profile', 'client', 'query']
        db.delete_unique(u'zephyr_useractivity', ['user_profile_id', 'client_id', 'query'])

        # Removing unique constraint on 'Subscription', fields ['user_profile', 'recipient']
        db.delete_unique(u'zephyr_subscription', ['user_profile_id', 'recipient_id'])

        # Removing unique constraint on 'UserMessage', fields ['user_profile', 'message']
        db.delete_unique(u'zephyr_usermessage', ['user_profile_id', 'message_id'])

        # Removing unique constraint on 'Recipient', fields ['type', 'type_id']
        db.delete_unique(u'zephyr_recipient', ['type', 'type_id'])

        # Removing unique constraint on 'Stream', fields ['name', 'realm']
        db.delete_unique(u'zephyr_stream', ['name', 'realm_id'])

        # Deleting model 'Realm'
        db.delete_table(u'zephyr_realm')

        # Deleting model 'UserProfile'
        db.delete_table(u'zephyr_userprofile')

        # Deleting model 'PreregistrationUser'
        db.delete_table(u'zephyr_preregistrationuser')

        # Removing M2M table for field streams on 'PreregistrationUser'
        db.delete_table('zephyr_preregistrationuser_streams')

        # Deleting model 'MitUser'
        db.delete_table(u'zephyr_mituser')

        # Deleting model 'Stream'
        db.delete_table(u'zephyr_stream')

        # Deleting model 'Recipient'
        db.delete_table(u'zephyr_recipient')

        # Deleting model 'Client'
        db.delete_table(u'zephyr_client')

        # Deleting model 'Message'
        db.delete_table(u'zephyr_message')

        # Deleting model 'UserMessage'
        db.delete_table(u'zephyr_usermessage')

        # Deleting model 'Subscription'
        db.delete_table(u'zephyr_subscription')

        # Deleting model 'Huddle'
        db.delete_table(u'zephyr_huddle')

        # Deleting model 'UserActivity'
        db.delete_table(u'zephyr_useractivity')

        # Deleting model 'UserPresence'
        db.delete_table(u'zephyr_userpresence')

        # Deleting model 'DefaultStream'
        db.delete_table(u'zephyr_defaultstream')

        # Deleting model 'StreamColor'
        db.delete_table(u'zephyr_streamcolor')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserProfile.is_bot'
        db.add_column(u'zephyr_userprofile', 'is_bot',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=True)

        # Adding field 'UserProfile.bot_owner'
        db.add_column(u'zephyr_userprofile', 'bot_owner',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'], null=True, on_delete=models.SET_NULL),
                      keep_default=True)


    def backwards(self, orm):
        # Deleting field 'UserProfile.is_bot'
        db.delete_column(u'zephyr_userprofile', 'is_bot')

        # Deleting field 'UserProfile.bot_owner'
        db.delete_column(u'zephyr_userprofile', 'bot_owner_id')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Subscription.notifications'
        db.add_column(u'zephyr_subscription', 'notifications',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=True)

    def backwards(self, orm):
        # Deleting field 'Subscription.notifications'
        db.delete_column(u'zephyr_subscription', 'notifications')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserProfile.onboarding_steps'
        db.add_column(u'zephyr_userprofile', 'onboarding_steps',
                      self.gf('django.db.models.fields.TextField')(default='[]'),
                      keep_default=True)


    def backwards(self, orm):
        # Deleting field 'UserProfile.onboarding_steps'
        db.delete_column(u'zephyr_userprofile', 'onboarding_steps')


    models = {
        u'zephyr.client': {
            'Meta': {'object_name': 'Client'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        u'zephyr.defaultstream': {
            'Meta': {'unique_together': "(('realm', 'stream'),)", 'object_name': 'DefaultStream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Stream']"})
        },
        u'zephyr.huddle': {
            'Meta': {'object_name': 'Huddle'},
            'huddle_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zephyr.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'rendered_content': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rendered_content_version': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"}),
            'sending_client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'})
        },
        u'zephyr.mituser': {
            'Meta': {'object_name': 'MitUser'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'zephyr.preregistrationuser': {
            'Meta': {'object_name': 'PreregistrationUser'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'streams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['zephyr.Stream']", 'null': 'True', 'symmetrical': 'False'})
        },
        u'zephyr.realm': {
            'Meta': {'object_name': 'Realm'},
            'domain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_to_domain': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'zephyr.recipient': {
            'Meta': {'unique_together': "(('type', 'type_id'),)", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'zephyr.stream': {
            'Meta': {'unique_together': "(('name', 'realm'),)", 'object_name': 'Stream'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_only': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"})
        },
        u'zephyr.streamcolor': {
            'Meta': {'object_name': 'StreamColor'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Subscription']"})
        },
        u'zephyr.subscription': {
            'Meta': {'unique_together': "(('user_profile', 'recipient'),)", 'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#c2c2c2'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_home_view': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'notifications': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Recipient']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.useractivity': {
            'Meta': {'unique_together': "(('user_profile', 'client', 'query'),)", 'object_name': 'UserActivity'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_visit': ('django.db.models.fields.DateTimeField', [], {}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.usermessage': {
            'Meta': {'unique_together': "(('user_profile', 'message'),)", 'object_name': 'UserMessage'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Message']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userpresence': {
            'Meta': {'unique_together': "(('user_profile', 'client'),)", 'object_name': 'UserPresence'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']"})
        },
        u'zephyr.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'bot_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.UserProfile']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'enable_desktop_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_offline_email_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enable_sounds': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'enter_sends': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_bot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_pointer_updater': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'last_reminder': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'onboarding_steps': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'pointer': ('django.db.models.fields.IntegerField', [], {}),
            'realm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zephyr.Realm']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tutorial_status': ('django.db.models.fields.CharField', [], {'default': "'W'", 'max_length': '1'})
        }
    }

    complete_apps = ['zephyr']


from __future__ import absolute_import

from django.core.management.base import BaseCommand
from zephyr.models import get_user_profile_by_email
import os
from ConfigParser import SafeConfigParser

class Command(BaseCommand):
    help = """Reset all colors for a person to the default grey"""

    def handle(self, *args, **options):
        config_file = os.path.join(os.environ["HOME"], ".humbugrc")
        if not os.path.exists(config_file):
            raise RuntimeError("No ~/.humbugrc found")
        config = SafeConfigParser()
        with file(config_file, 'r') as f:
            config.readfp(f, config_file)
        api_key = config.get("api", "key")
        email = config.get("api", "email")

        user_profile = get_user_profile_by_email(email)
        user_profile.api_key = api_key
        user_profile.save(update_fields=["api_key"])

from __future__ import absolute_import

from optparse import make_option
import logging
import sys

from django.core.management.base import BaseCommand

from zephyr.lib import utils
from zephyr.models import UserMessage, get_user_profile_by_email
from django.db import transaction, models


class Command(BaseCommand):
    help = """Sets user message flags. Used internally by actions.py. Marks all
    Expects a comma-delimited list of user message ids via stdin, and an EOF to terminate."""

    option_list = BaseCommand.option_list + (
        make_option('-r', '--for-real',
                    dest='for_real',
                    action='store_true',
                    default=False,
                    help="Actually change message flags. Default is a dry run."),
        make_option('-f', '--flag',
                    dest='flag',
                    type='string',
                    help="The flag to add of remove"),
        make_option('-o', '--op',
                    dest='op',
                    type='string',
                    help="The operation to do: 'add' or 'remove'"),
        make_option('-u', '--until',
                    dest='all_until',
                    type='string',
                    help="Mark all messages <= specific usermessage id"),
        make_option('-m', '--email',
                    dest='email',
                    type='string',
                    help="Email to set messages for"),
        )

    def handle(self, *args, **options):
        if not options["flag"] or not options["op"] or not options["email"]:
            print "Please specify an operation, a flag and an email"
            exit(1)

        op = options['op']
        flag = getattr(UserMessage.flags, options['flag'])
        all_until = options['all_until']
        email = options['email']

        user_profile = get_user_profile_by_email(email)

        if all_until:
            filt = models.Q(id__lte=all_until)
        else:
            filt = models.Q(message__id__in=[mid.strip() for mid in sys.stdin.read().split(',')])
        mids = [m.id for m in
                    UserMessage.objects.filter(filt, user_profile=user_profile).order_by('-id')]

        if options["for_real"]:
            sys.stdin.close()
            sys.stdout.close()
            sys.stderr.close()

        def do_update(batch):
            with transaction.commit_on_success():
                msgs = UserMessage.objects.filter(id__in=batch)
                if op == 'add':
                    msgs.update(flags=models.F('flags').bitor(flag))
                elif op == 'remove':
                    msgs.update(flags=models.F('flags').bitand(~flag))

        if not options["for_real"]:
            logging.info("Updating %s by %s %s" % (mids, op, flag))
            logging.info("Dry run completed. Run with --for-real to change message flags.")
            exit(1)

        utils.run_in_batches(mids, 400, do_update, sleep_time=3)
        exit(0)

from __future__ import absolute_import

import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.core import validators

from zephyr.models import Realm, email_to_username
from zephyr.lib.actions import do_create_user
from zephyr.views import notify_new_user
from zephyr.lib.initial_password import initial_password

class Command(BaseCommand):
    help = """Create the specified user with a default initial password.

A user MUST have ALREADY accepted the Terms of Service before creating their
account this way.
"""

    option_list = BaseCommand.option_list + (
        make_option('--this-user-has-accepted-the-tos',
                    dest='tos',
                    action="store_true",
                    default=False,
                    help='Acknowledgement that the user has already accepted the ToS.'),
        make_option('--domain',
                    dest='domain',
                    type='str',
                    help='The name of the existing realm to which to add the user.'),
        )

    def handle(self, *args, **options):
        if not options["tos"]:
            raise CommandError("""You must confirm that this user has accepted the
Terms of Service by passing --this-user-has-accepted-the-tos.""")

        if not options["domain"]:
            raise CommandError("""Please specify a realm by passing --domain.""")

        try:
            realm = Realm.objects.get(domain=options["domain"])
        except Realm.DoesNotExist:
            raise CommandError("Realm does not exist.")

        try:
            email, full_name = args
            try:
                validators.validate_email(email)
            except ValidationError:
                raise CommandError("Invalid email address.")
        except ValueError:
            if len(args) != 0:
                raise CommandError("""Either specify an email and full name as two
parameters, or specify no parameters for interactive user creation.""")
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
            notify_new_user(do_create_user(email, initial_password(email),
                realm, full_name, email_to_username(email)),
                internal=True)
        except IntegrityError:
            raise CommandError("User already exists.")

from __future__ import absolute_import

from django.core.management.base import BaseCommand
from django.db.models import get_app, get_models
from django.contrib.auth.management import create_permissions

class Command(BaseCommand):
    help = "Sync newly created object permissions to the database"

    def handle(self, *args, **options):
        # From http://stackoverflow.com/a/11914435/90777
        create_permissions(get_app("zephyr"), get_models(), 2)

from __future__ import absolute_import

import datetime
import pytz

from django.core.management.base import BaseCommand
from zephyr.models import UserProfile, Realm, Stream, Message

class Command(BaseCommand):
    help = "Generate statistics on user activity."

    def messages_sent_by(self, user, week):
        start = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=(week + 1)*7)
        end = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=week*7)
        return Message.objects.filter(sender=user, pub_date__gt=start, pub_date__lte=end).count()

    def handle(self, *args, **options):
        if args:
            try:
                realms = [Realm.objects.get(domain=domain) for domain in args]
            except Realm.DoesNotExist, e:
                print e
                exit(1)
        else:
            realms = Realm.objects.all()

        for realm in realms:
            print realm.domain
            user_profiles = UserProfile.objects.filter(realm=realm, is_active=True)
            print "%d users" % (len(user_profiles),)
            print "%d streams" % (len(Stream.objects.filter(realm=realm)),)

            for user_profile in user_profiles:
                print "%35s" % (user_profile.email,),
                for week in range(10):
                    print "%5d" % (self.messages_sent_by(user_profile, week)),
                print ""

from __future__ import absolute_import

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

from zephyr.models import Realm
from zephyr.lib.actions import set_default_streams, log_event

from optparse import make_option
import sys

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

from __future__ import absolute_import

from optparse import make_option
from django.core.management.base import BaseCommand
from confirmation.models import Confirmation
from zephyr.models import UserProfile, MitUser, get_user_profile_by_email

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--resend', '-r', dest='resend', action='store_true',
                    help='Send tokens even if tokens were previously sent for the user.'),)
    help = "Generate an activation email to send to MIT users."

    def handle(self, *args, **options):
        for username in args:
            email = username + "@mit.edu"
            try:
                get_user_profile_by_email(email)
            except UserProfile.DoesNotExist:
                print username + ": User does not exist in database"
                continue
            mit_user, created = MitUser.objects.get_or_create(email=email)
            if not created and not options["resend"]:
                print username + ": User already exists. Use -r to resend."
            else:
                Confirmation.objects.send_confirmation(mit_user, email)
                print username + ": Mailed."


from __future__ import absolute_import

from optparse import make_option

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from zephyr.models import Realm, Stream, UserProfile, Subscription, \
    Message, Recipient

class Command(BaseCommand):
    help = """Colorize streams in a realm for people who have not already colored their streams."""

    option_list = BaseCommand.option_list + (
        make_option('-d', '--domain',
                    dest='domain',
                    type='str',
                    help='The name of the realm in which you are colorizing streams.'),
        )

    def handle(self, **options):
        if options["domain"] is None:
            self.print_help("python manage.py", "colorize_streams")
            exit(1)

        realm = Realm.objects.get(domain=options["domain"])
        user_profiles = UserProfile.objects.filter(realm=realm)
        users_who_need_colors = filter(lambda profile: Subscription.objects.filter(
                user_profile=profile).filter(~Q(color=Subscription.DEFAULT_STREAM_COLOR)).count() == 0, user_profiles)

        # Hand-selected colors from the current swatch options,
        # providing reasonable contrast for 1 - 7 streams.
        colors = [
            "#76ce90", # light forest green
            "#f5ce6e", # goldenrod
            "#a6c7e5", # light blue
            "#b0a5fd", # volet
            "#e79ab5", # pink
            "#bfd56f", # greenish-yellow
            "#f4ae55", # orange
            ]

        print "Setting stream colors for:"
        for user_profile in users_who_need_colors:
            print "    ", user_profile.full_name

        stream_ids = [result['recipient__type_id'] for result in \
                          Message.objects.filter(sender__realm=realm,
                                                 recipient__type=Recipient.STREAM)
                      .values('recipient__type_id').annotate(
                count=Count('recipient__type_id')).order_by('-count')]

        print "Setting color for:"
        for stream_id, color in zip(stream_ids, colors):
            # Give everyone the same color for a stream.
            print "    ", Stream.objects.get(id=stream_id).name
            # If this realm has more streams than preselected colors,
            # only color the N most popular.
            recipient = Recipient.objects.get(type=Recipient.STREAM, type_id=stream_id)
            for user_profile in users_who_need_colors:
                try:
                    subscription = Subscription.objects.get(user_profile=user_profile,
                                                            recipient=recipient)
                except Subscription.DoesNotExist:
                    # Not subscribed
                    continue

                subscription.color = color
                subscription.save(update_fields=["color"])

from __future__ import absolute_import

import os
import sys
import select

from django.core.management.base import BaseCommand, CommandError

from zephyr.lib.unminify import SourceMap

# Wait for the user to paste text, then time out quickly and
# return it.  Disable echo so that we can re-echo the same
# lines with our annotations.
def get_full_paste():
    try:
        os.system('stty -echo raw isig')

        data = ''
        while True:
            fd = sys.stdin.fileno()
            can_read = select.select([fd], [], [], 0.1)[0]
            if can_read:
                data += os.read(fd, 1)
            else:
                if data:
                    return data
    finally:
        os.system('stty cooked echo')

class Command(BaseCommand):
    args = '<source map directory>'
    help = '''Add source locations to a stack backtrace generated by minified code.

The currently checked out code should match the version that generated the error.'''

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('No source map directory specified')

        source_map = SourceMap(args[0])

        if os.isatty(sys.stdin.fileno()):
            sys.stdout.write('Paste stacktrace:\n\n')
            sys.stdout.flush()
            stacktrace = get_full_paste()
        else:
            stacktrace = sys.stdin.read()

        sys.stdout.write(source_map.annotate_stacktrace(stacktrace))

from __future__ import absolute_import

from django.core.management.base import BaseCommand
from zephyr.models import Subscription, Recipient, get_user_profile_by_email

class Command(BaseCommand):
    help = """Reset all colors for a person to the default grey"""

    def handle(self, *args, **options):
        if not args:
            self.print_help("python manage.py", "reset_colors")
            exit(1)

        for email in args:
            user_profile = get_user_profile_by_email(email)
            subs = Subscription.objects.filter(user_profile=user_profile,
                                               active=True,
                                               recipient__type=Recipient.STREAM)

            for sub in subs:
                sub.color = Subscription.DEFAULT_STREAM_COLOR
                sub.save(update_fields=["color"])

from __future__ import absolute_import

from django.core.management.base import BaseCommand

from zephyr.lib.actions import do_change_user_email
from zephyr.models import UserProfile, get_user_profile_by_email

class Command(BaseCommand):
    help = """Change the email address for a user.

Usage: python manage.py change_user_email <old email> <new email>"""

    def handle(self, *args, **options):
        if len(args) != 2:
            print "Please provide both the old and new address."
            exit(1)

        old_email, new_email = args
        try:
            user_profile = get_user_profile_by_email(old_email)
        except UserProfile.DoesNotExist:
            print "Old e-mail doesn't exist in the system."
            exit(1)

        do_change_user_email(user_profile, new_email)

from __future__ import absolute_import

from django.core.management.base import BaseCommand
from zephyr.models import StreamColor

class Command(BaseCommand):
    help = """Copies all colors from the StreamColor table to the Subscription table."""

    def handle(self, *args, **options):
        for stream_color in StreamColor.objects.all():
            subscription = stream_color.subscription
            subscription.color = stream_color.color
            subscription.save(update_fields=["color"])

from __future__ import absolute_import

from django.core.management.base import NoArgsCommand
from zephyr.models import clear_database

class Command(NoArgsCommand):
    help = "Clear only tables we change: messages, accounts + sessions"

    def handle_noargs(self, **options):
        clear_database()
        self.stdout.write("Successfully cleared the database.\n")


from __future__ import absolute_import

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import UserProfile, get_user_profile_by_email
from zephyr.lib.actions import do_change_password
import ujson

def dump():
    passwords = []
    for user_profile in UserProfile.objects.all():
        passwords.append((user_profile.email, user_profile.password))
    file("dumped-passwords", "w").write(ujson.dumps(passwords) + "\n")

def restore(change):
    for (email, password) in ujson.loads(file("dumped-passwords").read()):
        try:
            user_profile = get_user_profile_by_email(email)
        except UserProfile.DoesNotExist:
            print "Skipping...", email
            continue
        if change:
            do_change_password(user_profile, password, log=False,
                               hashed_password=True)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--restore', default=False, action='store_true'),
        make_option('--dry-run', '-n', default=False, action='store_true'),)

    def handle(self, *args, **options):
        if options["restore"]:
            restore(change=not options['dry_run'])
        else:
            dump()

from __future__ import absolute_import

from django.core.management.base import BaseCommand
from zephyr.lib.initial_password import initial_password
from zephyr.models import get_user_profile_by_email

class Command(BaseCommand):
    help = "Print the initial password and API key for accounts as created by populate_db"

    fmt = '%-30s %-16s  %-32s'

    def handle(self, *args, **options):
        print self.fmt % ('email', 'password', 'API key')
        for email in args:
            if '@' not in email:
                print 'ERROR: %s does not look like an email address' % (email,)
                continue
            print self.fmt % (email, initial_password(email), get_user_profile_by_email(email).api_key)

from __future__ import absolute_import

from optparse import make_option
from django.core.management.base import BaseCommand

from zephyr.models import UserProfile
from zephyr.lib.actions import compute_mit_user_fullname

# Helper to be used with manage.py shell to fix bad names on prod.
def update_mit_fullnames(change=False):
    for u in UserProfile.objects.select_related().all():
        if (u.is_active or u.realm.domain != "mit.edu"):
            # Don't change fullnames for non-MIT users or users who
            # actually have an account (is_active) and thus have
            # presumably set their fullname how they like it.
            continue
        computed_name = compute_mit_user_fullname(u.email)
        if u.full_name != computed_name:
            print "%s: %s => %s" % (u.email, u.full_name, computed_name)
            if change:
                u.full_name = computed_name
                u.save(update_fields=["full_name"])

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run', '-n', dest='dry_run', default=False, action='store_true'),)

    def handle(self, *args, **options):
        update_mit_fullnames(change=not options['dry_run'])

from __future__ import absolute_import

from django.core.management.base import BaseCommand

from zephyr.lib.actions import update_message_flags
from zephyr.models import UserProfile, Message, get_user_profile_by_email

class Command(BaseCommand):
    help = """Bankrupt one or many users.

Usage: python manage.py bankrupt_users <list of email addresses>"""

    def handle(self, *args, **options):
        if len(args) < 1:
            print "Please provide at least one e-mail address."
            exit(1)

        for email in args:
            try:
                user_profile = get_user_profile_by_email(email)
            except UserProfile.DoesNotExist:
                print "e-mail %s doesn't exist in the system, skipping" % (email,)
                continue

            update_message_flags(user_profile, "add", "read", None, True)

            messages = Message.objects.filter(
                usermessage__user_profile=user_profile).order_by('-id')[:1]
            if messages:
                old_pointer = user_profile.pointer
                new_pointer = messages[0].id
                user_profile.pointer = new_pointer
                user_profile.save(update_fields=["pointer"])
                print "%s: %d => %d" % (email, old_pointer, new_pointer)
            else:
                print "%s has no messages, can't bankrupt!" % (email,)

from __future__ import absolute_import

from django.core.management.base import BaseCommand
from zephyr.models import Subscription, Recipient, Message, Stream, \
    get_user_profile_by_email
from django.db.models import Q

import datetime
import pytz
from optparse import make_option

class Command(BaseCommand):
    help = """Delete all inactive tutorial stream subscriptions."""

    option_list = BaseCommand.option_list + (
        make_option('-f', '--for-real',
                    dest='for_real',
                    action='store_true',
                    default=False,
                    help="Actually deactive subscriptions. Default is a dry run."),
        )

    def has_sent_to(self, user_profile, recipient):
        return Message.objects.filter(sender=user_profile, recipient=recipient).count() != 0

    def handle(self, **options):
        possible_tutorial_streams = Stream.objects.filter(Q(name__startswith='tutorial-'))

        tutorial_bot = get_user_profile_by_email("tutorial-bot@zulip.com")

        for stream in possible_tutorial_streams:
            recipient = Recipient.objects.get(type=Recipient.STREAM, type_id=stream.id)
            subscribers = Subscription.objects.filter(recipient=recipient, active=True)
            if ((subscribers.count() == 1) and self.has_sent_to(tutorial_bot, recipient)):
                # This is a tutorial stream.
                most_recent_message = Message.objects.filter(
                    recipient=recipient).latest("pub_date")
                # This cutoff must be more generous than the tutorial bot cutoff
                # in the client code.
                cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(hours=2)

                if most_recent_message.pub_date < cutoff:
                    # The tutorial has expired, so delete the stream.
                    print stream.name, most_recent_message.pub_date
                    if options["for_real"]:
                        tutorial_user = subscribers[0]
                        tutorial_user.active = False
                        tutorial_user.save(update_fields=["active"])

        if options["for_real"]:
            print "Subscriptions deactivated."
        else:
            print "This was a dry run. Pass -f to actually deactivate."

from __future__ import absolute_import

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.lib.cache_helpers import fill_memcached_cache, cache_fillers

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--cache', dest="cache", default=None),)
    help = "Populate the memcached cache of messages."

    def handle(self, *args, **options):
        if options["cache"] is not None:
            return fill_memcached_cache(options["cache"])

        for cache in cache_fillers.keys():
            fill_memcached_cache(cache)


from __future__ import absolute_import

from optparse import make_option

from django.core.management.base import BaseCommand

from zephyr.lib.actions import do_deactivate, user_sessions
from zephyr.models import get_user_profile_by_email, UserProfile

class Command(BaseCommand):
    help = "Deactivate a user, including forcibly logging them out."

    option_list = BaseCommand.option_list + (
        make_option('-f', '--for-real',
                    dest='for_real',
                    action='store_true',
                    default=False,
                    help="Actually deactivate the user. Default is a dry run."),
        )

    def handle(self, *args, **options):
        if not args:
            print "Please specify an e-mail address."
            exit(1)

        user_profile = get_user_profile_by_email(args[0])

        print "Deactivating %s (%s) - %s" % (user_profile.full_name,
                                             user_profile.email,
                                             user_profile.realm.domain)
        print "%s has the following active sessions:" % (user_profile.email,)
        for session in user_sessions(user_profile):
            print session.expire_date, session.get_decoded()
        print ""
        print "%s has %s active bots that will also be deactivated." % (
                user_profile.email,
                UserProfile.objects.filter(
                    is_bot=True, is_active=True, bot_owner=user_profile
                ).count()
            )

        if not options["for_real"]:
            print "This was a dry run. Pass -f to actually deactivate."
            exit(1)

        do_deactivate(user_profile)
        print "Sessions deleted, user deactivated."

from __future__ import absolute_import

from optparse import make_option

from django.core.management.base import BaseCommand

from zephyr.lib.actions import do_remove_subscription
from zephyr.models import Realm, UserProfile, get_stream, \
    get_user_profile_by_email

class Command(BaseCommand):
    help = """Remove some or all users in a realm from a stream."""

    option_list = BaseCommand.option_list + (
        make_option('-d', '--domain',
                    dest='domain',
                    type='str',
                    help='The name of the realm in which you are removing people.'),
        make_option('-s', '--stream',
                    dest='stream',
                    type='str',
                    help='A stream name.'),
        make_option('-u', '--users',
                    dest='users',
                    type='str',
                    help='A comma-separated list of email addresses.'),
        make_option('-a', '--all-users',
                    dest='all_users',
                    action="store_true",
                    default=False,
                    help='Remove all users in this realm from this stream.'),
        )

    def handle(self, **options):
        if options["domain"] is None or options["stream"] is None or \
                (options["users"] is None and options["all_users"] is None):
            self.print_help("python manage.py", "remove_users_from_stream")
            exit(1)

        realm = Realm.objects.get(domain=options["domain"])
        stream_name = options["stream"].strip()
        stream = get_stream(stream_name, realm)

        if options["all_users"]:
            user_profiles = UserProfile.objects.filter(realm=realm)
        else:
            emails = set([email.strip() for email in options["users"].split(",")])
            user_profiles = []
            for email in emails:
                user_profiles.append(get_user_profile_by_email(email))

        for user_profile in user_profiles:
            did_remove = do_remove_subscription(user_profile, stream)
            print "%s %s from %s" % (
                "Removed" if did_remove else "Couldn't remove",
                user_profile.email, stream_name)

from django.core.management.base import BaseCommand
from django.db.models import Q
from zephyr.models import Realm, Stream, Message, Subscription, Recipient

class Command(BaseCommand):
    help = "Generate statistics on the streams for a realm."

    def handle(self, *args, **options):
        if args:
            try:
                realms = [Realm.objects.get(domain=domain) for domain in args]
            except Realm.DoesNotExist, e:
                print e
                exit(1)
        else:
            realms = Realm.objects.all()

        for realm in realms:
            print realm.domain
            print "------------"
            print "%25s %15s %10s" % ("stream", "subscribers", "messages")
            streams = Stream.objects.filter(realm=realm).exclude(Q(name__istartswith="tutorial-"))
            invite_only_count = 0
            for stream in streams:
                if stream.invite_only:
                    invite_only_count += 1
                    continue
                print "%25s" % (stream.name,),
                recipient = Recipient.objects.filter(type=Recipient.STREAM, type_id=stream.id)
                print "%10d" % (len(Subscription.objects.filter(recipient=recipient, active=True)),),
                num_messages = len(Message.objects.filter(recipient=recipient))
                print "%12d" % (num_messages,)
            print "%d invite-only streams" % (invite_only_count,)
            print ""

from __future__ import absolute_import

from optparse import make_option

from django.core.management.base import BaseCommand

from zephyr.lib.actions import delete_all_user_sessions, \
    delete_realm_user_sessions
from zephyr.models import Realm

class Command(BaseCommand):
    help = "Log out all users."

    option_list = BaseCommand.option_list + (
        make_option('--realm',
                    dest='realm',
                    action='store',
                    default=None,
                    help="Only logout all users in a particular realm"),
        )

    def handle(self, *args, **options):
        if options["realm"]:
            realm = Realm.objects.get(domain=options["realm"])
            delete_realm_user_sessions(realm)
        else:
            delete_all_user_sessions()

from __future__ import absolute_import

from django.conf import settings
settings.RUNNING_INSIDE_TORNADO = True
# We must call zephyr.lib.tornado_ioloop_logging.instrument_tornado_ioloop
# before we import anything else from our project in order for our
# Tornado load logging to work; otherwise we might accidentally import
# zephyr.lib.queue (which will instantiate the Tornado ioloop) before
# this.
from zephyr.lib.tornado_ioloop_logging import instrument_tornado_ioloop
instrument_tornado_ioloop()

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os
import sys
import tornado.web
import logging
from tornado import ioloop
from zephyr.lib.debug import interactive_debug_listen
from zephyr.lib.response import json_response
from zephyr import tornado_callbacks
from zephyr.lib.event_queue import setup_event_queue, add_client_gc_hook
from zephyr.lib.queue import setup_tornado_rabbitmq
from zephyr.middleware import async_request_stop

if settings.USING_RABBITMQ:
    from zephyr.lib.queue import queue_client

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
        interactive_debug_listen()

        import django
        from tornado import httpserver, web

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
            print "Quit the server with %s." % (quit_command,)

            if settings.USING_RABBITMQ:
                # Process notifications received via RabbitMQ
                def process_notification(chan, method, props, data):
                    tornado_callbacks.process_notification(data)
                queue_client.register_json_consumer('notify_tornado', process_notification)

            try:
                urls = (r"/json/get_updates",
                        r"/api/v1/get_messages",
                        r"/notify_tornado",
                        r"/api/v1/messages/latest",
                        r"/json/get_events",
                        r"/api/v1/events",
                        )
                # Application is an instance of Django's standard wsgi handler.
                application = web.Application([(url, AsyncDjangoHandler) for url in urls],
                                                debug=django.conf.settings.DEBUG,
                                              # Disable Tornado's own request logging, since we have our own
                                              log_function=lambda x: None)

                # start tornado web server in single-threaded mode
                http_server = httpserver.HTTPServer(application,
                                                    xheaders=xheaders,
                                                    no_keep_alive=no_keep_alive)
                http_server.listen(int(port), address=addr)

                if django.conf.settings.DEBUG:
                    ioloop.IOLoop.instance().set_blocking_log_threshold(5)

                setup_event_queue()
                add_client_gc_hook(tornado_callbacks.missedmessage_hook)
                setup_tornado_rabbitmq()
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

                ### ADDED BY HUMBUG
                request._resolver = resolver
                ### END ADDED BY HUMBUG

                callback, callback_args, callback_kwargs = resolver.resolve(
                        request.path_info)

                # Apply view middleware
                if response is None:
                    for middleware_method in self._view_middleware:
                        response = middleware_method(request, callback, callback_args, callback_kwargs)
                        if response:
                            break

                ### THIS BLOCK MODIFIED BY HUMBUG
                if response is None:
                    from ...decorator import RespondAsynchronously

                    try:
                        response = callback(request, *callback_args, **callback_kwargs)
                        if response is RespondAsynchronously:
                            async_request_stop(request)
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

        ### HUMBUG CHANGE: The remainder of this function was moved
        ### into its own function, just below, so we can call it from
        ### finish().
        response = self.apply_response_middleware(request, response, resolver)

        return response

    ### Copied from get_response (above in this file)
    def apply_response_middleware(self, request, response, resolver):
        try:
            # Apply response middleware, regardless of the response
            for middleware_method in self._response_middleware:
                response = middleware_method(request, response)
            response = self.apply_response_fixes(request, response)
        except: # Any exception should be gathered and handled
            signals.got_request_exception.send(sender=self.__class__, request=request)
            response = self.handle_uncaught_exception(request, resolver, sys.exc_info())

        return response

    def humbug_finish(self, response, request, apply_markdown):
        # Make sure that Markdown rendering really happened, if requested.
        # This is a security issue because it's where we escape HTML.
        # c.f. ticket #64
        #
        # apply_markdown=True is the fail-safe default.
        if response['result'] == 'success' and 'messages' in response and apply_markdown:
            for msg in response['messages']:
                if msg['content_type'] != 'text/html':
                    self.set_status(500)
                    return self.finish('Internal error: bad message format')
        if response['result'] == 'error':
            self.set_status(400)

        # Call the Django response middleware on our object so that
        # e.g. our own logging code can run; but don't actually use
        # the headers from that since sending those to Tornado seems
        # tricky; instead just send the (already json-rendered)
        # content on to Tornado
        django_response = json_response(res_type=response['result'],
                                        data=response, status=self.get_status())
        django_response = self.apply_response_middleware(request, django_response,
                                                         request._resolver)
        # Pass through the content-type from Django, as json content should be
        # served as application/json
        self.set_header("Content-Type", django_response['Content-Type'])
        return self.finish(django_response.content)

from __future__ import absolute_import

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import UserProfile, Message, UserMessage, \
    get_user_profile_by_email
from zephyr.lib.timestamp import datetime_to_timestamp, timestamp_to_datetime
import ujson

def dump():
    pointers = []
    for u in UserProfile.objects.all():
        pointer = u.pointer
        if pointer != -1:
            pub_date = Message.objects.get(id=pointer).pub_date
            pointers.append((u.email, datetime_to_timestamp(pub_date)))
        else:
            pointers.append((u.email, -1))
    file("dumped-pointers", "w").write(ujson.dumps(pointers) + "\n")

def restore(change):
    for (email, timestamp) in ujson.loads(file("dumped-pointers").read()):
        try:
            u = get_user_profile_by_email(email)
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
            u.save(update_fields=["pointer"])

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--restore', default=False, action='store_true'),
        make_option('--dry-run', '-n', default=False, action='store_true'),)

    def handle(self, *args, **options):
        if options["restore"]:
            restore(change=not options['dry_run'])
        else:
            dump()

from __future__ import absolute_import

from postmonkey import PostMonkey
from django.core.management.base import BaseCommand
from django.conf import settings

from zephyr.lib.queue import SimpleQueueClient

class Command(BaseCommand):
    pm = PostMonkey(settings.MAILCHIMP_API_KEY, timeout=10)

    def subscribe(self, ch, method, properties, data):
        self.pm.listSubscribe(
                id=settings.HUMBUG_FRIENDS_LIST_ID,
                email_address=data['EMAIL'],
                merge_vars=data['merge_vars'],
                double_optin=False,
                send_welcome=False)

    def handle(self, *args, **options):
        q = SimpleQueueClient()
        q.register_json_consumer("signups", self.subscribe)
        q.start_consuming()

from __future__ import absolute_import

import sys
import requests
from zephyr.models import get_user_profile_by_email, UserProfile
from zephyr.lib.avatar import gravatar_hash, user_avatar_hash
from zephyr.lib.upload import upload_avatar_image
from django.core.management.base import BaseCommand, CommandError
from django.core.files.uploadedfile import SimpleUploadedFile

class Command(BaseCommand):
    help = """Migrate the specified user's Gravatar over to an avatar that we serve.  If two
email addresses are specified, use the Gravatar for the first and upload the image
for both email addresses."""

    def handle(self, *args, **kwargs):
        if len(args) == 0:
            raise CommandError("You must specify a user")
        if len(args) > 2:
            raise CommandError("Too many positional arguments")

        old_email = args[0]

        if len(args) == 2:
            new_email = args[1]
        elif len(args) == 1:
            new_email = old_email

        gravatar_url = "https://secure.gravatar.com/avatar/%s?d=identicon" % (gravatar_hash(old_email),)
        gravatar_data = requests.get(gravatar_url).content
        gravatar_file = SimpleUploadedFile('gravatar.jpg', gravatar_data, 'image/jpeg')

        try:
            user_profile = get_user_profile_by_email(old_email)
        except UserProfile.DoesNotExist:
            try:
                user_profile = get_user_profile_by_email(new_email)
            except UserProfile.DoesNotExist:
                raise CommandError("Could not find specified user")

        upload_avatar_image(gravatar_file, user_profile, old_email)
        if old_email != new_email:
            gravatar_file.seek(0)
            upload_avatar_image(gravatar_file, user_profile, new_email)

        user_profile.avatar_source = UserProfile.AVATAR_FROM_USER
        user_profile.save(update_fields=['avatar_source'])

from __future__ import absolute_import
from optparse import make_option

from django.core.management.base import BaseCommand
from zephyr.lib.actions import do_create_realm

class Command(BaseCommand):
    help = """Create a realm for the specified domain.

Usage: python manage.py create_realm foo.com"""

    option_list = BaseCommand.option_list + (
        make_option('-o', '--open-realm',
                    dest='open_realm',
                    action="store_true",
                    default=False,
                    help='Make this an open realm.'),
        )

    def handle(self, *args, **options):
        if not args:
            self.print_help("python manage.py", "create_realm")
            exit(1)

        domain = args[0]
        realm, created = do_create_realm(
            domain, restricted_to_domain=not options["open_realm"])
        if created:
            print domain, "created."
        else:
            print domain, "already exists."

from __future__ import absolute_import

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import get_user_profile_by_email, UserMessage
from zephyr.views import get_old_messages_backend
import cProfile
import logging
from zephyr.middleware import LogRequests

request_logger = LogRequests()

class MockSession(object):
    def __init__(self):
        self.modified = False

class MockRequest(object):
    def __init__(self, email):
        self.user = get_user_profile_by_email(email)
        self.path = '/'
        self.method = "POST"
        self.META = {"REMOTE_ADDR": "127.0.0.1"}
        self.REQUEST = {"anchor": UserMessage.objects.filter(user_profile=self.user).order_by("-message")[200].message_id,
                        "num_before": 1200,
                        "num_after": 200}
        self.GET = {}
        self.session = MockSession()

    def get_full_path(self):
        return self.path

def profile_request(request):
    request_logger.process_request(request)
    prof = cProfile.Profile()
    prof.enable()
    ret = get_old_messages_backend(request, request.user,
                                   apply_markdown=True)
    prof.disable()
    prof.dump_stats("/tmp/profile.data")
    request_logger.process_response(request, ret)
    logging.info("Profiling data written to /tmp/profile.data")
    return ret

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--email', action='store'),
        )

    def handle(self, *args, **options):
        profile_request(MockRequest(options["email"]))

from __future__ import absolute_import

from zephyr.models import get_user_profile_by_id
from zephyr.lib.rate_limiter import client, max_api_calls, max_api_window

from django.core.management.base import BaseCommand
from django.conf import settings
from optparse import make_option

import time, logging

class Command(BaseCommand):
    help = """Checks redis to make sure our rate limiting system hasn't grown a bug and left redis with a bunch of data

    Usage: ./manage.py [--trim] check_redis"""

    option_list = BaseCommand.option_list + (
        make_option('-t', '--trim',
                    dest='trim',
                    default=False,
                    action='store_true',
                    help="Actually trim excess"),
        )

    def _check_within_range(self, key, count_func, trim_func):
        user_id = int(key.split(':')[1])
        try:
            user = get_user_profile_by_id(user_id)
        except:
            user = None
        max_calls = max_api_calls(user=user)

        age = int(client.ttl(key))
        if age < 0:
            logging.error("Found key with age of %s, will never expire: %s" % (age, key,))

        count = count_func()
        if count > max_calls:
            logging.error("Redis health check found key with more elements \
than max_api_calls! (trying to trim) %s %s" % (key, count))
            if self.trim:
                client.expire(key, max_api_window(user=user))
                trim_func(key, max_calls)

    def handle(self, *args, **options):
        if not settings.RATE_LIMITING:
            print "This machine is not using redis or rate limiting, aborting"
            exit(1)

        # Find all keys, and make sure they're all within size constraints
        wildcard_list = "ratelimit:*:*:list"
        wildcard_zset = "ratelimit:*:*:zset"

        self.trim = options['trim']

        lists = client.keys(wildcard_list)
        for list_name in lists:
            self._check_within_range(list_name,
                                     lambda: client.llen(list_name),
                                     lambda key, max_calls: client.ltrim(key, 0, max_calls - 1))

        zsets = client.keys(wildcard_zset)
        for zset in zsets:
            now = time.time()
            # We can warn on our zset being too large, but we don't know what
            # elements to trim. We'd have to go through every list item and take
            # the intersection. The best we can do is expire it
            self._check_within_range(zset,
                                     lambda:  client.zcount(zset, 0, now),
                                     lambda key, max_calls:  None)

from __future__ import absolute_import

from django.conf import settings
from django.core.management.base import BaseCommand
from zephyr.lib.actions import process_user_activity_event, \
        process_user_presence_event
from zephyr.lib.queue import SimpleQueueClient
import sys
import signal
import os
import traceback
import ujson

ERROR_LOG_FILE = os.path.join(settings.ERROR_LOG_DIR, "process_user_activity")

class Command(BaseCommand):
    option_list = BaseCommand.option_list
    help = "Process UserActivity log messages."

    def handle(self, *args, **options):
        activity_queue = SimpleQueueClient()

        def callback_activity(ch, method, properties, event):
            print " [x] Received activity %r" % (event,)
            try:
                process_event(event)
            except Exception:
                if not os.path.exists(settings.ERROR_LOG_DIR):
                    os.mkdir(settings.ERROR_LOG_DIR)
                # One can parse out just the JSON records from this log format using:
                #
                # grep "Error Processing" errors/process_user_activity  | cut -f 2- -d:
                file(ERROR_LOG_FILE, "a").write(
                    "Error Processing event: " + ujson.dumps(event) + "\n" +
                    traceback.format_exc())

        def process_event(event):
            msg_type = event['type']
            if msg_type == 'user_activity':
                process_user_activity_event(event)
            elif msg_type == 'user_presence':
                process_user_presence_event(event)
            else:
                print("[*] Unknown message type: %s" % (msg_type,))

        def signal_handler(signal, frame):
            print("[*] Closing and disconnecting from queues")
            activity_queue.stop_consuming()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        print ' [*] Waiting for messages. To exit press CTRL+C'
        activity_queue.register_json_consumer('user_activity', callback_activity)
        activity_queue.start_consuming()

from __future__ import absolute_import

import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.core import validators

from guardian.shortcuts import assign_perm, remove_perm

from zephyr.models import Realm, UserProfile

class Command(BaseCommand):
    help = """Give an existing user administrative permissions over their (own) Realm.

ONLY perform this on customer request from an authorized person.
"""

    option_list = BaseCommand.option_list + (
        make_option('-f', '--for-real',
                    dest='ack',
                    action="store_true",
                    default=False,
                    help='Acknowledgement that this is done according to policy.'),
        make_option('--revoke',
                    dest='grant',
                    action="store_false",
                    default=True,
                    help='Remove an administrator\'s rights.'),
        )

    def handle(self, *args, **options):
        try:
            email = args[0]
        except ValueError:
            raise CommandError("""Please specify a user.""")
        try:
            profile = UserProfile.objects.get(email=email)
        except ValidationError:
            raise CommandError("No such user.")

        if options['grant']:
            if profile.has_perm('administer', profile.realm):
                raise CommandError("User already has permission for this realm.")
            else:
                if options['ack']:
                    assign_perm('administer', profile, profile.realm)
                    print "Done!"
                else:
                    print "Would have made %s an administrator for %s" % (email, profile.realm.domain)
        else:
            if profile.has_perm('administer', profile.realm):
                if options['ack']:
                    remove_perm('administer', profile, profile.realm)
                    print "Done!"
                else:
                    print "Would have removed %s's administrator rights on %s" % (email,
                            profile.realm.domain)
            else:
                raise CommandError("User did not have permission for this realm!")

from __future__ import absolute_import

import time

from collections import defaultdict

from django.core.management.base import BaseCommand

from zephyr.lib.queue import SimpleQueueClient
from zephyr.lib.actions import handle_missedmessage_emails

class Command(BaseCommand):
    def handle(self, *args, **options):
        q = SimpleQueueClient()
        while True:
            missed_events = q.drain_queue("missedmessage_emails", json=True)
            by_recipient = defaultdict(list)

            for event in missed_events:
                print "Received missed message event: %s" % (event,)
                by_recipient[event['user_profile_id']].append(event)

            for user_profile_id, events in by_recipient.items():
                handle_missedmessage_emails(user_profile_id, events)

            # Aggregate all messages received every 2 minutes to let someone finish sending a batch
            # of messages
            time.sleep(2 * 60)

from __future__ import absolute_import

from optparse import make_option

from django.core.management.base import BaseCommand

from zephyr.lib.actions import create_stream_if_needed, do_add_subscription
from zephyr.models import Realm, UserProfile, get_user_profile_by_email

class Command(BaseCommand):
    help = """Add some or all users in a realm to a set of streams."""

    option_list = BaseCommand.option_list + (
        make_option('-d', '--domain',
                    dest='domain',
                    type='str',
                    help='The name of the realm in which you are adding people to streams.'),
        make_option('-s', '--streams',
                    dest='streams',
                    type='str',
                    help='A comma-separated list of stream names.'),
        make_option('-u', '--users',
                    dest='users',
                    type='str',
                    help='A comma-separated list of email addresses.'),
        make_option('-a', '--all-users',
                    dest='all_users',
                    action="store_true",
                    default=False,
                    help='Add all users in this realm to these streams.'),
        )

    def handle(self, **options):
        if options["domain"] is None or options["streams"] is None or \
                (options["users"] is None and options["all_users"] is None):
            self.print_help("python manage.py", "add_users_to_streams")
            exit(1)

        stream_names = set([stream.strip() for stream in options["streams"].split(",")])
        realm = Realm.objects.get(domain=options["domain"])

        if options["all_users"]:
            user_profiles = UserProfile.objects.filter(realm=realm)
        else:
            emails = set([email.strip() for email in options["users"].split(",")])
            user_profiles = []
            for email in emails:
                user_profiles.append(get_user_profile_by_email(email))

        for stream_name in set(stream_names):
            for user_profile in user_profiles:
                stream, _ = create_stream_if_needed(user_profile.realm, stream_name)
                did_subscribe = do_add_subscription(user_profile, stream)
                print "%s %s to %s" % (
                    "Subscribed" if did_subscribe else "Already subscribed",
                    user_profile.email, stream_name)

from __future__ import absolute_import

from django.core.management.base import BaseCommand
from confirmation.models import Confirmation
from zephyr.models import UserProfile, PreregistrationUser, \
    get_user_profile_by_email

class Command(BaseCommand):
    help = "Generate activation links for users and print them to stdout."

    def handle(self, *args, **options):
        duplicates = False
        for email in args:
            try:
                get_user_profile_by_email(email)
                print email + ": There is already a user registered with that address."
                duplicates = True
                continue
            except UserProfile.DoesNotExist:
                pass

        if duplicates:
            return

        for email in args:
            prereg_user = PreregistrationUser(email=email)
            prereg_user.save()
            print email + ": " + Confirmation.objects.get_link_for_object(prereg_user)


from __future__ import absolute_import

from zephyr.models import UserProfile, get_user_profile_by_email
from zephyr.lib.rate_limiter import block_user, unblock_user

from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
    help = """Manually block or unblock a user from accessing the API

    Usage: ./manage.py rate_limit [--all-bots] [--domain all] [--seconds 60] [--api-key bf4sds] [--email f@b.com] block/unblock"""

    option_list = BaseCommand.option_list + (
        make_option('-e', '--email',
                    dest='email',
                    help="Email account of user."),
        make_option('-a', '--api-key',
                    dest='api_key',
                    help="API key of user."),
        make_option('-s', '--seconds',
                    dest='seconds',
                    default=60,
                    type=int,
                    help="Seconds to block for."),
        make_option('-d', '--domain',
                    dest='domain',
                    default='all',
                    help="Rate-limiting domain. Defaults to 'all'."),
        make_option('-b', '--all-bots',
                    dest='bots',
                    action='store_true',
                    default=False,
                    help="Whether or not to also block all bots for this user."),
        )

    def handle(self, *args, **options):
        if len(args) == 0 or args[0] not in ('block', 'unblock'):
            print "Please pass either 'block' or 'unblock"
            exit(1)

        if (not options['api_key'] and not options['email']) or \
           (options['api_key'] and options['email']):
            print "Please enter either an email or API key to manage"
            exit(1)

        if options['email']:
            user_profile = get_user_profile_by_email(options['email'])
        else:
            try:
                user_profile = UserProfile.objects.get(api_key=options['api_key'])
            except:
                print "Unable to get user profile for api key %s" % (options['api_key'], )
                exit(1)

        users = [user_profile]
        if options['bots']:
            users.extend(bot for bot in UserProfile.objects.filter(is_bot=True,
                                                                   bot_owner=user_profile))

        operation = args[0]
        for user in users:
            print "Applying operation to User ID: %s: %s" % (user.id, operation)

            if operation == 'block':
                block_user(user, options['seconds'], options['domain'])
            elif operation == 'unblock':
                unblock_user(user, options['domain'])

from __future__ import absolute_import

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from django.contrib.sites.models import Site
from zephyr.models import Message, UserProfile, Stream, Recipient, Client, \
    Subscription, Huddle, get_huddle, Realm, UserMessage, \
    get_huddle_hash, clear_database, get_client, get_user_profile_by_id, \
    email_to_domain, email_to_username
from zephyr.lib.actions import do_send_message, set_default_streams, \
    do_activate_user, do_deactivate, do_change_password
from zephyr.lib.parallel import run_parallel
from django.db import transaction, connection
from django.conf import settings
from zephyr.lib.bulk_create import bulk_create_realms, \
    bulk_create_streams, bulk_create_users, bulk_create_huddles, \
    bulk_create_clients
from zephyr.lib.timestamp import timestamp_to_datetime
from zephyr.models import MAX_MESSAGE_LENGTH
from zephyr.models import DefaultStream, get_stream

import ujson
import datetime
import random
import glob
import os
from os import path
from optparse import make_option

settings.TORNADO_SERVER = None

def create_users(realms, name_list):
    user_set = set()
    for full_name, email in name_list:
        short_name = email_to_username(email)
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
            humbug_realm = Realm.objects.create(domain="zulip.com")
            Realm.objects.create(domain="mit.edu")
            realms = {}
            for realm in Realm.objects.all():
                realms[realm.domain] = realm

            # Create test Users (UserProfiles are automatically created,
            # as are subscriptions to the ability to receive personals).
            names = [("Othello, the Moor of Venice", "othello@zulip.com"), ("Iago", "iago@zulip.com"),
                     ("Prospero from The Tempest", "prospero@zulip.com"),
                     ("Cordelia Lear", "cordelia@zulip.com"), ("King Hamlet", "hamlet@zulip.com")]
            for i in xrange(options["extra_users"]):
                names.append(('Extra User %d' % (i,), 'extrauser%d@zulip.com' % (i,)))
            create_users(realms, names)
            # Create public streams.
            stream_list = ["Verona", "Denmark", "Scotland", "Venice", "Rome"]
            create_streams(realms, humbug_realm, stream_list)
            recipient_streams = [Stream.objects.get(name=name, realm=humbug_realm).id for name in stream_list]

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
            Subscription.objects.bulk_create(subscriptions_to_add)
        else:
            humbug_realm = Realm.objects.get(domain="zulip.com")
            recipient_streams = [klass.type_id for klass in
                                 Recipient.objects.filter(type=Recipient.STREAM)]

        # Extract a list of all users
        user_profiles = [user_profile.id for user_profile in UserProfile.objects.all()]

        # Create several initial huddles
        for i in xrange(options["num_huddles"]):
            get_huddle(random.sample(user_profiles, random.randint(3, 4)))

        # Create several initial pairs for personals
        personals_pairs = [random.sample(user_profiles, 2)
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
                ("Zulip New User Bot", "new-user-bot@zulip.com"),
                ("Zulip Error Bot", "error-bot@zulip.com"),
                ("Zulip Notification Bot", "notification-bot@zulip.com"),
                ("Zulip Tutorial Bot", "tutorial-bot@zulip.com"),
                ]
            create_users(realms, hardcoded_humbug_users_nosubs)

            if not options["test_suite"]:
                # To keep the messages.json fixtures file for the test
                # suite fast, don't add these users and subscriptions
                # when running populate_db for the test suite

                internal_mit_users = []
                create_users(realms, internal_mit_users)

                create_users(realms, settings.INTERNAL_HUMBUG_USERS)
                humbug_stream_list = ["devel", "all", "humbug", "design", "support", "social", "test",
                                      "errors", "sales"]
                create_streams(realms, humbug_realm, humbug_stream_list)

                # Add a few default streams
                for stream_name in ["design", "devel", "social", "support"]:
                    DefaultStream.objects.create(realm=humbug_realm, stream=get_stream(stream_name, humbug_realm))

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
                Subscription.objects.bulk_create(subscriptions_to_add)

                # These bots are not needed by the test suite
                internal_humbug_users_nosubs = [
                    ("Zulip Commit Bot", "commit-bot@zulip.com"),
                    ("Zulip Trac Bot", "trac-bot@zulip.com"),
                    ("Zulip Nagios Bot", "nagios-bot@zulip.com"),
                    ("Zulip Feedback Bot", "feedback@zulip.com"),
                    ]
                create_users(realms, internal_humbug_users_nosubs)

            # Mark all messages as read
            with transaction.commit_on_success():
                UserMessage.objects.all().update(flags=UserMessage.flags.read)

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
    email_set = set([u.email for u in UserProfile.objects.all()])
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
            tmp_message = ujson.loads(old_message_json)
            tmp_message['id'] = '1'
            duplicate_suppression_key = ujson.dumps(tmp_message)
            if duplicate_suppression_key in duplicate_suppression_hash:
                return
            duplicate_suppression_hash[duplicate_suppression_key] = True

        old_message = ujson.loads(old_message_json)
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
        elif message_type == "user_email_changed":
            old_message["old_email"] = fix_email(old_message["old_email"])
            old_message["new_email"] = fix_email(old_message["new_email"])
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

        domain = email_to_domain(sender_email)
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

    event_glob = path.join(settings.EVENT_LOG_DIR, 'events.*')
    for filename in sorted(glob.glob(event_glob)):
        with file(filename, "r") as message_log:
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
        users[user_profile.email] = user_profile
        users_by_id[user_profile.id] = user_profile
    for recipient in Recipient.objects.filter(type=Recipient.PERSONAL):
        user_recipients[users_by_id[recipient.type_id].email] = recipient

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
        domain = email_to_domain(sender_email)
        realm = realms[domain]

        message.sender = users[sender_email]
        type_hash = {"stream": Recipient.STREAM,
                     "huddle": Recipient.HUDDLE,
                     "personal": Recipient.PERSONAL}

        if 'sending_client' in old_message:
            message.sending_client = clients[old_message['sending_client']]
        elif sender_email in ["othello@zulip.com", "iago@zulip.com", "prospero@zulip.com",
                              "cordelia@zulip.com", "hamlet@zulip.com"]:
            message.sending_client = clients['populate_db']
        elif realm.domain == "zulip.com":
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
    Message.objects.bulk_create(messages_to_create)
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

    if len(messages_by_id) == 0:
        print datetime.datetime.now(), "No old messages to replay"
        return

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
            user_profile = users[old_message["user"]]
            join_date = timestamp_to_datetime(old_message['timestamp'])
            do_activate_user(user_profile, log=False, join_date=join_date)
            # Update the cache of users to show this user as activated
            users_by_id[user_profile.id] = user_profile
            users[old_message["user"]] = user_profile
            continue
        elif message_type == "user_deactivated":
            user_profile = users[old_message["user"]]
            do_deactivate(user_profile, log=False)
            continue
        elif message_type == "user_change_password":
            # Just handle these the slow way
            user_profile = users[old_message["user"]]
            do_change_password(user_profile, old_message["pwhash"], log=False,
                               hashed_password=True)
            continue
        elif message_type == "user_change_full_name":
            # Just handle these the slow way
            user_profile = users[old_message["user"]]
            user_profile.full_name = old_message["full_name"]
            user_profile.save(update_fields=["full_name"])
            continue
        elif message_type == "enable_desktop_notifications_changed":
            # Just handle these the slow way
            user_profile = users[old_message["user"]]
            user_profile.enable_desktop_notifications = (old_message["enable_desktop_notifications"] != "false")
            user_profile.save(update_fields=["enable_desktop_notifications"])
            continue
        elif message_type == "enable_sounds_changed":
            user_profile = users[old_message["user"]]
            user_profile.enable_sounds = (old_message["enable_sounds"] != "false")
            user_profile.save(update_fields=["enable_sounds"])
        elif message_type == "enable_offline_email_notifications_changed":
            user_profile = users[old_message["user"]]
            user_profile.enable_offline_email_notifications = (old_message["enable_offline_email_notifications"] != "false")
            user_profile.save(update_fields=["enable_offline_email_notifications"])
            continue
        elif message_type == "default_streams":
            set_default_streams(Realm.objects.get(domain=old_message["domain"]),
                                old_message["streams"])
            continue
        elif message_type == "subscription_property":
            property_name = old_message.get("property")
            if property_name == "stream_color" or property_name == "color":
                color = old_message.get("color", old_message.get("value"))
                pending_colors[(old_message["user"],
                                old_message["stream_name"].lower())] = color
            elif property_name in ["in_home_view", "notifications"]:
                # TODO: Handle this
                continue
            else:
                raise RuntimeError("Unknown property %s" % (property_name,))
            continue
        elif message_type == "realm_created":
            # No action required
            continue
        elif message_type in ["user_email_changed", "update_onboarding", "update_message"]:
            # TODO: Handle these
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
            if users_by_id[user_profile_id].is_active:
                um = UserMessage(user_profile_id=user_profile_id,
                                 message=message)
                user_messages_to_create.append(um)

        if len(user_messages_to_create) > 100000:
            tot_user_messages += len(user_messages_to_create)
            UserMessage.objects.bulk_create(user_messages_to_create)
            user_messages_to_create = []

    print datetime.datetime.now(), "Importing usermessages, part 2..."
    tot_user_messages += len(user_messages_to_create)
    UserMessage.objects.bulk_create(user_messages_to_create)

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
    Subscription.objects.bulk_create(subscriptions_to_add)
    with transaction.commit_on_success():
        for (sub, active) in subscriptions_to_change:
            current_subs_obj[sub].active = active
            current_subs_obj[sub].save(update_fields=["active"])

    subs = {}
    for sub in Subscription.objects.all():
        subs[(sub.user_profile_id, sub.recipient_id)] = sub

    # TODO: do restore of subscription colors -- we're currently not
    # logging changes so there's little point in having the code :(

    print datetime.datetime.now(), "Finished importing %s messages (%s usermessages)" % \
        (len(all_messages), tot_user_messages)

    site = Site.objects.get_current()
    site.domain = 'zulip.com'
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
            user_profile.save(update_fields=["pointer"])

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

from __future__ import absolute_import

from optparse import make_option
import logging

from django.core.management.base import BaseCommand

from zephyr.lib import utils
from zephyr.models import UserMessage, UserProfile, \
    get_user_profile_by_email
from django.db import transaction, models


class Command(BaseCommand):
    help = "Updates a user's read messages up to her current pointer location"

    option_list = BaseCommand.option_list + (
        make_option('-f', '--for-real',
                    dest='for_real',
                    action='store_true',
                    default=False,
                    help="Actually change message flags. Default is a dry run."),
        make_option('-a', '--all',
                    dest='all_users',
                    action='store_true',
                    default=False,
                    help="Updates flags for all users at once."),
        make_option('-r', '--realm',
                    dest='one_realm',
                    action='store_true',
                    default=False,
                    help="Updates flags for all users in one realm at once."),
        )

    def handle(self, *args, **options):
        if not args and not options["all_users"] and not options["one_realm"]:
            print "Please specify an e-mail address and/or --realm or --all"
            exit(1)

        if options["all_users"]:
            users = UserProfile.objects.all()
        elif options["one_realm"]:
            if not args:
                print "Please specify which realm to process."
                exit(1)
            users = UserProfile.objects.filter(realm__domain=args[0])
        else:
            users = [get_user_profile_by_email(args[0])]


        for user_profile in users:
            pointer = user_profile.pointer
            msgs = UserMessage.objects.filter(user_profile=user_profile,
                                              flags=~UserMessage.flags.read,
                                              message__id__lte=pointer)
            if not options["for_real"]:
                for msg in msgs:
                    print "Adding read flag to msg: %s - %s/%s (own msg: %s)"   \
                            % (user_profile.email,
                               msg.message.id,
                               msg.id,
                               msg.message.sender.email == user_profile.email)
            else:
                def do_update(batch):
                    with transaction.commit_on_success():
                        UserMessage.objects.filter(id__in=batch).update(flags=models.F('flags').bitor(UserMessage.flags.read))

                mids = [m.id for m in msgs]
                utils.run_in_batches(mids, 250, do_update, 3, logging.info)

        if not options["for_real"]:
            print "Dry run completed. Run with --for-real to change message flags."
            exit(1)

        print "User messages updated."

from __future__ import absolute_import

import datetime
import pytz

from django.core.management.base import BaseCommand
from django.db.models import Count
from zephyr.models import UserProfile, Realm, Stream, Message, Recipient, UserActivity, \
    Subscription, UserMessage

MOBILE_CLIENT_LIST = ["Android", "iPhone"]
HUMAN_CLIENT_LIST = MOBILE_CLIENT_LIST + ["website"]

human_messages = Message.objects.filter(sending_client__name__in=HUMAN_CLIENT_LIST)

class Command(BaseCommand):
    help = "Generate statistics on realm activity."

    def active_users(self, realm):
        # Has been active (on the website, for now) in the last 7 days.
        activity_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=7)
        return [activity.user_profile for activity in \
                    UserActivity.objects.filter(user_profile__realm=realm,
                                                user_profile__is_active=True,
                                                last_visit__gt=activity_cutoff,
                                                query="/json/update_pointer",
                                                client__name="website")]

    def messages_sent_by(self, user, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return human_messages.filter(sender=user, pub_date__gt=sent_time_cutoff).count()

    def total_messages(self, realm, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return Message.objects.filter(sender__realm=realm, pub_date__gt=sent_time_cutoff).count()

    def human_messages(self, realm, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return human_messages.filter(sender__realm=realm, pub_date__gt=sent_time_cutoff).count()

    def api_messages(self, realm, days_ago):
        return (self.total_messages(realm, days_ago) - self.human_messages(realm, days_ago))

    def stream_messages(self, realm, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return human_messages.filter(sender__realm=realm, pub_date__gt=sent_time_cutoff,
                                     recipient__type=Recipient.STREAM).count()

    def private_messages(self, realm, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return human_messages.filter(sender__realm=realm, pub_date__gt=sent_time_cutoff).exclude(
            recipient__type=Recipient.STREAM).exclude(recipient__type=Recipient.HUDDLE).count()

    def group_private_messages(self, realm, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return human_messages.filter(sender__realm=realm, pub_date__gt=sent_time_cutoff).exclude(
            recipient__type=Recipient.STREAM).exclude(recipient__type=Recipient.PERSONAL).count()

    def report_percentage(self, numerator, denominator, text):
        if not denominator:
            fraction = 0.0
        else:
            fraction = numerator / float(denominator)
        print "%.2f%% of" % (fraction * 100,), text

    def handle(self, *args, **options):
        if args:
            try:
                realms = [Realm.objects.get(domain=domain) for domain in args]
            except Realm.DoesNotExist, e:
                print e
                exit(1)
        else:
            realms = Realm.objects.all()

        for realm in realms:
            print realm.domain

            user_profiles = UserProfile.objects.filter(realm=realm, is_active=True)
            active_users = self.active_users(realm)
            num_active = len(active_users)

            print "%d active users (%d total)" % (num_active, len(user_profiles))
            streams = Stream.objects.filter(realm=realm).extra(
                tables=['zephyr_subscription', 'zephyr_recipient'],
                where=['zephyr_subscription.recipient_id = zephyr_recipient.id',
                       'zephyr_recipient.type = 2',
                       'zephyr_recipient.type_id = zephyr_stream.id',
                       'zephyr_subscription.active = true']).annotate(count=Count("name"))
            print "%d streams" % (streams.count(),)

            for days_ago in (1, 7, 30):
                print "In last %d days, users sent:" % (days_ago,)
                sender_quantities = [self.messages_sent_by(user, days_ago) for user in user_profiles]
                for quantity in sorted(sender_quantities, reverse=True):
                    print quantity,
                print ""

                print "%d stream messages" % (self.stream_messages(realm, days_ago),)
                print "%d one-on-one private messages" % (self.private_messages(realm, days_ago),)
                print "%d messages sent via the API" % (self.api_messages(realm, days_ago),)
                print "%d group private messages" % (self.group_private_messages(realm, days_ago),)

            num_notifications_enabled = len(filter(lambda x: x.enable_desktop_notifications == True,
                                                   active_users))
            self.report_percentage(num_notifications_enabled, num_active,
                                   "active users have desktop notifications enabled")

            num_enter_sends = len(filter(lambda x: x.enter_sends, active_users))
            self.report_percentage(num_enter_sends, num_active,
                                   "active users have enter-sends")

            all_message_count = human_messages.filter(sender__realm=realm).count()
            multi_paragraph_message_count = human_messages.filter(
                sender__realm=realm, content__contains="\n\n").count()
            self.report_percentage(multi_paragraph_message_count, all_message_count,
                                   "all messages are multi-paragraph")

            # Starred messages
            starrers = UserMessage.objects.filter(user_profile__in=user_profiles,
                                                  flags=UserMessage.flags.starred).values(
                "user_profile").annotate(count=Count("user_profile"))
            print "%d users have starred %d messages" % (
                len(starrers), sum([elt["count"] for elt in starrers]))

            active_user_subs = Subscription.objects.filter(
                user_profile__in=user_profiles, active=True)

            # Streams not in home view
            non_home_view = active_user_subs.filter(in_home_view=False).values(
                "user_profile").annotate(count=Count("user_profile"))
            print "%d users have %d streams not in home view" % (
                len(non_home_view), sum([elt["count"] for elt in non_home_view]))

            # Code block markup
            markup_messages = human_messages.filter(
                sender__realm=realm, content__contains="~~~").values(
                "sender").annotate(count=Count("sender"))
            print "%d users have used code block markup on %s messages" % (
                len(markup_messages), sum([elt["count"] for elt in markup_messages]))

            # Notifications for stream messages
            notifications = active_user_subs.filter(notifications=True).values(
                "user_profile").annotate(count=Count("user_profile"))
            print "%d users receive desktop notifications for %d streams" % (
                len(notifications), sum([elt["count"] for elt in notifications]))

            print ""

from __future__ import absolute_import

from django.core.management.base import BaseCommand

from zephyr.models import UserPresence, UserActivity
from zephyr.lib.utils import statsd, statsd_key

from datetime import datetime, timedelta
from collections import defaultdict

class Command(BaseCommand):
    help = """Sends active user statistics to statsd.

    Run as a cron job that runs every 10 minutes."""

    def handle(self, *args, **options):
        # Get list of all active users in the last 1 week
        cutoff = datetime.now() - timedelta(minutes=30, hours=168)

        users = UserPresence.objects.select_related().filter(timestamp__gt=cutoff)

        # Calculate 10min, 2hrs, 12hrs, 1day, 2 business days (TODO business days), 1 week bucket of stats
        hour_buckets = [0.16, 2, 12, 24, 48, 168]
        user_info = defaultdict(dict)

        for last_presence in users:
            if last_presence.status == UserPresence.IDLE:
                known_active = last_presence.timestamp - timedelta(minutes=30)
            else:
                known_active = last_presence.timestamp

            for bucket in hour_buckets:
                if not bucket in user_info[last_presence.user_profile.realm.domain]:
                    user_info[last_presence.user_profile.realm.domain][bucket] = []
                if datetime.now(known_active.tzinfo) - known_active < timedelta(hours=bucket):
                    user_info[last_presence.user_profile.realm.domain][bucket].append(last_presence.user_profile.email)

        for realm, buckets in user_info.items():
            print("Realm %s" % realm)
            for hr, users in sorted(buckets.items()):
                print("\tUsers for %s: %s" % (hr, len(users)))
                statsd.gauge("users.active.%s.%shr" %  (statsd_key(realm, True), statsd_key(hr, True)), len(users))

        # Also do stats for how many users have been reading the app.
        users_reading = UserActivity.objects.select_related().filter(query="/json/update_message_flags")
        user_info = defaultdict(dict)
        for activity in users_reading:
            for bucket in hour_buckets:
                if not bucket in user_info[activity.user_profile.realm.domain]:
                    user_info[activity.user_profile.realm.domain][bucket] = []
                if datetime.now(activity.last_visit.tzinfo) - activity.last_visit < timedelta(hours=bucket):
                    user_info[activity.user_profile.realm.domain][bucket].append(activity.user_profile.email)
        for realm, buckets in user_info.items():
            print("Realm %s" % realm)
            for hr, users in sorted(buckets.items()):
                print("\tUsers reading for %s: %s" % (hr, len(users)))
                statsd.gauge("users.reading.%s.%shr" %  (statsd_key(realm, True), statsd_key(hr, True)), len(users))

from __future__ import absolute_import

from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = """Send some stats to statsd.

Usage: python manage.py send_stats [incr|decr|timing|timer|gauge] name val"""

    def handle(self, *args, **options):
        if len(args) != 3:
            print "Usage: python manage.py send_stats [incr|decr|timing|timer|gauge] name val"
            exit(1)

        operation = args[0]
        name = args[1]
        val = args[2]

        if settings.USING_STATSD:
            from statsd import statsd

            func = getattr(statsd, operation)
            func(name, val)

from __future__ import absolute_import

import os
import sys
import datetime
import tempfile
import traceback
import ujson
from os import path

from django.core.management.base import BaseCommand
from zephyr.retention_policy     import should_expunge_from_log

now = datetime.datetime.now()

def copy_retained_messages(infile, outfile):
    """Copy messages from infile to outfile which should be retained
       according to policy."""
    for ln in infile:
        msg = ujson.loads(ln)
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
            except KeyboardInterrupt:
                raise
            except:
                print >>sys.stderr, 'WARNING: Could not expunge from', infile
                traceback.print_exc()

from __future__ import absolute_import

from django.core.management.base import BaseCommand

from zephyr.models import get_user_profile_by_email, get_prereg_user_by_email
from zephyr.lib.queue import SimpleQueueClient
from zephyr.lib.actions import do_send_confirmation_email

class Command(BaseCommand):
    """
    Send confirmation e-mails to invited users.

    This command processes events from the `invites` queue.
    """
    def subscribe(self, ch, method, properties, data):
        invitee = get_prereg_user_by_email(data["email"])
        referrer = get_user_profile_by_email(data["referrer_email"])
        do_send_confirmation_email(invitee, referrer)

    def handle(self, *args, **options):
        q = SimpleQueueClient()
        q.register_json_consumer("invites", self.subscribe)
        q.start_consuming()

from __future__ import absolute_import

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import Recipient, Message
from zephyr.lib.timestamp import timestamp_to_datetime
import datetime
import time
import logging

def compute_stats(log_level):
    logger = logging.getLogger()
    logger.setLevel(log_level)

    one_week_ago = timestamp_to_datetime(time.time()) - datetime.timedelta(weeks=1)
    mit_query = Message.objects.filter(sender__realm__domain="mit.edu",
                                       recipient__type=Recipient.STREAM,
                                       pub_date__gt=one_week_ago)
    for bot_sender_start in ["imap.", "rcmd.", "sys."]:
        mit_query = mit_query.exclude(sender__email__startswith=(bot_sender_start))
    # Filtering for "/" covers tabbott/extra@ and all the daemon/foo bots.
    mit_query = mit_query.exclude(sender__email__contains=("/"))
    mit_query = mit_query.exclude(sender__email__contains=("aim.com"))
    mit_query = mit_query.exclude(
        sender__email__in=["rss@mit.edu", "bash@mit.edu", "apache@mit.edu",
                           "bitcoin@mit.edu", "lp@mit.edu", "clocks@mit.edu",
                           "root@mit.edu", "nagios@mit.edu",
                           "www-data|local-realm@mit.edu"])
    user_counts = {}
    for m in mit_query.select_related("sending_client", "sender"):
        email = m.sender.email
        user_counts.setdefault(email, {})
        user_counts[email].setdefault(m.sending_client.name, 0)
        user_counts[email][m.sending_client.name] += 1

    total_counts = {}
    total_user_counts = {}
    for email, counts in user_counts.items():
        total_user_counts.setdefault(email, 0)
        for client_name, count in counts.items():
            total_counts.setdefault(client_name, 0)
            total_counts[client_name] += count
            total_user_counts[email] += count

    logging.debug("%40s | %10s | %s" % ("User", "Messages", "Percentage Humbug"))
    top_percents = {}
    for size in [10, 25, 50, 100, 200, len(total_user_counts.keys())]:
        top_percents[size] = 0
    for i, email in enumerate(sorted(total_user_counts.keys(),
                                     key=lambda x: -total_user_counts[x])):
        percent_humbug = round(100 - (user_counts[email].get("zephyr_mirror", 0)) * 100. /
                               total_user_counts[email], 1)
        for size in top_percents.keys():
            top_percents.setdefault(size, 0)
            if i < size:
                top_percents[size] += (percent_humbug * 1.0 / size)

        logging.debug("%40s | %10s | %s%%" % (email, total_user_counts[email],
                                              percent_humbug))

    logging.info("")
    for size in sorted(top_percents.keys()):
        logging.info("Top %6s | %s%%" % (size, round(top_percents[size], 1)))

    grand_total = sum(total_counts.values())
    print grand_total
    logging.info("%15s | %s" % ("Client", "Percentage"))
    for client in total_counts.keys():
        logging.info("%15s | %s%%" % (client, round(100. * total_counts[client] / grand_total, 1)))

class Command(BaseCommand):
    option_list = BaseCommand.option_list + \
        (make_option('--verbose', default=False, action='store_true'),)

    help = "Compute statistics on MIT Zephyr usage."

    def handle(self, *args, **options):
        level = logging.INFO
        if options["verbose"]:
            level = logging.DEBUG
        compute_stats(level)

from __future__ import absolute_import

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import UserActivity, get_client, get_user_profile_by_email
import ujson
from zephyr.lib.timestamp import datetime_to_timestamp, timestamp_to_datetime

def dump():
    pointers = []
    for activity in UserActivity.objects.select_related("user_profile__email",
                                                        "client__name").all():
        pointers.append((activity.user_profile.email, activity.client.name,
                         activity.query, activity.count,
                         datetime_to_timestamp(activity.last_visit)))
    file("dumped-activity", "w").write(ujson.dumps(pointers) + "\n")

def restore(change):
    for (email, client_name, query, count, timestamp) in ujson.loads(file("dumped-activity").read()):
        user_profile = get_user_profile_by_email(email)
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

from __future__ import absolute_import

from django.conf import settings
import pika
import logging
import ujson
import random
import time
import threading
import atexit
from collections import defaultdict

from zephyr.lib.utils import statsd

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

    def _reconnect_consumer_callbacks(self):
        for queue, consumers in self.consumers.items():
            for consumer in consumers:
                self.log.info("Queue reconnecting saved consumer %s to queue %s" % (consumer, queue))
                self.ensure_queue(queue, lambda: self.channel.basic_consume(
                                                        consumer,
                                                        queue=queue,
                                                        consumer_tag=self._generate_ctag(queue)))

    def close(self):
        if self.connection:
            self.connection.close()

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
        def do_publish():
            self.channel.basic_publish(
                            exchange='',
                            routing_key=queue_name,
                            properties=pika.BasicProperties(delivery_mode=2),
                            body=body)

            statsd.incr("rabbitmq.publish.%s" % (queue_name,))

        self.ensure_queue(queue_name, do_publish)

    def json_publish(self, queue_name, body):
        try:
            return self.publish(queue_name, ujson.dumps(body))
        except (AttributeError, pika.exceptions.AMQPConnectionError):
            self.log.warning("Failed to send to rabbitmq, trying to reconnect and send again")
            self._reconnect()

            return self.publish(queue_name, ujson.dumps(body))

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
            return callback(ch, method, properties, ujson.loads(body))
        return self.register_consumer(queue_name, wrapped_callback)

    def drain_queue(self, queue_name, json=False):
        "Returns all messages in the desired queue"
        messages =[]
        def opened():
            while True:
                (meta, _, message) = self.channel.basic_get(queue_name)

                if not message:
                    break;

                self.channel.basic_ack(meta.delivery_tag)
                if json:
                    message = ujson.loads(message)
                messages.append(message)

        self.ensure_queue(queue_name, opened)
        return messages

    def start_consuming(self):
        self.channel.start_consuming()

    def stop_consuming(self):
        self.channel.stop_consuming()

# Patch pika.adapters.TornadoConnection so that a socket error doesn't
# throw an exception and disconnect the tornado process from the rabbitmq
# queue. Instead, just re-connect as usual
class ExceptionFreeTornadoConnection(pika.adapters.TornadoConnection):
    def _adapter_disconnect(self):
        try:
            super(ExceptionFreeTornadoConnection, self)._adapter_disconnect()
        except (pika.exceptions.ProbableAuthenticationError,
                pika.exceptions.ProbableAccessDeniedError,
                pika.exceptions.IncompatibleProtocolError) as e:
            logging.warning("Caught exception '%r' in ExceptionFreeTornadoConnection when \
calling _adapter_disconnect, ignoring" % (e,))


class TornadoQueueClient(SimpleQueueClient):
    # Based on:
    # https://pika.readthedocs.org/en/0.9.8/examples/asynchronous_consumer_example.html
    def __init__(self):
        super(TornadoQueueClient, self).__init__()
        self._on_open_cbs = []

    def _connect(self, on_open_cb = None):
        self.log.info("Beginning TornadoQueueClient connection")
        if on_open_cb:
            self._on_open_cbs.append(on_open_cb)
        self.connection = ExceptionFreeTornadoConnection(
            self._get_parameters(),
            on_open_callback = self._on_open,
            stop_ioloop_on_close = False)
        self.connection.add_on_close_callback(self._on_connection_closed)

    def _reconnect(self):
        self.connection = None
        self.channel = None
        self.queues = set()
        self._connect()

    def _on_open(self, connection):
        self.connection.channel(
            on_open_callback = self._on_channel_open)

    def _on_channel_open(self, channel):
        self.channel = channel
        for callback in self._on_open_cbs:
            callback()
        self._reconnect_consumer_callbacks()
        self.log.info('TornadoQueueClient connected')

    def _on_connection_closed(self, method_frame):
        self.log.warning("TornadoQueueClient lost connection to RabbitMQ, reconnecting...")
        from tornado import ioloop

        # Try to reconnect in two seconds
        retry_seconds = 2
        def on_timeout():
            try:
                self._reconnect()
            except pika.exceptions.AMQPConnectionError:
                self.log.critical("Failed to reconnect to RabbitMQ, retrying...")
                ioloop.IOLoop.instance().add_timeout(time.time() + retry_seconds, on_timeout)

        ioloop.IOLoop.instance().add_timeout(time.time() + retry_seconds, on_timeout)

    def ensure_queue(self, queue_name, callback):
        def finish(frame):
            self.queues.add(queue_name)
            callback()

        if queue_name not in self.queues:
            # If we're not connected yet, send this message
            # once we have created the channel
            if not self.ready():
                self._on_open_cbs.append(lambda: self.ensure_queue(queue_name, callback))
                return

            self.channel.queue_declare(queue=queue_name, durable=True, callback=finish)
        else:
            callback()

    def register_consumer(self, queue_name, consumer):
        def wrapped_consumer(ch, method, properties, body):
            consumer(ch, method, properties, body)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        if not self.ready():
            self.consumers[queue_name].add(wrapped_consumer)
            return

        self.consumers[queue_name].add(wrapped_consumer)
        self.ensure_queue(queue_name,
            lambda: self.channel.basic_consume(wrapped_consumer, queue=queue_name,
                consumer_tag=self._generate_ctag(queue_name)))

if settings.RUNNING_INSIDE_TORNADO and settings.USING_RABBITMQ:
    queue_client = TornadoQueueClient()
elif settings.USING_RABBITMQ:
    queue_client = SimpleQueueClient()

def setup_tornado_rabbitmq():
    # When tornado is shut down, disconnect cleanly from rabbitmq
    if settings.USING_RABBITMQ:
        atexit.register(lambda: queue_client.close())

# We using a simple lock to prevent multiple RabbitMQ messages being
# sent to the SimpleQueueClient at the same time; this is a workaround
# for an issue with the pika BlockingConnection where using
# BlockingConnection for multiple queues causes the channel to
# randomly close.
queue_lock = threading.RLock()

def queue_json_publish(queue_name, event, processor):
    with queue_lock:
        if settings.USING_RABBITMQ:
            queue_client.json_publish(queue_name, event)
        else:
            processor(event)


from __future__ import absolute_import

from django.contrib.auth.models import UserManager
from django.utils import timezone
from zephyr.models import UserProfile, Recipient, Subscription
import base64
import ujson
import os
import string

# The ordered list of onboarding steps we want new users to complete. If the
# steps are changed here, they must also be changed in onboarding.js.
onboarding_steps = ["sent_stream_message", "sent_private_message", "made_app_sticky"]

def create_onboarding_steps_blob():
    return ujson.dumps([(step, False) for step in onboarding_steps])

def random_api_key():
    choices = string.ascii_letters + string.digits
    altchars = ''.join([choices[ord(os.urandom(1)) % 62] for _ in range(2)])
    return base64.b64encode(os.urandom(24), altchars=altchars)

# create_user_profile is based on Django's User.objects.create_user,
# except that we don't save to the database so it can used in
# bulk_creates
#
# Only use this for bulk_create -- for normal usage one should use
# create_user (below) which will also make the Subscription and
# Recipient objects
def create_user_profile(realm, email, password, active, bot, full_name, short_name, bot_owner):
    now = timezone.now()
    email = UserManager.normalize_email(email)
    user_profile = UserProfile(email=email, is_staff=False, is_active=active,
                               full_name=full_name, short_name=short_name,
                               last_login=now, date_joined=now, realm=realm,
                               pointer=-1, is_bot=bot, bot_owner=bot_owner,
                               onboarding_steps=create_onboarding_steps_blob())

    if bot or not active:
        user_profile.set_unusable_password()
    else:
        user_profile.set_password(password)

    user_profile.api_key = random_api_key()
    return user_profile

def create_user(email, password, realm, full_name, short_name,
                active=True, bot=False, bot_owner=None,
                avatar_source=UserProfile.AVATAR_FROM_GRAVATAR):
    user_profile = create_user_profile(realm, email, password, active, bot,
                                       full_name, short_name, bot_owner)
    user_profile.avatar_source = avatar_source
    user_profile.save()
    recipient = Recipient.objects.create(type_id=user_profile.id,
                                         type=Recipient.PERSONAL)
    Subscription.objects.create(user_profile=user_profile, recipient=recipient)
    return user_profile

from __future__ import absolute_import

def last_n(n, query_set):
    """Get the last n results from a Django QuerySet, in a semi-efficient way.
       Returns a list."""

    # We don't use reversed() because we would get a generator,
    # which causes bool(last_n(...)) to be True always.

    xs = list(query_set.reverse()[:n])
    xs.reverse()
    return xs

from __future__ import absolute_import

from django.conf import settings
from django.template.defaultfilters import slugify

from zephyr.lib.avatar import user_avatar_hash

from boto.s3.key import Key
from boto.s3.connection import S3Connection
from mimetypes import guess_type, guess_extension

import base64
import os

# Performance Note:
#
# For writing files to S3, the file could either be stored in RAM
# (if it is less than 2.5MiB or so) or an actual temporary file on disk.
#
# Because we set FILE_UPLOAD_MAX_MEMORY_SIZE to 0, only the latter case
# should occur in practice.
#
# This is great, because passing the pseudofile object that Django gives
# you to boto would be a pain.

def gen_s3_key(user_profile, name):
    split_name = name.split('.')
    base = ".".join(split_name[:-1])
    extension = split_name[-1]

    # To come up with a s3 key we randomly generate a "directory". The "file
    # name" is the original filename provided by the user run through Django's
    # slugify.

    return base64.urlsafe_b64encode(os.urandom(60)) + "/" + slugify(base) + "." + slugify(extension)

def upload_image_to_s3(
        bucket_name,
        file_name,
        content_type,
        user_profile_id,
        user_file,
    ):

    conn = S3Connection(settings.S3_KEY, settings.S3_SECRET_KEY)
    key = Key(conn.get_bucket(bucket_name))
    key.key = file_name
    key.set_metadata("user_profile_id", str(user_profile_id))

    if content_type:
        headers = {'Content-Type': content_type}
    else:
        headers = None

    contents = user_file.read()
    key.set_contents_from_string(contents, headers=headers)

def get_file_info(request, user_file):
    uploaded_file_name = user_file.name
    content_type = request.GET.get('mimetype')
    if content_type is None:
        content_type = guess_type(uploaded_file_name)[0]
    else:
        uploaded_file_name = uploaded_file_name + guess_extension(content_type)
    return uploaded_file_name, content_type


def upload_message_image(request, user_file, user_profile):
    uploaded_file_name, content_type = get_file_info(request, user_file)
    bucket_name = settings.S3_BUCKET
    s3_file_name = gen_s3_key(user_profile, uploaded_file_name)
    upload_image_to_s3(
            bucket_name,
            s3_file_name,
            content_type,
            user_profile.id,
            user_file,
    )
    return "https://%s.s3.amazonaws.com/%s" % (bucket_name, s3_file_name)

def upload_avatar_image(user_file, user_profile, email):
    content_type = guess_type(user_file.name)[0]
    bucket_name = settings.S3_AVATAR_BUCKET
    s3_file_name = user_avatar_hash(email)
    upload_image_to_s3(
        bucket_name,
        s3_file_name,
        content_type,
        user_profile.id,
        user_file,
    )
    # See avatar_url in avatar.py for URL.  (That code also handles the case
    # that users use gravatar.)

from __future__ import absolute_import

# This file needs to be different from cache.py because cache.py
# cannot import anything from zephyr.models or we'd have an import
# loop
from django.conf import settings
from zephyr.models import Message, UserProfile, Stream, get_stream_cache_key, \
    Recipient, get_recipient_cache_key, Client, get_client_cache_key, \
    Huddle, huddle_hash_cache_key
from zephyr.lib.cache import cache_with_key, cache_set, message_cache_key, \
    user_profile_by_email_cache_key, user_profile_by_id_cache_key, \
    get_memcached_time, get_memcached_requests, cache_set_many
from django.utils.importlib import import_module
from django.contrib.sessions.models import Session
import logging
from django.db.models import Q

MESSAGE_CACHE_SIZE = 75000

def cache_save_message(message):
    cache_set(message_cache_key(message.id), message, timeout=3600*24)

@cache_with_key(message_cache_key, timeout=3600*24)
def cache_get_message(message_id):
    return Message.objects.select_related().get(id=message_id)

def message_fetch_objects():
    max_id = Message.objects.only('id').order_by("-id")[0].id
    return Message.objects.select_related().filter(~Q(sender__email='tabbott/extra@mit.edu'),
                                                    id__gt=max_id - MESSAGE_CACHE_SIZE)

def message_cache_items(items_for_memcached, message):
    items_for_memcached[message_cache_key(message.id)] = (message,)

def user_cache_items(items_for_memcached, user_profile):
    items_for_memcached[user_profile_by_email_cache_key(user_profile.email)] = (user_profile,)
    items_for_memcached[user_profile_by_id_cache_key(user_profile.id)] = (user_profile,)

def stream_cache_items(items_for_memcached, stream):
    items_for_memcached[get_stream_cache_key(stream.name, stream.realm_id)] = (stream,)

def client_cache_items(items_for_memcached, client):
    items_for_memcached[get_client_cache_key(client.name)] = (client,)

def huddle_cache_items(items_for_memcached, huddle):
    items_for_memcached[huddle_hash_cache_key(huddle.huddle_hash)] = (huddle,)

def recipient_cache_items(items_for_memcached, recipient):
    items_for_memcached[get_recipient_cache_key(recipient.type, recipient.type_id)] = (recipient,)

session_engine = import_module(settings.SESSION_ENGINE)
def session_cache_items(items_for_memcached, session):
    store = session_engine.SessionStore(session_key=session.session_key)
    items_for_memcached[store.cache_key] = store.decode(session.session_data)

# Format is (objects query, items filler function, timeout, batch size)
#
# The objects queries are put inside lambdas to prevent Django from
# doing any setup for things we're unlikely to use (without the lambda
# wrapper the below adds an extra 3ms or so to startup time for
# anything importing this file).
cache_fillers = {
    'user': (lambda: UserProfile.objects.select_related().all(), user_cache_items, 3600*24*7, 10000),
    'client': (lambda: Client.objects.select_related().all(), client_cache_items, 3600*24*7, 10000),
    'recipient': (lambda: Recipient.objects.select_related().all(), recipient_cache_items, 3600*24*7, 10000),
    'stream': (lambda: Stream.objects.select_related().all(), stream_cache_items, 3600*24*7, 10000),
    'message': (message_fetch_objects, message_cache_items, 3600 * 24, 1000),
    'huddle': (lambda: Huddle.objects.select_related().all(), huddle_cache_items, 3600*24*7, 10000),
    'session': (lambda: Session.objects.all(), session_cache_items, 3600*24*7, 10000),
    }

def fill_memcached_cache(cache):
    memcached_time_start = get_memcached_time()
    memcached_requests_start = get_memcached_requests()
    items_for_memcached = {}
    (objects, items_filler, timeout, batch_size) = cache_fillers[cache]
    count = 0
    for obj in objects():
        items_filler(items_for_memcached, obj)
        count += 1
        if (count % batch_size == 0):
            cache_set_many(items_for_memcached, timeout=3600*24)
            items_for_memcached = {}
    cache_set_many(items_for_memcached, timeout=3600*24*7)
    logging.info("Succesfully populated %s cache!  Consumed %s memcached queries (%s time)" % \
                     (cache, get_memcached_requests() - memcached_requests_start,
                      round(get_memcached_time() - memcached_time_start, 2)))

from __future__ import absolute_import

from django.conf import settings

import hashlib
import base64

def initial_password(email):
    """Given an email address, returns the initial password for that account, as
       created by populate_db."""

    digest = hashlib.sha256(settings.INITIAL_PASSWORD_SALT + email).digest()
    return base64.b64encode(digest)[:16]

from __future__ import absolute_import

import sys
import time
import ctypes
import threading

# Based on http://code.activestate.com/recipes/483752/

class TimeoutExpired(Exception):
    '''Exception raised when a function times out.'''
    def __str__(self):
        return 'Function call timed out.'

def timeout(timeout, func, *args, **kwargs):
    '''Call the function in a separate thread.
       Return its return value, or raise an exception,
       within approximately 'timeout' seconds.

       The function may receive a TimeoutExpired exception
       anywhere in its code, which could have arbitrary
       unsafe effects (resources not released, etc.).
       It might also fail to receive the exception and
       keep running in the background even though
       timeout() has returned.

       This may also fail to interrupt functions which are
       stuck in a long-running primitive interpreter
       operation.'''

    class TimeoutThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.result = None
            self.exc_info = None

            # Don't block the whole program from exiting
            # if this is the only thread left.
            self.daemon = True

        def run(self):
            try:
                self.result = func(*args, **kwargs)
            except BaseException:
                self.exc_info = sys.exc_info()

        def raise_async_timeout(self):
            # Called from another thread.
            # Attempt to raise a TimeoutExpired in the thread represented by 'self'.
            tid = ctypes.c_long(self.ident)
            result = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                tid, ctypes.py_object(TimeoutExpired))
            if result > 1:
                # "if it returns a number greater than one, you're in trouble,
                # and you should call it again with exc=NULL to revert the effect"
                #
                # I was unable to find the actual source of this quote, but it
                # appears in the many projects across the Internet that have
                # copy-pasted this recipe.
                ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)

    thread = TimeoutThread()
    thread.start()
    thread.join(timeout)

    if thread.isAlive():
        # Gamely try to kill the thread, following the dodgy approach from
        # http://stackoverflow.com/a/325528/90777
        #
        # We need to retry, because an async exception received while the
        # thread is in a system call is simply ignored.
        for i in xrange(10):
            thread.raise_async_timeout()
            time.sleep(0.1)
            if not thread.isAlive():
                break
        raise TimeoutExpired

    if thread.exc_info:
        # Raise the original stack trace so our error messages are more useful.
        # from http://stackoverflow.com/a/4785766/90777
        raise thread.exc_info[0], thread.exc_info[1], thread.exc_info[2]
    return thread.result

from __future__ import absolute_import

from django.conf import settings

import redis
import time
import logging

from itertools import izip

# Implement a rate-limiting scheme inspired by the one described here, but heavily modified
# http://blog.domaintools.com/2013/04/rate-limiting-with-redis/

client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
rules = settings.RATE_LIMITING_RULES
def _rules_for_user(user):
    if user.rate_limits != "":
        return [[int(l) for l in limit.split(':')] for limit in user.rate_limits.split(',')]
    return rules

def redis_key(user, domain):
    """Return the redis keys for this user"""
    return ["ratelimit:%s:%s:%s" % (user.id, domain, keytype) for keytype in ['list', 'zset', 'block']]

def max_api_calls(user):
    "Returns the API rate limit for the highest limit"
    return _rules_for_user(user)[-1][1]

def max_api_window(user):
    "Returns the API time window for the highest limit"
    return _rules_for_user(user)[-1][0]

def add_ratelimit_rule(range_seconds, num_requests):
    "Add a rate-limiting rule to the ratelimiter"
    global rules

    rules.append((range_seconds, num_requests))
    rules.sort(cmp=lambda x, y: x[0] < y[0])

def remove_ratelimit_rule(range_seconds, num_requests):
    global rules
    rules = filter(lambda x: x[0] != range_seconds and x[1] != num_requests, rules)

def block_user(user, seconds, domain='all'):
    "Manually blocks a user id for the desired number of seconds"
    _, _, blocking_key = redis_key(user, domain)
    with client.pipeline() as pipe:
        pipe.set(blocking_key, 1)
        pipe.expire(blocking_key, seconds)
        pipe.execute()

def unblock_user(user, domain='all'):
    _, _, blocking_key = redis_key(user, domain)
    client.delete(blocking_key)

def clear_user_history(user, domain='all'):
    '''
    This is only used by test code now, where it's very helpful in
    allowing us to run tests quickly, by giving a user a clean slate.
    '''
    for key in redis_key(user, domain):
        client.delete(key)

def _get_api_calls_left(user, domain, range_seconds, max_calls):
    list_key, set_key, _ = redis_key(user, domain)
    # Count the number of values in our sorted set
    # that are between now and the cutoff
    now = time.time()
    boundary = now - range_seconds

    with client.pipeline() as pipe:
        # Count how many API calls in our range have already been made
        pipe.zcount(set_key, boundary, now)
        # Get the newest call so we can calculate when the ratelimit
        # will reset to 0
        pipe.lindex(list_key, 0)

        results = pipe.execute()

    count = results[0]
    newest_call = results[1]

    calls_left = max_calls - count
    if newest_call is not None:
        time_reset = now + (range_seconds - (now - float(newest_call)))
    else:
        time_reset = now

    return calls_left, time_reset

def api_calls_left(user, domain='all'):
    """Returns how many API calls in this range this client has, as well as when
       the rate-limit will be reset to 0"""
    max_window = _rules_for_user(user)[-1][0]
    max_calls = _rules_for_user(user)[-1][1]
    return _get_api_calls_left(user, domain, max_window, max_calls)

def is_ratelimited(user, domain='all'):
    "Returns a tuple of (rate_limited, time_till_free)"
    list_key, set_key, blocking_key = redis_key(user, domain)

    rules = _rules_for_user(user)

    if len(rules) == 0:
        return False, 0.0

    # Go through the rules from shortest to longest,
    # seeing if this user has violated any of them. First
    # get the timestamps for each nth items
    with client.pipeline() as pipe:
        for _, request_count in rules:
            pipe.lindex(list_key, request_count - 1) # 0-indexed list

        # Get blocking info
        pipe.get(blocking_key)
        pipe.ttl(blocking_key)

        rule_timestamps = pipe.execute()

    # Check if there is a manual block on this API key
    blocking_ttl = rule_timestamps.pop()
    key_blocked = rule_timestamps.pop()

    if key_blocked is not None:
        # We are manually blocked. Report for how much longer we will be
        if blocking_ttl is None:
            blocking_ttl = 0.5
        else:
            blocking_ttl = int(blocking_ttl)
        return True, blocking_ttl

    now = time.time()
    for timestamp, (range_seconds, num_requests) in izip(rule_timestamps, rules):
        # Check if the nth timestamp is newer than the associated rule. If so,
        # it means we've hit our limit for this rule
        if timestamp is None:
            continue

        timestamp = float(timestamp)
        boundary = timestamp + range_seconds
        if boundary > now:
            free = boundary - now
            return True, free

    # No api calls recorded yet
    return False, 0.0

def incr_ratelimit(user, domain='all'):
    """Increases the rate-limit for the specified user"""
    list_key, set_key, _ = redis_key(user, domain)
    now = time.time()

    # If we have no rules, we don't store anything
    if len(rules) == 0:
        return

    # Start redis transaction
    with client.pipeline() as pipe:
        count = 0
        while True:
            try:
                # To avoid a race condition between getting the element we might trim from our list
                # and removing it from our associated set, we abort this whole transaction if
                # another agent manages to change our list out from under us
                # When watching a value, the pipeline is set to Immediate mode
                pipe.watch(list_key)

                # Get the last elem that we'll trim (so we can remove it from our sorted set)
                last_val = pipe.lindex(list_key, max_api_calls(user) - 1)

                # Restart buffered execution
                pipe.multi()

                # Add this timestamp to our list
                pipe.lpush(list_key, now)

                # Trim our list to the oldest rule we have
                pipe.ltrim(list_key, 0, max_api_calls(user) - 1)

                # Add our new value to the sorted set that we keep
                # We need to put the score and val both as timestamp,
                # as we sort by score but remove by value
                pipe.zadd(set_key, now, now)

                # Remove the trimmed value from our sorted set, if there was one
                if last_val is not None:
                    pipe.zrem(set_key, last_val)

                # Set the TTL for our keys as well
                api_window = max_api_window(user)
                pipe.expire(list_key, api_window)
                pipe.expire(set_key, api_window)

                pipe.execute()

                # If no exception was raised in the execution, there were no transaction conflicts
                break
            except redis.WatchError:
                if count > 10:
                    logging.error("Failed to complete incr_ratelimit transaction without interference 10 times in a row! Aborting rate-limit increment")
                    break
                count += 1

                continue

from __future__ import absolute_import

from functools import wraps

from django.core.cache import cache as djcache
from django.core.cache import get_cache
from django.conf import settings

from zephyr.lib.utils import statsd, statsd_key, make_safe_digest
import time
import base64
import random
import sys
import os
import os.path
import hashlib

memcached_time_start = 0
memcached_total_time = 0
memcached_total_requests = 0

def get_memcached_time():
    return memcached_total_time

def get_memcached_requests():
    return memcached_total_requests

def memcached_stats_start():
    global memcached_time_start
    memcached_time_start = time.time()

def memcached_stats_finish():
    global memcached_total_time
    global memcached_total_requests
    global memcached_time_start
    memcached_total_requests += 1
    memcached_total_time += (time.time() - memcached_time_start)

def get_or_create_key_prefix():
    if settings.TEST_SUITE:
        # This sets the prefix mostly for the benefit of the JS tests.
        # The Python tests overwrite KEY_PREFIX on each test.
        return 'test_suite:' + str(os.getpid()) + ':'

    filename = os.path.join(settings.DEPLOY_ROOT, "memcached_prefix")
    try:
        fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0444)
        prefix = base64.b16encode(hashlib.sha256(str(random.getrandbits(256))).digest())[:32].lower() + ':'
        # This does close the underlying file
        with os.fdopen(fd, 'w') as f:
            f.write(prefix + "\n")
    except OSError:
        # The file already exists
        tries = 1
        while tries < 10:
            with file(filename, 'r') as f:
                prefix = f.readline()[:-1]
            if len(prefix) == 33:
                break
            tries += 1
            prefix = ''
            time.sleep(0.5)

    if not prefix:
        sys.exit("Could not read memcache key prefix file")

    return prefix

KEY_PREFIX = get_or_create_key_prefix()

def bounce_key_prefix_for_testing(test_name):
    global KEY_PREFIX
    KEY_PREFIX = test_name + ':' + str(os.getpid()) + ':'

def get_cache_backend(cache_name):
    if cache_name is None:
        return djcache
    return get_cache(cache_name)

def cache_with_key(keyfunc, cache_name=None, timeout=None, with_statsd_key=None):
    """Decorator which applies Django caching to a function.

       Decorator argument is a function which computes a cache key
       from the original function's arguments.  You are responsible
       for avoiding collisions with other uses of this decorator or
       other uses of caching."""

    def decorator(func):
        @wraps(func)
        def func_with_caching(*args, **kwargs):
            key = keyfunc(*args, **kwargs)

            val = cache_get(key, cache_name=cache_name)

            extra = ""
            if cache_name == 'database':
                extra = ".dbcache"

            if with_statsd_key is not None:
                metric_key = with_statsd_key
            else:
                metric_key = statsd_key(key)

            status = "hit" if val is not None else "miss"
            statsd.incr("cache%s.%s.%s" % (extra, metric_key, status))

            # Values are singleton tuples so that we can distinguish
            # a result of None from a missing key.
            if val is not None:
                return val[0]

            val = func(*args, **kwargs)

            cache_set(key, val, cache_name=cache_name, timeout=timeout)

            return val

        return func_with_caching

    return decorator

def cache_set(key, val, cache_name=None, timeout=None):
    memcached_stats_start()
    cache_backend = get_cache_backend(cache_name)
    ret = cache_backend.set(KEY_PREFIX + key, (val,), timeout=timeout)
    memcached_stats_finish()
    return ret

def cache_get(key, cache_name=None):
    memcached_stats_start()
    cache_backend = get_cache_backend(cache_name)
    ret = cache_backend.get(KEY_PREFIX + key)
    memcached_stats_finish()
    return ret

def cache_get_many(keys, cache_name=None):
    keys = [KEY_PREFIX + key for key in keys]
    memcached_stats_start()
    ret = get_cache_backend(cache_name).get_many(keys)
    memcached_stats_finish()
    return dict([(key[len(KEY_PREFIX):], value) for key, value in ret.items()])

def cache_set_many(items, cache_name=None, timeout=None):
    new_items = {}
    for key in items:
        new_items[KEY_PREFIX + key] = items[key]
    items = new_items
    memcached_stats_start()
    ret = get_cache_backend(cache_name).set_many(items, timeout=timeout)
    memcached_stats_finish()
    return ret

# Required Arguments are as follows:
# * object_ids: The list of object ids to look up
# * cache_key_function: object_id => cache key
# * query_function: [object_ids] => [objects from database]
# Optional keyword arguments:
# * setter: Function to call before storing items to cache (e.g. compression)
# * extractor: Function to call on items returned from cache
#   (e.g. decompression).  Should be the inverse of the setter
#   function.
# * id_fetcher: Function mapping an object from database => object_id
#   (in case we're using a key more complex than obj.id)
# * cache_transformer: Function mapping an object from database =>
#   value for cache (in case the values that we're caching are some
#   function of the objects, not the objects themselves)
def generic_bulk_cached_fetch(cache_key_function, query_function, object_ids,
                              extractor=lambda obj: obj,
                              setter=lambda obj: obj,
                              id_fetcher=lambda obj: obj.id,
                              cache_transformer=lambda obj: obj):
    cache_keys = {}
    for object_id in object_ids:
        cache_keys[object_id] = cache_key_function(object_id)
    cached_objects = cache_get_many([cache_keys[object_id]
                                     for object_id in object_ids])
    for (key, val) in cached_objects.items():
        cached_objects[key] = extractor(cached_objects[key][0])
    needed_ids = [object_id for object_id in object_ids if
                  cache_keys[object_id] not in cached_objects]
    db_objects = query_function(needed_ids)

    items_for_memcached = {}
    for obj in db_objects:
        key = cache_keys[id_fetcher(obj)]
        item = cache_transformer(obj)
        items_for_memcached[key] = (setter(item),)
        cached_objects[key] = item
    if len(items_for_memcached) > 0:
        cache_set_many(items_for_memcached)
    return dict((object_id, cached_objects[cache_keys[object_id]]) for object_id in object_ids
                if cache_keys[object_id] in cached_objects)

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

def message_cache_key(message_id):
    return "message:%d" % (message_id,)

def user_profile_by_email_cache_key(email):
    # See the comment in zephyr/lib/avatar.py:gravatar_hash for why we
    # are proactively encoding email addresses even though they will
    # with high likelihood be ASCII-only for the foreseeable future.
    return 'user_profile_by_email:%s' % (make_safe_digest(email),)

def user_profile_by_id_cache_key(user_profile_id):
    return "user_profile_by_id:%s" % (user_profile_id,)

# Called by models.py to flush the user_profile cache whenever we save
# a user_profile object
def update_user_profile_cache(sender, **kwargs):
    user_profile = kwargs['instance']
    items_for_memcached = {}
    items_for_memcached[user_profile_by_email_cache_key(user_profile.email)] = (user_profile,)
    items_for_memcached[user_profile_by_id_cache_key(user_profile.id)] = (user_profile,)
    cache_set_many(items_for_memcached)

def status_dict_cache_key(user_profile):
    return "status_dict:%d" % (user_profile.realm_id,)

def update_user_presence_cache(sender, **kwargs):
    user_profile = kwargs['instance'].user_profile
    if kwargs['update_fields'] is None or "status" in kwargs['update_fields']:
        # If the status of the user changed, flush the user's realm's
        # entry in the UserPresence cache to avoid giving out stale state
        djcache.delete(KEY_PREFIX + status_dict_cache_key(user_profile))

from __future__ import absolute_import

from django.conf import settings
from django.core import validators
from django.contrib.sessions.models import Session
from zephyr.lib.context_managers import lockfile
from zephyr.models import Realm, Stream, UserProfile, UserActivity, \
    Subscription, Recipient, Message, UserMessage, valid_stream_name, \
    DefaultStream, UserPresence, MAX_SUBJECT_LENGTH, \
    MAX_MESSAGE_LENGTH, get_client, get_stream, get_recipient, get_huddle, \
    get_user_profile_by_id, PreregistrationUser, get_display_recipient, \
    to_dict_cache_key, get_realm, stringify_message_dict, bulk_get_recipients, \
    email_to_domain, email_to_username
from django.db import transaction, IntegrityError
from django.db.models import F, Q
from django.core.exceptions import ValidationError
from django.utils.importlib import import_module
from django.template import loader
from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import utc, is_naive

from confirmation.models import Confirmation

session_engine = import_module(settings.SESSION_ENGINE)

from zephyr.lib.initial_password import initial_password
from zephyr.lib.timestamp import timestamp_to_datetime, datetime_to_timestamp
from zephyr.lib.cache_helpers import cache_save_message
from zephyr.lib.queue import queue_json_publish
from django.utils import timezone
from zephyr.lib.create_user import create_user
from zephyr.lib import bugdown
from zephyr.lib.cache import cache_with_key, \
    user_profile_by_email_cache_key, status_dict_cache_key, cache_set_many
from zephyr.decorator import get_user_profile_by_email, json_to_list, JsonableError, \
     statsd_increment
from zephyr.lib.event_queue import request_event_queue, get_user_events
from zephyr.lib.utils import log_statsd_event, statsd
from zephyr.lib.html_diff import highlight_html_differences

import confirmation.settings

from zephyr import tornado_callbacks

import subprocess
import ujson
import time
import traceback
import re
import datetime
import os
import platform
import logging
from collections import defaultdict
from os import path

# Store an event in the log for re-importing messages
def log_event(event):
    if "timestamp" not in event:
        event["timestamp"] = time.time()

    if not path.exists(settings.EVENT_LOG_DIR):
        os.mkdir(settings.EVENT_LOG_DIR)

    template = path.join(settings.EVENT_LOG_DIR,
        '%s.' + platform.node()
        + datetime.datetime.now().strftime('.%Y-%m-%d'))

    with lockfile(template % ('lock',)):
        with open(template % ('events',), 'a') as log:
            log.write(ujson.dumps(event) + '\n')

def notify_created_user(user_profile):
    notice = dict(event=dict(type="realm_user", op="add",
                             person=dict(email=user_profile.email,
                                         full_name=user_profile.full_name)),
                  users=[up.id for up in
                         UserProfile.objects.select_related().filter(realm=user_profile.realm,
                                                                     is_active=True)])
    tornado_callbacks.send_notification(notice)

def do_create_user(email, password, realm, full_name, short_name,
                   active=True, bot=False, bot_owner=None,
                   avatar_source=UserProfile.AVATAR_FROM_GRAVATAR):
    event = {'type': 'user_created',
               'timestamp': time.time(),
               'full_name': full_name,
               'short_name': short_name,
               'user': email,
               'domain': realm.domain,
               'bot': bot}
    if bot:
        event['bot_owner'] = bot_owner.email
    log_event(event)

    user_profile = create_user(email, password, realm, full_name, short_name,
                               active, bot, bot_owner, avatar_source)

    notify_created_user(user_profile)
    return user_profile

def user_sessions(user_profile):
    return [s for s in Session.objects.all()
            if s.get_decoded().get('_auth_user_id') == user_profile.id]

def delete_session(session):
    return session_engine.SessionStore(session.session_key).delete()

def delete_user_sessions(user_profile):
    for session in Session.objects.all():
        if session.get_decoded().get('_auth_user_id') == user_profile.id:
            delete_session(session)

def delete_realm_user_sessions(realm):
    realm_user_ids = [user_profile.id for user_profile in
                      UserProfile.objects.filter(realm=realm)]
    for session in Session.objects.all():
        if session.get_decoded().get('_auth_user_id') in realm_user_ids:
            delete_session(session)

def delete_all_user_sessions():
    for session in Session.objects.all():
        delete_session(session)

def do_deactivate(user_profile, log=True, _cascade=True):
    if not user_profile.is_active:
        return

    user_profile.is_active = False;
    user_profile.save(update_fields=["is_active"])

    delete_user_sessions(user_profile)

    if log:
        log_event({'type': 'user_deactivated',
                   'timestamp': time.time(),
                   'user': user_profile.email,
                   'domain': user_profile.realm.domain})

    notice = dict(event=dict(type="realm_user", op="remove",
                             person=dict(email=user_profile.email,
                                         full_name=user_profile.full_name)),
                  users=[up.id for up in
                         UserProfile.objects.select_related().filter(realm=user_profile.realm,
                                                                     is_active=True)])
    tornado_callbacks.send_notification(notice)

    if _cascade:
        bot_profiles = UserProfile.objects.filter(is_bot=True, is_active=True,
                                                  bot_owner=user_profile)
        for profile in bot_profiles:
            do_deactivate(profile, _cascade=False)

def do_change_user_email(user_profile, new_email):
    old_email = user_profile.email
    user_profile.email = new_email
    user_profile.save(update_fields=["email"])

    log_event({'type': 'user_email_changed',
               'old_email': old_email,
               'new_email': new_email})

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

@cache_with_key(lambda realm, email: user_profile_by_email_cache_key(email),
                timeout=3600*24*7)
@transaction.commit_on_success
def create_mit_user_if_needed(realm, email):
    try:
        return get_user_profile_by_email(email)
    except UserProfile.DoesNotExist:
        try:
            # Forge a user for this person
            return create_user(email, initial_password(email), realm,
                               compute_mit_user_fullname(email), email_to_username(email),
                               active=False)
        except IntegrityError:
            # Unless we raced with another thread doing the same
            # thing, in which case we should get the user they made
            transaction.commit()
            return get_user_profile_by_email(email)

def log_message(message):
    if not message.sending_client.name.startswith("test:"):
        log_event(message.to_log_dict())

# Helper function. Defaults here are overriden by those set in do_send_messages
def do_send_message(message, rendered_content = None, no_log = False, stream = None):
    do_send_messages([{'message': message,
                       'rendered_content': rendered_content,
                       'no_log': no_log,
                       'stream': stream}])

def do_send_messages(messages):
    # Filter out messages which didn't pass internal_prep_message properly
    messages = [message for message in messages if message is not None]

    # Filter out zephyr mirror anomalies where the message was already sent
    messages = [message for message in messages if message['message'] is not None]

    # For consistency, changes to the default values for these gets should also be applied
    # to the default args in do_send_message
    for message in messages:
        message['rendered_content'] = message.get('rendered_content', None)
        message['no_log'] = message.get('no_log', False)
        message['stream'] = message.get('stream', None)

    # Log the message to our message log for populate_db to refill
    for message in messages:
        if not message['no_log']:
            log_message(message['message'])

    for message in messages:
        if message['message'].recipient.type == Recipient.PERSONAL:
            message['recipients'] = list(set([get_user_profile_by_id(message['message'].recipient.type_id),
                                              get_user_profile_by_id(message['message'].sender_id)]))
            # For personals, you send out either 1 or 2 copies of the message, for
            # personals to yourself or to someone else, respectively.
            assert((len(message['recipients']) == 1) or (len(message['recipients']) == 2))
        elif (message['message'].recipient.type == Recipient.STREAM or
              message['message'].recipient.type == Recipient.HUDDLE):
            query = Subscription.objects.select_related("user_profile").only(
                "id", "user_profile__id", "user_profile__is_active").filter(
                recipient=message['message'].recipient, active=True)
            message['recipients'] = [s.user_profile for s in query]
        else:
            raise ValueError('Bad recipient type')

        message['message'].maybe_render_content()

    # Save the message receipts in the database
    user_message_flags = defaultdict(dict)
    with transaction.commit_on_success():
        Message.objects.bulk_create([message['message'] for message in messages])
        ums = []
        for message in messages:
            ums_to_create = [UserMessage(user_profile=user_profile, message=message['message'])
                             for user_profile in message['recipients']
                             if user_profile.is_active]

            # These properties on the Message are set via
            # Message.render_markdown by code in the bugdown inline patterns
            wildcard = message['message'].mentions_wildcard
            mentioned_ids = message['message'].mentions_user_ids

            for um in ums_to_create:
                sent_by_human = message['message'].sending_client.name.lower() in \
                                    ['website', 'iphone', 'android']
                if um.user_profile.id == message['message'].sender.id and sent_by_human:
                    um.flags |= UserMessage.flags.read
                if wildcard:
                    um.flags |= UserMessage.flags.wildcard_mentioned
                if um.user_profile_id in mentioned_ids:
                    um.flags |= UserMessage.flags.mentioned
                user_message_flags[message['message'].id][um.user_profile_id] = um.flags_list()
            ums.extend(ums_to_create)
        UserMessage.objects.bulk_create(ums)

    for message in messages:
        cache_save_message(message['message'])
        # Render Markdown etc. here and store (automatically) in
        # memcached, so that the single-threaded Tornado server
        # doesn't have to.
        message['message'].to_dict(apply_markdown=True)
        message['message'].to_dict(apply_markdown=False)
        user_flags = user_message_flags.get(message['message'].id, {})
        data = dict(
            type     = 'new_message',
            message  = message['message'].id,
            users    = [{'id': user.id, 'flags': user_flags.get(user.id, [])} for user in message['recipients']])
        if message['message'].recipient.type == Recipient.STREAM:
            # Note: This is where authorization for single-stream
            # get_updates happens! We only attach stream data to the
            # notify new_message request if it's a public stream,
            # ensuring that in the tornado server, non-public stream
            # messages are only associated to their subscribed users.
            if message['stream'] is None:
                message['stream'] = Stream.objects.select_related("realm").get(id=message['message'].recipient.type_id)
            if message['stream'].is_public():
                data['realm_id'] = message['stream'].realm.id
                data['stream_name'] = message['stream'].name
        tornado_callbacks.send_notification(data)

def create_stream_if_needed(realm, stream_name, invite_only=False):
    (stream, created) = Stream.objects.get_or_create(
        realm=realm, name__iexact=stream_name,
        defaults={'name': stream_name, 'invite_only': invite_only})
    if created:
        Recipient.objects.create(type_id=stream.id, type=Recipient.STREAM)
    return stream, created

def recipient_for_emails(emails, not_forged_zephyr_mirror, user_profile, sender):
    recipient_profile_ids = set()
    for email in emails:
        try:
            recipient_profile_ids.add(get_user_profile_by_email(email).id)
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
        return get_recipient(Recipient.HUDDLE, huddle.id)
    else:
        return get_recipient(Recipient.PERSONAL, list(recipient_profile_ids)[0])

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

def extract_recipients(raw_recipients):
    try:
        recipients = json_to_list(raw_recipients)
    except ValueError:
        recipients = [raw_recipients]

    # Strip recipients, and then remove any duplicates and any that
    # are the empty string after being stripped.
    recipients = [recipient.strip() for recipient in recipients]
    return list(set(recipient for recipient in recipients if recipient))

# check_send_message:
# Returns None on success or the error message on error.
# has same argspec as check_message
def check_send_message(*args, **kwargs):
    message = check_message(*args, **kwargs)
    if(type(message) != dict):
        assert isinstance(message, basestring)
        return message
    do_send_messages([message])
    return None

# check_message:
# Returns message ready for sending with do_send_message on success or the error message (string) on error.
def check_message(sender, client, message_type_name, message_to,
                  subject_name, message_content, realm=None, forged=False,
                  forged_timestamp=None, forwarder_user_profile=None):
    stream = None
    if len(message_to) == 0:
        return "Message must have recipients."
    if len(message_content) > MAX_MESSAGE_LENGTH:
        return "Message too long."

    if realm is None:
        realm = sender.realm

    if message_type_name == 'stream':
        if len(message_to) > 1:
            return "Cannot send to multiple streams"

        stream_name = message_to[0].strip()
        if stream_name == "":
            return "Stream can't be empty"
        if len(stream_name) > Stream.MAX_NAME_LENGTH:
            return "Stream name too long"
        if not valid_stream_name(stream_name):
            return "Invalid stream name"

        if subject_name is None:
            return "Missing topic"
        subject = subject_name.strip()
        if subject == "":
            return "Topic can't be empty"
        if len(subject) > MAX_SUBJECT_LENGTH:
            return "Topic too long"
        ## FIXME: Commented out temporarily while we figure out what we want
        # if not valid_stream_name(subject):
        #     return json_error("Invalid subject name")

        stream = get_stream(stream_name, realm)
        if stream is None:
            return "Stream does not exist"
        recipient = get_recipient(Recipient.STREAM, stream.id)

        if (stream.invite_only
            and ((not sender.is_bot and not subscribed_to_stream(sender, stream))
                 or (sender.is_bot and not (subscribed_to_stream(sender.bot_owner, stream)
                                            or subscribed_to_stream(sender, stream))))):
            return "Not authorized to send to stream '%s'" % (stream.name,)
    elif message_type_name == 'private':
        not_forged_zephyr_mirror = client and client.name == "zephyr_mirror" and not forged
        try:
            recipient = recipient_for_emails(message_to, not_forged_zephyr_mirror,
                                             forwarder_user_profile, sender)
        except ValidationError, e:
            assert isinstance(e.messages[0], basestring)
            return e.messages[0]
    else:
        return "Invalid message type"

    message = Message()
    message.sender = sender
    message.content = message_content
    message.recipient = recipient
    if message_type_name == 'stream':
        message.subject = subject
    if forged:
        # Forged messages come with a timestamp
        message.pub_date = timestamp_to_datetime(forged_timestamp)
    else:
        message.pub_date = timezone.now()
    message.sending_client = client

    if not message.maybe_render_content():
        return "We were unable to render your message"

    if client.name == "zephyr_mirror" and already_sent_mirrored_message(message):
        return {'message': None}

    return {'message': message, 'stream': stream}

def internal_prep_message(sender_email, recipient_type_name, recipients,
                          subject, content, realm=None):
    """
    Create a message object and checks it, but doesn't send it or save it to the database.
    The internal function that calls this can therefore batch send a bunch of created
    messages together as one database query.
    Call do_send_messages with a list of the return values of this method.
    """
    if len(content) > MAX_MESSAGE_LENGTH:
        content = content[0:3900] + "\n\n[message was too long and has been truncated]"

    sender = get_user_profile_by_email(sender_email)
    if realm is None:
        realm = sender.realm
    parsed_recipients = extract_recipients(recipients)
    if recipient_type_name == "stream":
        stream, _ = create_stream_if_needed(realm, parsed_recipients[0])

    ret = check_message(sender, get_client("Internal"), recipient_type_name,
                        parsed_recipients, subject, content, realm)
    if isinstance(ret, basestring):
        logging.error("Error queueing internal message by %s: %s" % (sender_email, ret))
    elif isinstance(ret, dict):
        return ret
    else:
        logging.error("Error queueing internal message; check message return unexpected type: %s" \
                      % (repr(ret),))

def internal_send_message(sender_email, recipient_type_name, recipients,
                          subject, content, realm=None):
    msg = internal_prep_message(sender_email, recipient_type_name, recipients,
                                subject, content, realm)

    # internal_prep_message encountered an error
    if msg is None:
        return

    do_send_messages([msg])

def pick_color(user_profile):
    subs = Subscription.objects.filter(user_profile=user_profile,
                                       active=True,
                                       recipient__type=Recipient.STREAM)
    return pick_color_helper(user_profile, subs)

def pick_color_helper(user_profile, subs):
    # These colors are shared with the palette in subs.js.
    stream_assignment_colors = [
        "#76ce90", "#fae589", "#a6c7e5", "#e79ab5",
        "#bfd56f", "#f4ae55", "#b0a5fd", "#addfe5",
        "#f5ce6e", "#c2726a", "#94c849", "#bd86e5",
        "#ee7e4a", "#a6dcbf", "#95a5fd", "#53a063",
        "#9987e1", "#e4523d", "#c2c2c2", "#4f8de4",
        "#c6a8ad", "#e7cc4d", "#c8bebf", "#a47462"]
    used_colors = [sub.color for sub in subs if sub.active]
    available_colors = filter(lambda x: x not in used_colors,
                              stream_assignment_colors)

    if available_colors:
        return available_colors[0]
    else:
        return stream_assignment_colors[len(used_colors) % len(stream_assignment_colors)]

def get_subscription(stream_name, user_profile):
    stream = get_stream(stream_name, user_profile.realm)
    recipient = get_recipient(Recipient.STREAM, stream.id)
    return Subscription.objects.get(user_profile=user_profile,
                                    recipient=recipient, active=True)

def set_stream_color(user_profile, stream_name, color=None):
    subscription = get_subscription(stream_name, user_profile)
    if not color:
        color = pick_color(user_profile)
    subscription.color = color
    subscription.save(update_fields=["color"])
    return color

def notify_subscriptions_added(user_profile, sub_pairs, no_log=False):
    if not no_log:
        log_event({'type': 'subscription_added',
                   'user': user_profile.email,
                   'names': [stream.name for sub, stream in sub_pairs],
                   'domain': stream.realm.domain})

    payload = [dict(name=stream.name,
                    in_home_view=subscription.in_home_view,
                    invite_only=stream.invite_only,
                    color=subscription.color)
            for (subscription, stream) in sub_pairs]
    notice = dict(event=dict(type="subscriptions", op="add",
                             subscriptions=payload),
                  users=[user_profile.id])
    tornado_callbacks.send_notification(notice)

def bulk_add_subscriptions(streams, users):
    recipients_map = bulk_get_recipients(Recipient.STREAM, [stream.id for stream in streams])
    recipients = [recipient.id for recipient in recipients_map.values()]

    stream_map = {}
    for stream in streams:
        stream_map[recipients_map[stream.id].id] = stream

    subs_by_user = defaultdict(list)
    all_subs_query = Subscription.objects.select_related("user_profile")
    for sub in all_subs_query.filter(user_profile__in=users,
                                     recipient__type=Recipient.STREAM):
        subs_by_user[sub.user_profile_id].append(sub)

    already_subscribed = []
    subs_to_activate = []
    new_subs = []
    for user_profile in users:
        needs_new_sub = set(recipients)
        for sub in subs_by_user[user_profile.id]:
            if sub.recipient_id in needs_new_sub:
                needs_new_sub.remove(sub.recipient_id)
                if sub.active:
                    already_subscribed.append((user_profile, stream_map[sub.recipient_id]))
                else:
                    subs_to_activate.append((sub, stream_map[sub.recipient_id]))
                    # Mark the sub as active, without saving, so that
                    # pick_color will consider this to be an active
                    # subscription when picking colors
                    sub.active = True
        for recipient_id in needs_new_sub:
            new_subs.append((user_profile, recipient_id, stream_map[recipient_id]))

    subs_to_add = []
    for (user_profile, recipient_id, stream) in new_subs:
        color = pick_color_helper(user_profile, subs_by_user[user_profile.id])
        sub_to_add = Subscription(user_profile=user_profile, active=True,
                                  color=color, recipient_id=recipient_id)
        subs_by_user[user_profile.id].append(sub_to_add)
        subs_to_add.append((sub_to_add, stream))
    Subscription.objects.bulk_create([sub for (sub, stream) in subs_to_add])
    Subscription.objects.filter(id__in=[sub.id for (sub, stream_name) in subs_to_activate]).update(active=True)

    sub_tuples_by_user = defaultdict(list)
    for (sub, stream) in subs_to_add + subs_to_activate:
        sub_tuples_by_user[sub.user_profile.id].append((sub, stream))

    for user_profile in users:
        if len(sub_tuples_by_user[user_profile.id]) == 0:
            continue
        notify_subscriptions_added(user_profile, sub_tuples_by_user[user_profile.id])

    return ([(user_profile, stream_name) for (user_profile, recipient_id, stream_name) in new_subs] +
            [(sub.user_profile, stream_name) for (sub, stream_name) in subs_to_activate],
            already_subscribed)

# When changing this, also change bulk_add_subscriptions
def do_add_subscription(user_profile, stream, no_log=False):
    recipient = get_recipient(Recipient.STREAM, stream.id)
    color = pick_color(user_profile)
    (subscription, created) = Subscription.objects.get_or_create(
        user_profile=user_profile, recipient=recipient,
        defaults={'active': True, 'color': color})
    did_subscribe = created
    if not subscription.active:
        did_subscribe = True
        subscription.active = True
        subscription.save(update_fields=["active"])
    if did_subscribe:
        notify_subscriptions_added(user_profile, [(subscription, stream)], no_log)
    return did_subscribe

def notify_subscriptions_removed(user_profile, streams, no_log=False):
    if not no_log:
        log_event({'type': 'subscription_removed',
                   'user': user_profile.email,
                   'names': [stream.name for stream in streams],
                   'domain': stream.realm.domain})

    payload = [dict(name=stream.name) for stream in streams]
    notice = dict(event=dict(type="subscriptions", op="remove",
                             subscriptions=payload),
                  users=[user_profile.id])
    tornado_callbacks.send_notification(notice)

def bulk_remove_subscriptions(users, streams):
    recipients_map = bulk_get_recipients(Recipient.STREAM,
                                         [stream.id for stream in streams])
    stream_map = {}
    for stream in streams:
        stream_map[recipients_map[stream.id].id] = stream

    subs_by_user = dict((user_profile.id, []) for user_profile in users)
    for sub in Subscription.objects.select_related("user_profile").filter(user_profile__in=users,
                                                                          recipient__in=recipients_map.values(),
                                                                          active=True):
        subs_by_user[sub.user_profile_id].append(sub)

    subs_to_deactivate = []
    not_subscribed = []
    for user_profile in users:
        recipients_to_unsub = set([recipient.id for recipient in recipients_map.values()])
        for sub in subs_by_user[user_profile.id]:
            recipients_to_unsub.remove(sub.recipient_id)
            subs_to_deactivate.append((sub, stream_map[sub.recipient_id]))
        for recipient_id in recipients_to_unsub:
            not_subscribed.append((user_profile, stream_map[recipient_id]))

    Subscription.objects.filter(id__in=[sub.id for (sub, stream_name) in
                                        subs_to_deactivate]).update(active=False)

    streams_by_user = defaultdict(list)
    for (sub, stream) in subs_to_deactivate:
        streams_by_user[sub.user_profile_id].append(stream)

    for user_profile in users:
        if len(streams_by_user[user_profile.id]) == 0:
            continue
        notify_subscriptions_removed(user_profile, streams_by_user[user_profile.id])

    return ([(sub.user_profile, stream) for (sub, stream) in subs_to_deactivate],
            not_subscribed)

def do_remove_subscription(user_profile, stream, no_log=False):
    recipient = get_recipient(Recipient.STREAM, stream.id)
    maybe_sub = Subscription.objects.filter(user_profile=user_profile,
                                    recipient=recipient)
    if len(maybe_sub) == 0:
        return False
    subscription = maybe_sub[0]
    did_remove = subscription.active
    subscription.active = False
    subscription.save(update_fields=["active"])
    if did_remove:
        notify_subscriptions_removed(user_profile, [stream], no_log)

    return did_remove

def log_subscription_property_change(user_email, stream_name, property, value):
    event = {'type': 'subscription_property',
             'property': property,
             'user': user_email,
             'stream_name': stream_name,
             'value': value}
    log_event(event)

def do_change_subscription_property(user_profile, sub, stream_name,
                                    property_name, value):
    setattr(sub, property_name, value)
    sub.save(update_fields=[property_name])
    log_subscription_property_change(user_profile.email, stream_name,
                                     property_name, value)

    notice = dict(event=dict(type="subscriptions",
                             op="update",
                             email=user_profile.email,
                             property=property_name,
                             value=value,
                             name=stream_name,),
                  users=[user_profile.id])
    tornado_callbacks.send_notification(notice)

def do_activate_user(user_profile, log=True, join_date=timezone.now()):
    user_profile.is_active = True
    user_profile.set_password(initial_password(user_profile.email))
    user_profile.date_joined = join_date
    user_profile.save(update_fields=["is_active", "date_joined", "password"])

    if log:
        domain = user_profile.realm.domain
        log_event({'type': 'user_activated',
                   'user': user_profile.email,
                   'domain': domain})

    notify_created_user(user_profile)

def do_change_password(user_profile, password, log=True, commit=True,
                       hashed_password=False):
    if hashed_password:
        # This is a hashed password, not the password itself.
        user_profile.set_password(password)
    else:
        user_profile.set_password(password)
    if commit:
        user_profile.save(update_fields=["password"])
    if log:
        log_event({'type': 'user_change_password',
                   'user': user_profile.email,
                   'pwhash': user_profile.password})

def do_change_full_name(user_profile, full_name, log=True):
    user_profile.full_name = full_name
    user_profile.save(update_fields=["full_name"])
    if log:
        log_event({'type': 'user_change_full_name',
                   'user': user_profile.email,
                   'full_name': full_name})

    notice = dict(event=dict(type="realm_user", op="update",
                             person=dict(email=user_profile.email,
                                         full_name=user_profile.full_name)),
                  users=[up.id for up in
                         UserProfile.objects.select_related().filter(realm=user_profile.realm,
                                                                     is_active=True)])
    tornado_callbacks.send_notification(notice)


def do_create_realm(domain, restricted_to_domain=True):
    realm = get_realm(domain)
    created = not realm
    if created:
        realm = Realm(domain=domain, restricted_to_domain=restricted_to_domain)
        realm.save()
        # Log the event
        log_event({"type": "realm_created",
                   "domain": domain,
                   "restricted_to_domain": restricted_to_domain})

        signup_message = "Signups enabled"
        if not restricted_to_domain:
            signup_message += " (open realm)"
        internal_send_message("new-user-bot@zulip.com", "stream",
                              "signups", domain, signup_message)
    return (realm, created)

def do_change_enable_desktop_notifications(user_profile, enable_desktop_notifications, log=True):
    user_profile.enable_desktop_notifications = enable_desktop_notifications
    user_profile.save(update_fields=["enable_desktop_notifications"])
    if log:
        log_event({'type': 'enable_desktop_notifications_changed',
                   'user': user_profile.email,
                   'enable_desktop_notifications': enable_desktop_notifications})

def do_change_enable_sounds(user_profile, enable_sounds, log=True):
    user_profile.enable_sounds = enable_sounds
    user_profile.save(update_fields=["enable_sounds"])
    if log:
        log_event({'type': 'enable_sounds_changed',
                   'user': user_profile.email,
                   'enable_sounds': enable_sounds})

def do_change_enable_offline_email_notifications(user_profile, offline_email_notifications, log=True):
    user_profile.enable_offline_email_notifications = offline_email_notifications
    user_profile.save(update_fields=["enable_offline_email_notifications"])
    if log:
        log_event({'type': 'enable_offline_email_notifications_changed',
                   'user': user_profile.email,
                   'enable_offline_email_notifications': offline_email_notifications})

def do_change_enter_sends(user_profile, enter_sends):
    user_profile.enter_sends = enter_sends
    user_profile.save(update_fields=["enter_sends"])

def set_default_streams(realm, stream_names):
    DefaultStream.objects.filter(realm=realm).delete()
    for stream_name in stream_names:
        stream, _ = create_stream_if_needed(realm, stream_name)
        DefaultStream.objects.create(stream=stream, realm=realm)

def get_default_subs(user_profile):
    return [default.stream for default in
            DefaultStream.objects.select_related("stream").filter(realm=user_profile.realm)]

@statsd_increment('user_activity')
@transaction.commit_on_success
def do_update_user_activity(user_profile, client, query, log_time):
    try:
        (activity, created) = UserActivity.objects.get_or_create(
            user_profile = user_profile,
            client = client,
            query = query,
            defaults={'last_visit': log_time, 'count': 0})
    except IntegrityError:
        transaction.commit()
        activity = UserActivity.objects.get(user_profile = user_profile,
                                            client = client,
                                            query = query)
    activity.count += 1
    activity.last_visit = log_time
    activity.save(update_fields=["last_visit", "count"])

def process_user_activity_event(event):
    user_profile = get_user_profile_by_id(event["user_profile_id"])
    client = get_client(event["client"])
    log_time = timestamp_to_datetime(event["time"])
    query = event["query"]
    return do_update_user_activity(user_profile, client, query, log_time)

def send_presence_changed(user_profile, presence):
    presence_dict = presence.to_dict()
    notice = dict(event=dict(type="presence", email=user_profile.email,
                             server_timestamp=time.time(),
                             presence={presence_dict['client']: presence.to_dict()}),
                  users=[up.id for up in
                         UserProfile.objects.select_related()
                                            .filter(realm=user_profile.realm,
                                                    is_active=True)])
    tornado_callbacks.send_notification(notice)

@statsd_increment('user_presence')
@transaction.commit_on_success
def do_update_user_presence(user_profile, client, log_time, status):
    try:
        (presence, created) = UserPresence.objects.get_or_create(
            user_profile = user_profile,
            client = client,
            defaults = {'timestamp': log_time,
                        'status': status})
    except IntegrityError:
        transaction.commit()
        presence = UserPresence.objects.get(user_profile = user_profile,
                                            client = client)
        created = False

    stale_status = (log_time - presence.timestamp) > datetime.timedelta(minutes=10)
    was_idle = presence.status == UserPresence.IDLE
    became_online = (status == UserPresence.ACTIVE) and (stale_status or was_idle)

    if not created:
        # The following block attempts to only update the "status"
        # field in the event that it actually changed.  This is
        # important to avoid flushing the UserPresence cache when the
        # data it would return to a client hasn't actually changed
        # (see the UserPresence post_save hook for details).
        presence.timestamp = log_time
        update_fields = ["timestamp"]
        if presence.status != status:
            presence.status = status
            update_fields.append("status")
        presence.save(update_fields=update_fields)

    if not user_profile.realm.domain == "mit.edu" and (created or became_online):
        # Push event to all users in the realm so they see the new user
        # appear in the presence list immediately, or the newly online
        # user without delay
        send_presence_changed(user_profile, presence)

def update_user_presence(user_profile, client, log_time, status):
    event={'type': 'user_presence',
           'user_profile_id': user_profile.id,
           'status': status,
           'time': datetime_to_timestamp(log_time),
           'client': client.name}

    queue_json_publish("user_activity", event, process_user_presence_event)

def update_message_flags(user_profile, operation, flag, messages, all):
    flagattr = getattr(UserMessage.flags, flag)

    if all:
        log_statsd_event('bankruptcy')
        msgs = UserMessage.objects.filter(user_profile=user_profile)
    else:
        msgs = UserMessage.objects.filter(user_profile=user_profile,
                                          message__id__in=messages)

    if operation == 'add':
        count = msgs.update(flags=F('flags').bitor(flagattr))
    elif operation == 'remove':
        count = msgs.update(flags=F('flags').bitand(~flagattr))

    statsd.incr("flags.%s.%s" % (flag, operation), count)

def process_user_presence_event(event):
    user_profile = get_user_profile_by_id(event["user_profile_id"])
    client = get_client(event["client"])
    log_time = timestamp_to_datetime(event["time"])
    status = event["status"]
    return do_update_user_presence(user_profile, client, log_time, status)

def subscribed_to_stream(user_profile, stream):
    try:
        if Subscription.objects.get(user_profile=user_profile,
                                    active=True,
                                    recipient__type=Recipient.STREAM,
                                    recipient__type_id=stream.id):
            return True
        return False
    except Subscription.DoesNotExist:
        return False

def do_update_onboarding_steps(user_profile, steps):
    user_profile.onboarding_steps = ujson.dumps(steps)
    user_profile.save(update_fields=["onboarding_steps"])

    log_event({'type': 'update_onboarding',
               'user': user_profile.email,
               'steps': steps})

    notice = dict(event=dict(type="onboarding_steps", steps=steps),
                  users=[user_profile.id])
    tornado_callbacks.send_notification(notice)

def do_update_message(user_profile, message_id, subject, content):
    try:
        message = Message.objects.select_related().get(id=message_id)
    except Message.DoesNotExist:
        raise JsonableError("Unknown message id")

    event = {'type': 'update_message',
             'sender': user_profile.email,
             'message_id': message_id}
    edit_history_event = {}

    if message.sender != user_profile:
        raise JsonableError("Message was not sent by you")

    # Set first_rendered_content to be the oldest version of the
    # rendered content recorded; which is the current version if the
    # content hasn't been edited before.  Note that because one could
    # have edited just the subject, not every edit history event
    # contains a prev_rendered_content element.
    first_rendered_content = message.rendered_content
    if message.edit_history is not None:
        edit_history = ujson.loads(message.edit_history)
        for old_edit_history_event in edit_history:
            if 'prev_rendered_content' in old_edit_history_event:
                first_rendered_content = old_edit_history_event['prev_rendered_content']

    if content is not None:
        if content == "":
            raise JsonableError("Message can't be empty")
        if len(content) > MAX_MESSAGE_LENGTH:
            raise JsonableError("Message too long")
        rendered_content = message.render_markdown(content)
        if not rendered_content:
            raise JsonableError("We were unable to render your updated message")

        # We are turning off diff highlighting everywhere until ticket #1532 is addressed.
        if False:
            # Don't highlight message edit diffs on prod
            rendered_content = highlight_html_differences(first_rendered_content, rendered_content)

        event['orig_content'] = message.content
        event['orig_rendered_content'] = message.rendered_content
        edit_history_event["prev_content"] = message.content
        edit_history_event["prev_rendered_content"] = message.rendered_content
        edit_history_event["prev_rendered_content_version"] = message.rendered_content_version
        message.content = content
        message.set_rendered_content(rendered_content)
        event["content"] = content
        event["rendered_content"] = rendered_content

    if subject is not None:
        subject = subject.strip()
        if subject == "":
            raise JsonableError("Topic can't be empty")

        if len(subject) > MAX_SUBJECT_LENGTH:
            raise JsonableError("Topic too long")
        event["orig_subject"] = message.subject
        message.subject = subject
        event["subject"] = subject
        event['subject_links'] = bugdown.subject_links(message.sender.realm.domain.lower(), subject)
        edit_history_event["prev_subject"] = event['orig_subject']

    message.last_edit_time = timezone.now()
    event['edit_timestamp'] = datetime_to_timestamp(message.last_edit_time)
    edit_history_event['timestamp'] = event['edit_timestamp']
    if message.edit_history is not None:
        edit_history.insert(0, edit_history_event)
    else:
        edit_history = [edit_history_event]
    message.edit_history = ujson.dumps(edit_history)

    log_event(event)
    message.save(update_fields=["subject", "content", "rendered_content",
                                "rendered_content_version", "last_edit_time",
                                "edit_history"])

    # Update the message as stored in both the (deprecated) message
    # cache (for shunting the message over to Tornado in the old
    # get_messages API) and also the to_dict caches.
    cache_save_message(message)
    items_for_memcached = {}
    items_for_memcached[to_dict_cache_key(message, True)] = \
        (stringify_message_dict(message.to_dict_uncached(apply_markdown=True)),)
    items_for_memcached[to_dict_cache_key(message, False)] = \
        (stringify_message_dict(message.to_dict_uncached(apply_markdown=False)),)
    cache_set_many(items_for_memcached)

    recipients = [um.user_profile_id for um in UserMessage.objects.filter(message=message_id)]
    notice = dict(event=event, users=recipients)
    tornado_callbacks.send_notification(notice)

def gather_subscriptions(user_profile):
    # For now, don't display subscriptions for private messages.
    subs = Subscription.objects.select_related().filter(
        user_profile    = user_profile,
        recipient__type = Recipient.STREAM)

    stream_ids = [sub.recipient.type_id for sub in subs]

    stream_hash = {}
    for stream in Stream.objects.filter(id__in=stream_ids):
        stream_hash[stream.id] = (stream.name, stream.invite_only)

    subscribed = []
    unsubscribed = []

    for sub in subs:
        (stream_name, invite_only) = stream_hash[sub.recipient.type_id]
        stream = {'name': stream_name,
                  'in_home_view': sub.in_home_view,
                  'invite_only': invite_only,
                  'color': sub.color,
                  'notifications': sub.notifications}
        if sub.active:
            subscribed.append(stream)
        else:
            unsubscribed.append(stream)

    return (sorted(subscribed), sorted(unsubscribed))

@cache_with_key(status_dict_cache_key, timeout=60)
def get_status_dict(requesting_user_profile):
    user_statuses = defaultdict(dict)

    # Return no status info for MIT
    if requesting_user_profile.realm.domain == 'mit.edu':
        return user_statuses

    for presence in UserPresence.objects.filter(user_profile__realm=requesting_user_profile.realm,
                                                user_profile__is_active=True) \
                                        .select_related('user_profile', 'client'):
        user_statuses[presence.user_profile.email][presence.client.name] = presence.to_dict()

    return user_statuses


def do_events_register(user_profile, user_client, apply_markdown=True,
                       event_types=None):
    queue_id = request_event_queue(user_profile, user_client, apply_markdown,
                                   event_types)
    if queue_id is None:
        raise JsonableError("Could not allocate event queue")

    ret = {'queue_id': queue_id}
    if event_types is not None:
        event_types = set(event_types)

    # Fetch initial data.  When event_types is not specified, clients
    # want all event types.
    if event_types is None or "message" in event_types:
        # The client should use get_old_messages() to fetch messages
        # starting with the max_message_id.  They will get messages
        # newer than that ID via get_events()
        messages = Message.objects.filter(usermessage__user_profile=user_profile).order_by('-id')[:1]
        if messages:
            ret['max_message_id'] = messages[0].id
        else:
            ret['max_message_id'] = -1
    if event_types is None or "pointer" in event_types:
        ret['pointer'] = user_profile.pointer
    if event_types is None or "realm_user" in event_types:
        ret['realm_users'] = [{'email'     : profile.email,
                               'full_name' : profile.full_name}
                              for profile in
                              UserProfile.objects.select_related().filter(realm=user_profile.realm,
                                                                          is_active=True)]
    if event_types is None or "onboarding_steps" in event_types:
        ret['onboarding_steps'] = [{'email' : profile.email,
                                    'steps' : profile.onboarding_steps}]
    if event_types is None or "subscription" in event_types:
        subs = gather_subscriptions(user_profile)
        ret['subscriptions'] = subs[0]
        ret['unsubscribed'] = subs[1]
    if event_types is None or "presence" in event_types:
        ret['presences'] = get_status_dict(user_profile)

    # Apply events that came in while we were fetching initial data
    events = get_user_events(user_profile, queue_id, -1)
    for event in events:
        if event['type'] == "message":
            ret['max_message_id'] = max(ret['max_message_id'], event['message']['id'])
        elif event['type'] == "pointer":
            ret['pointer'] = max(ret['pointer'], event['pointer'])
        elif event['type'] == "onboarding_steps":
            ret['onboarding_steps'] = event['steps']
        elif event['type'] == "realm_user":
            # We handle update by just removing the old value and
            # adding the new one.
            if event['op'] == "remove" or event['op'] == "update":
                person = event['person']
                ret['realm_users'] = filter(lambda p: p['email'] != person['email'],
                                            ret['realm_users'])
            if event['op'] == "add" or event['op'] == "update":
                ret['realm_users'].append(event['person'])
        elif event['type'] == "subscriptions":
            subscriptions_to_filter = set(sub.name.lower() for sub in event["subscriptions"])
            # We add the new subscriptions to the list of streams the
            # user is subscribed to, and also remove/add them from the
            # list of streams the user is not subscribed to (which we
            # are still sending on data about so that e.g. colors and
            # the in_home_view bit are properly available for those streams)
            #
            # And we do the opposite filtering process for unsubscribe events.
            if event['op'] == "add":
                ret['subscriptions'] += event['subscriptions']
                ret['unsubscribed'] = filter(lambda s: s['name'].lower() not in subscriptions_to_filter,
                                             ret['unsubscribed'])
            elif event['op'] == "remove":
                ret['unsubscribed'] += event['subscriptions']
                ret['subscriptions'] = filter(lambda s: s['name'].lower() not in subscriptions_to_filter,
                                              ret['subscriptions'])
            elif event['op'] == 'update':
                for sub in ret['subscriptions']:
                    if sub['name'].lower() == event['name'].lower():
                        sub[event['property']] = event['value']
        elif event['type'] == "presence":
                ret['presences'][event['email']] = event['presence']
        elif event['type'] == "update_message":
            # The client will get the updated message directly
            pass
        else:
            raise ValueError("Unexpected event type %s" % (event['type'],))

    if events:
        ret['last_event_id'] = events[-1]['id']
    else:
        ret['last_event_id'] = -1

    return ret

def do_send_confirmation_email(invitee, referrer):
    """
    Send the confirmation/welcome e-mail to an invited user.

    `invitee` is a PreregistrationUser.
    `referrer` is a UserProfile.
    """
    Confirmation.objects.send_confirmation(
        invitee, invitee.email, additional_context={'referrer': referrer},
        subject_template_path='confirmation/invite_email_subject.txt',
        body_template_path='confirmation/invite_email_body.txt')

def build_message_list(user_profile, messages):
    """
    Builds the message list object for the missed message email template.
    The messages are collapsed into per-recipient and per-sender blocks, like
    our web interface
    """
    messages_to_render = []

    def sender_string(message):
        sender = ''
        if message.recipient.type in (Recipient.STREAM, Recipient.HUDDLE):
            sender = message.sender.full_name
        return sender

    def build_message_payload(message):
        return {'plain': message.content,
                'html': message.rendered_content}

    def build_sender_payload(message):
        sender = sender_string(message)
        return {'sender': sender,
                'content': [build_message_payload(message)]}

    def message_header(user_profile, message):
        disp_recipient = get_display_recipient(message.recipient)
        if message.recipient.type == Recipient.PERSONAL:
            header = "You and %s" % (message.sender.full_name)
        elif message.recipient.type == Recipient.HUDDLE:
            other_recipients = [r['full_name'] for r in disp_recipient
                                    if r['email'] != user_profile.email]
            header = "You and %s" % (", ".join(other_recipients),)
        else:
            header = "%s > %s" % (disp_recipient, message.subject)
        return header

    # # Collapse message list to
    # [
    #    {
    #       "header":"xxx",
    #       "senders":[
    #          {
    #             "sender":"sender_name",
    #             "content":[
    #                {
    #                   "plain":"content",
    #                   "html":"htmlcontent"
    #                }
    #                {
    #                   "plain":"content",
    #                   "html":"htmlcontent"
    #                }
    #             ]
    #          }
    #       ]
    #    },
    # ]

    for message in messages:
        header = message_header(user_profile, message)

        # If we want to collapse into the previous recipient block
        if len(messages_to_render) > 0 and messages_to_render[-1]['header'] == header:
            sender = sender_string(message)
            sender_block = messages_to_render[-1]['senders']

            # Same message sender, collapse again
            if sender_block[-1]['sender'] == sender:
                sender_block[-1]['content'].append(build_message_payload(message))
            else:
                # Start a new sender block
                sender_block.append(build_sender_payload(message))
        else:
            # New recipient and sender block
            recipient_block = {'header': header,
                               'senders': [build_sender_payload(message)]}

            messages_to_render.append(recipient_block)

    return messages_to_render

@statsd_increment("missed_message_reminders")
def do_send_missedmessage_email(user_profile, missed_messages):
    """
    Send a reminder email to a user if she's missed some PMs by being offline

    `user_profile` is the user to send the reminder to
    `missed_messages` is a list of Message objects to remind about
    """
    template_payload = {'name': user_profile.full_name,
                        'messages': build_message_list(user_profile, missed_messages),
                        'message_count': len(missed_messages),
                        'url': 'https://zulip.com',
                        'reply_warning': False}

    senders = set(m.sender.full_name for m in missed_messages)
    sender_str = ", ".join(senders)

    headers = {}
    if all(msg.recipient.type in (Recipient.HUDDLE, Recipient.PERSONAL)
            for msg in missed_messages):
        # If we have one huddle, set a reply-to to all of the members
        # of the huddle except the user herself
        disp_recipients = [", ".join(recipient['email']
                                for recipient in get_display_recipient(msg.recipient)
                                    if recipient['email'] != user_profile.email)
                                 for msg in missed_messages]
        if all(msg.recipient.type == Recipient.HUDDLE for msg in missed_messages) and \
            len(set(disp_recipients)) == 1:
            headers['Reply-To'] = disp_recipients[0]
        elif len(senders) == 1:
            headers['Reply-To'] = missed_messages[0].sender.email
        else:
            template_payload['reply_warning'] = True
    else:
        # There are some @-mentions mixed in with personals
        template_payload['mention'] = True
        template_payload['reply_warning'] = True
        headers['Reply-To'] = "Nobody <noreply@zulip.com>"

    subject = "Missed Zulip%s from %s" % ('s' if len(senders) > 1 else '', sender_str)
    from_email = "%s (via Zulip) <noreply@zulip.com>" % (sender_str)

    text_content = loader.render_to_string('zephyr/missed_message_email.txt', template_payload)
    html_content = loader.render_to_string('zephyr/missed_message_email_html.txt', template_payload)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [user_profile.email],
                                 headers = headers)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    user_profile.last_reminder = datetime.datetime.now()
    user_profile.save(update_fields=['last_reminder'])

def handle_missedmessage_emails(user_profile_id, missed_email_events):
    message_ids = [event.get('message_id') for event in missed_email_events]
    timestamp = timestamp_to_datetime(event.get('timestamp'))

    user_profile = get_user_profile_by_id(user_profile_id)
    messages = [um.message for um in UserMessage.objects.filter(user_profile=user_profile,
                                                                message__id__in=message_ids,
                                                                flags=~UserMessage.flags.read)]

    last_reminder = user_profile.last_reminder
    if last_reminder is not None and is_naive(last_reminder):
        logging.warning("Loaded a user_profile.last_reminder for user %s that's not tz-aware: %s"
                          % (user_profile.email, last_reminder))
        last_reminder = last_reminder.replace(tzinfo=utc)

    waitperiod = datetime.timedelta(hours=UserProfile.EMAIL_REMINDER_WAITPERIOD)
    if len(messages) == 0 or (last_reminder and \
                              timestamp - last_reminder < waitperiod):
        # Don't spam the user, if we've sent an email in the last day
        return

    do_send_missedmessage_email(user_profile, messages)


def user_email_is_unique(value):
    try:
        get_user_profile_by_email(value)
        raise ValidationError(u'%s is already registered' % value)
    except UserProfile.DoesNotExist:
        pass

def do_invite_users(user_profile, invitee_emails, streams):
    new_prereg_users = []
    errors = []
    skipped = []

    ret_error = None
    ret_error_data = {}

    for email in invitee_emails:
        if email == '':
            continue

        try:
            validators.validate_email(email)
        except ValidationError:
            errors.append((email, "Invalid address."))
            continue

        if user_profile.realm.restricted_to_domain and \
                email_to_domain(email).lower() != user_profile.realm.domain.lower():
            errors.append((email, "Outside your domain."))
            continue

        # Redundant check in case earlier validation preventing MIT users from
        # inviting people fails.
        if settings.ALLOW_REGISTER == False:
            if "@mit.edu" in email:
                errors.append((email, "Invitations are not enabled for MIT at this time."))
                continue

        try:
            user_email_is_unique(email)
        except ValidationError:
            skipped.append((email, "Already has an account."))
            continue

        # The logged in user is the referrer.
        prereg_user = PreregistrationUser(email=email, referred_by=user_profile)

        # We save twice because you cannot associate a ManyToMany field
        # on an unsaved object.
        prereg_user.save()
        prereg_user.streams = streams
        prereg_user.save()

        new_prereg_users.append(prereg_user)

    if errors:
        ret_error = "Some emails did not validate, so we didn't send any invitations."
        ret_error_data = {'errors': errors}

    if skipped and len(skipped) == len(invitee_emails):
        # All e-mails were skipped, so we didn't actually invite anyone.
        ret_error = "We weren't able to invite anyone."
        ret_error_data = {'errors': skipped}
        return ret_error, ret_error_data

    # If we encounter an exception at any point before now, there are no unwanted side-effects,
    # since it is totally fine to have duplicate PreregistrationUsers
    for user in new_prereg_users:
        event = {"email": user.email, "referrer_email": user_profile.email}
        queue_json_publish("invites", event,
                           lambda event: do_send_confirmation_email(user, user_profile))

    if skipped:
        ret_error = "Some of those addresses are already using Zulip, \
so we didn't send them an invitation. We did send invitations to everyone else!"
        ret_error_data = {'errors': skipped}

    return ret_error, ret_error_data


from __future__ import absolute_import

from django.http import HttpResponse, HttpResponseNotAllowed
import ujson

class HttpResponseUnauthorized(HttpResponse):
    status_code = 401

    def __init__(self, realm):
        HttpResponse.__init__(self)
        self["WWW-Authenticate"] = 'Basic realm="%s"' % (realm,)

def json_unauthorized(message):
    resp = HttpResponseUnauthorized("humbug")
    resp.content = ujson.dumps({"result": "error",
                                "msg": message})
    return resp

def json_method_not_allowed(methods):
    resp = HttpResponseNotAllowed(methods)
    resp.content = ujson.dumps({"result": "error",
        "msg": "Method Not Allowed",
        "allowed_methods": methods})
    return resp

def json_response(res_type="success", msg="", data={}, status=200):
    content = {"result": res_type, "msg": msg}
    content.update(data)
    return HttpResponse(content=ujson.dumps(content),
                        mimetype='application/json', status=status)

def json_success(data={}):
    return json_response(data=data)

def json_error(msg, data={}, status=400):
    return json_response(res_type="error", msg=msg, data=data, status=status)

from __future__ import absolute_import

import logging
import time
from tornado import ioloop

orig_poll_impl = ioloop._poll

# A hack to keep track of how much time we spend working, versus sleeping in
# the event loop.
#
# Creating a new event loop instance with a custom impl object fails (events
# don't get processed), so instead we modify the ioloop module variable holding
# the default poll implementation.  We need to do this before any Tornado code
# runs that might instantiate the default event loop.

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

def instrument_tornado_ioloop():
    ioloop._poll = InstrumentedPoll

from __future__ import absolute_import
from django.conf import settings

import hashlib
from zephyr.lib.utils import make_safe_digest

def gravatar_hash(email):
    """Compute the Gravatar hash for an email address."""
    # Non-ASCII characters aren't permitted by the currently active e-mail
    # RFCs. However, the IETF has published https://tools.ietf.org/html/rfc4952,
    # outlining internationalization of email addresses, and regardless if we
    # typo an address or someone manages to give us a non-ASCII address, let's
    # not error out on it.
    return make_safe_digest(email.lower(), hashlib.md5)

def user_avatar_hash(email):
    # Salting the user_key may be overkill, but it prevents us from
    # basically mimicking Gravatar's hashing scheme, which could lead
    # to some abuse scenarios like folks using us as a free Gravatar
    # replacement.
    user_key = email.lower() + settings.AVATAR_SALT
    return make_safe_digest(user_key, hashlib.sha1)

def avatar_url(user_profile):
    if user_profile.avatar_source == 'U':
        bucket = settings.S3_AVATAR_BUCKET
        hash_key = user_avatar_hash(user_profile.email)
        # ?x=x allows templates to append additional parameters with &s
        return "https://%s.s3.amazonaws.com/%s?x=x" % (bucket, hash_key)
    else:
        hash_key = gravatar_hash(user_profile.email)
        return "https://secure.gravatar.com/avatar/%s?d=identicon" % (hash_key,)

import logging
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

class ReturnTrue(logging.Filter):
    def filter(self, record):
        return True

class RequireReallyDeployed(logging.Filter):
    def filter(self, record):
        from django.conf import settings
        return settings.DEPLOYED and not settings.TESTING_DEPLOYED

from __future__ import absolute_import

from django.conf import settings
from collections import deque
import os
import time
import socket
import logging
import ujson
import requests
import cPickle as pickle
import atexit
import sys
import signal
import tornado
import random
from zephyr.lib.utils import statsd
from zephyr.middleware import async_request_restart
from zephyr.models import get_client

# The idle timeout used to be a week, but we found that in that
# situation, queues from dead browser sessions would grow quite large
# due to the accumulation of message data in those queues.
IDLE_EVENT_QUEUE_TIMEOUT_SECS = 60 * 10
EVENT_QUEUE_GC_FREQ_MSECS = 1000 * 60 * 5
# The heartbeats effectively act as a server-side timeout for
# get_events().  The actual timeout value is randomized for each
# client connection based on the below value.  We ensure that the
# maximum timeout value is 55 seconds, to deal with crappy home
# wireless routers that kill "inactive" http connections.
HEARTBEAT_MIN_FREQ_SECS = 45

class ClientDescriptor(object):
    def __init__(self, user_profile_id, id, event_types, client_type,
                 apply_markdown=True):
        self.user_profile_id = user_profile_id
        self.current_handler = None
        self.event_queue = EventQueue(id)
        self.event_types = event_types
        self.last_connection_time = time.time()
        self.apply_markdown = apply_markdown
        self.client_type = client_type
        self._timeout_handle = None

    def prepare_for_pickling(self):
        self.current_handler = None
        self._timeout_handle = None

    def add_event(self, event):
        if self.current_handler is not None:
            async_request_restart(self.current_handler._request)

        self.event_queue.push(event)
        if self.current_handler is not None:
            try:
                self.current_handler.humbug_finish(dict(result='success', msg='',
                                                        events=[event],
                                                        queue_id=self.event_queue.id),
                                                   self.current_handler._request,
                                                   apply_markdown=self.apply_markdown)
            except socket.error:
                pass
            self.disconnect_handler()

    def accepts_event_type(self, type):
        if self.event_types is None:
            return True
        return type in self.event_types

    def idle(self, now):
        return (self.current_handler is None
                and now - self.last_connection_time >= IDLE_EVENT_QUEUE_TIMEOUT_SECS)

    def connect_handler(self, handler):
        self.current_handler = handler
        self.last_connection_time = time.time()
        def timeout_callback():
            self._timeout_handle = None
            # All clients get heartbeat events
            self.add_event(dict(type='heartbeat'))
        ioloop = tornado.ioloop.IOLoop.instance()
        heartbeat_time = time.time() + HEARTBEAT_MIN_FREQ_SECS + random.randint(0, 10)
        self._timeout_handle = ioloop.add_timeout(heartbeat_time, timeout_callback)

    def disconnect_handler(self):
        self.current_handler = None
        if self._timeout_handle is not None:
            ioloop = tornado.ioloop.IOLoop.instance()
            ioloop.remove_timeout(self._timeout_handle)
            self._timeout_handle = None

class EventQueue(object):
    def __init__(self, id):
        self.queue = deque()
        self.next_event_id = 0
        self.id = id

    def push(self, event):
        event['id'] = self.next_event_id
        self.next_event_id += 1
        self.queue.append(event)

    def pop(self):
        return self.queue.popleft()

    def empty(self):
        return len(self.queue) == 0

    def prune(self, through_id):
        while not self.empty() and self.queue[0]['id'] <= through_id:
            self.pop()

    def contents(self):
        return list(self.queue)

# maps queue ids to client descriptors
clients = {}
# maps user id to list of client descriptors
user_clients = {}

# list of registered gc hooks.
# each one will be called with a user profile id, queue, and bool
# last_for_client that is true if this is the last queue pertaining
# to this user_profile_id
# that is about to be deleted
gc_hooks = []

next_queue_id = 0

def add_client_gc_hook(hook):
    gc_hooks.append(hook)

def get_client_descriptor(queue_id):
    return clients.get(queue_id)

def get_client_descriptors_for_user(user_profile_id):
    return user_clients.get(user_profile_id, [])

def allocate_client_descriptor(user_profile_id, event_types, client_type,
                               apply_markdown):
    global next_queue_id
    id = str(settings.SERVER_GENERATION) + ':' + str(next_queue_id)
    next_queue_id += 1
    client = ClientDescriptor(user_profile_id, id, event_types, client_type,
                              apply_markdown)
    clients[id] = client
    user_clients.setdefault(user_profile_id, []).append(client)
    return client

def gc_event_queues():
    start = time.time()
    to_remove = set()
    affected_users = set()
    for (id, client) in clients.iteritems():
        if client.idle(start):
            to_remove.add(id)
            affected_users.add(client.user_profile_id)

    for user_id in affected_users:
        new_client_list = filter(lambda c: c.event_queue.id not in to_remove,
                                user_clients[user_id])
        if len(new_client_list) == 0:
            del user_clients[user_id]
        else:
            user_clients[user_id] = new_client_list

    for id in to_remove:
        for cb in gc_hooks:
            cb(clients[id].user_profile_id, clients[id], clients[id].user_profile_id not in user_clients)
        del clients[id]

    logging.info(('Tornado removed %d idle event queues owned by %d users in %.3fs.'
                  + '  Now %d active queues')
                 % (len(to_remove), len(affected_users), time.time() - start,
                    len(clients)))
    statsd.gauge('tornado.active_queues', len(clients))
    statsd.gauge('tornado.active_users', len(user_clients))

def dump_event_queues():
    start = time.time()
    # Remove unpickle-able attributes
    for client in clients.itervalues():
        client.prepare_for_pickling()

    with file(settings.PERSISTENT_QUEUE_FILENAME, "w") as stored_queues:
        pickle.dump(clients, stored_queues)

    logging.info('Tornado dumped %d event queues in %.3fs'
                 % (len(clients), time.time() - start))

def load_event_queues():
    global clients
    start = time.time()
    try:
        with file(settings.PERSISTENT_QUEUE_FILENAME, "r") as stored_queues:
            clients = pickle.load(stored_queues)
    except (IOError, EOFError):
        pass

    for client in clients.itervalues():
        # The following client_type block can be dropped once we've
        # cleared out all our old event queues
        if not hasattr(client, 'client_type'):
            client.client_type = get_client("website")
        user_clients.setdefault(client.user_profile_id, []).append(client)

    logging.info('Tornado loaded %d event queues in %.3fs'
                 % (len(clients), time.time() - start))

def send_restart_events():
    event = dict(type='restart', server_generation=settings.SERVER_GENERATION)
    for client in clients.itervalues():
        # All clients get restart events
        client.add_event(event.copy())

def setup_event_queue():
    load_event_queues()
    atexit.register(dump_event_queues)
    # Make sure we dump event queues even if we exit via signal
    signal.signal(signal.SIGTERM, lambda signum, stack: sys.exit(1))

    try:
        os.remove(settings.PERSISTENT_QUEUE_FILENAME)
    except OSError:
        pass

    # Set up event queue garbage collection
    ioloop = tornado.ioloop.IOLoop.instance()
    pc = tornado.ioloop.PeriodicCallback(gc_event_queues,
                                         EVENT_QUEUE_GC_FREQ_MSECS, ioloop)
    pc.start()

    send_restart_events()

# The following functions are called from Django

# Workaround to support the Python-requests 1.0 transition of .json
# from a property to a function
requests_json_is_function = callable(requests.Response.json)
def extract_json_response(resp):
    if requests_json_is_function:
        return resp.json()
    else:
        return resp.json

def request_event_queue(user_profile, user_client, apply_markdown,
                        event_types=None):
    if settings.TORNADO_SERVER:
        req = {'dont_block'    : 'true',
               'apply_markdown': ujson.dumps(apply_markdown),
               'client'        : 'internal',
               'user_client'   : user_client.name}
        if event_types is not None:
            req['event_types'] = ujson.dumps(event_types)
        resp = requests.get(settings.TORNADO_SERVER + '/api/v1/events',
                            auth=requests.auth.HTTPBasicAuth(user_profile.email,
                                                             user_profile.api_key),
                            params=req)

        resp.raise_for_status()

        return extract_json_response(resp)['queue_id']

    return None

def get_user_events(user_profile, queue_id, last_event_id):
    if settings.TORNADO_SERVER:
        resp = requests.get(settings.TORNADO_SERVER + '/api/v1/events',
                            auth=requests.auth.HTTPBasicAuth(user_profile.email,
                                                             user_profile.api_key),
                            params={'queue_id'     : queue_id,
                                    'last_event_id': last_event_id,
                                    'dont_block'   : 'true',
                                    'client'       : 'internal'})

        resp.raise_for_status()

        return extract_json_response(resp)['events']

from diff_match_patch import diff_match_patch
import platform
import logging

# TODO: handle changes in link hrefs

def highlight_with_class(klass, text):
    return '<span class="%s">%s</span>' % (klass, text)

def highlight_inserted(text):
    return highlight_with_class('highlight_text_inserted', text)

def highlight_deleted(text):
    return highlight_with_class('highlight_text_deleted', text)

def highlight_replaced(text):
    return highlight_with_class('highlight_text_replaced', text)

def chunkize(text, in_tag):
    start = 0
    idx = 0
    chunks = []
    for c in text:
        if c == '<':
            in_tag = True
            if start != idx:
                chunks.append(('text', text[start:idx]))
            start = idx
        elif c == '>':
            in_tag = False
            if start != idx + 1:
                chunks.append(('tag', text[start:idx + 1]))
            start = idx + 1
        idx += 1

    if start != idx:
        chunks.append(('tag' if in_tag else 'text', text[start:idx]))
    return chunks, in_tag

def highlight_chunks(chunks, highlight_func):
    retval = ''
    for type, text in chunks:
        if type == 'text':
            retval += highlight_func(text)
        else:
            retval += text
    return retval

def verify_html(html):
    # TODO: Actually parse the resulting HTML to ensure we don't
    # create mal-formed markup.  This is unfortunately hard because
    # we both want pretty strict parsing and we want to parse html5
    # fragments.  For now, we do a basic sanity check.
    in_tag = False
    for c in html:
        if c == '<':
            if in_tag:
                return False
            in_tag = True
        elif c == '>':
            if not in_tag:
                return False
            in_tag = False
    if in_tag:
        return False
    return True

def highlight_html_differences(s1, s2):
    differ = diff_match_patch()
    ops = differ.diff_main(s1, s2)
    differ.diff_cleanupSemantic(ops)
    retval = ''
    in_tag = False

    idx = 0
    while idx < len(ops):
        op, text = ops[idx]
        next_op = None
        if idx != len(ops) - 1:
            next_op, next_text = ops[idx + 1]
        if op == diff_match_patch.DIFF_DELETE and next_op == diff_match_patch.DIFF_INSERT:
            # Replace operation
            chunks, in_tag = chunkize(next_text, in_tag)
            retval += highlight_chunks(chunks, highlight_replaced)
            idx += 1
        elif op == diff_match_patch.DIFF_INSERT and next_op == diff_match_patch.DIFF_DELETE:
            # Replace operation
            # I have no idea whether diff_match_patch generates inserts followed
            # by deletes, but it doesn't hurt to handle them
            chunks, in_tag = chunkize(text, in_tag)
            retval += highlight_chunks(chunks, highlight_replaced)
            idx += 1
        elif op == diff_match_patch.DIFF_DELETE:
            retval += highlight_deleted('&nbsp;')
        elif op == diff_match_patch.DIFF_INSERT:
            chunks, in_tag = chunkize(text, in_tag)
            retval += highlight_chunks(chunks, highlight_inserted)
        elif op == diff_match_patch.DIFF_EQUAL:
            chunks, in_tag = chunkize(text, in_tag)
            retval += text
        idx += 1

    if not verify_html(retval):
        from zephyr.lib.actions import internal_send_message
        # We probably want more information here
        logging.getLogger('').error('HTML diff produced mal-formed HTML')

        subject = "HTML diff failure on %s" % (platform.node(),)
        internal_send_message("error-bot@zulip.com", "stream",
                              "errors", subject, "HTML diff produced malformed HTML")
        return s2

    return retval


"""
Context managers, i.e. things you can use with the 'with' statement.
"""

from __future__ import absolute_import

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

from __future__ import absolute_import

from zephyr.lib.initial_password import initial_password
from zephyr.models import Realm, Stream, UserProfile, Huddle, \
    Subscription, Recipient, Client, get_huddle_hash, email_to_domain
from zephyr.lib.create_user import create_user_profile

def bulk_create_realms(realm_list):
    existing_realms = set(r.domain for r in Realm.objects.select_related().all())

    realms_to_create = []
    for domain in realm_list:
        if domain not in existing_realms:
            realms_to_create.append(Realm(domain=domain))
            existing_realms.add(domain)
    Realm.objects.bulk_create(realms_to_create)

def bulk_create_users(realms, users_raw):
    """
    Creates and saves a UserProfile with the given email.
    Has some code based off of UserManage.create_user, but doesn't .save()
    """
    users = []
    existing_users = set(u.email for u in UserProfile.objects.all())
    for (email, full_name, short_name, active) in users_raw:
        if email in existing_users:
            continue
        users.append((email, full_name, short_name, active))
        existing_users.add(email)

    # Now create user_profiles
    profiles_to_create = []
    for (email, full_name, short_name, active) in users:
        domain = email_to_domain(email)
        profile = create_user_profile(realms[domain], email,
                                      initial_password(email), active, False,
                                      full_name, short_name, None)
        profiles_to_create.append(profile)
    UserProfile.objects.bulk_create(profiles_to_create)

    profiles_by_email = {}
    profiles_by_id = {}
    for profile in UserProfile.objects.select_related().all():
        profiles_by_email[profile.email] = profile
        profiles_by_id[profile.id] = profile

    recipients_to_create = []
    for (email, _, _, _) in users:
        recipients_to_create.append(Recipient(type_id=profiles_by_email[email].id,
                                              type=Recipient.PERSONAL))
    Recipient.objects.bulk_create(recipients_to_create)

    recipients_by_email = {}
    for recipient in Recipient.objects.filter(type=Recipient.PERSONAL):
        recipients_by_email[profiles_by_id[recipient.type_id].email] = recipient

    subscriptions_to_create = []
    for (email, _, _, _) in users:
        subscriptions_to_create.append(
            Subscription(user_profile_id=profiles_by_email[email].id,
                         recipient=recipients_by_email[email]))
    Subscription.objects.bulk_create(subscriptions_to_create)

def bulk_create_streams(realms, stream_list):
    existing_streams = set((stream.realm.domain, stream.name.lower())
                           for stream in Stream.objects.select_related().all())
    streams_to_create = []
    for (domain, name) in stream_list:
        if (domain, name.lower()) not in existing_streams:
            streams_to_create.append(Stream(realm=realms[domain], name=name))
    Stream.objects.bulk_create(streams_to_create)

    recipients_to_create = []
    for stream in Stream.objects.select_related().all():
        if (stream.realm.domain, stream.name.lower()) not in existing_streams:
            recipients_to_create.append(Recipient(type_id=stream.id,
                                                  type=Recipient.STREAM))
    Recipient.objects.bulk_create(recipients_to_create)

def bulk_create_clients(client_list):
    existing_clients = set(client.name for client in Client.objects.select_related().all())

    clients_to_create = []
    for name in client_list:
        if name not in existing_clients:
            clients_to_create.append(Client(name=name))
            existing_clients.add(name)
    Client.objects.bulk_create(clients_to_create)

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
    Huddle.objects.bulk_create(huddles_to_create)

    for huddle in Huddle.objects.all():
        huddles[huddle.huddle_hash] = huddle
        huddles_by_id[huddle.id] = huddle

    recipients_to_create = []
    for (huddle_hash, _) in huddle_set:
        recipients_to_create.append(Recipient(type_id=huddles[huddle_hash].id, type=Recipient.HUDDLE))
    Recipient.objects.bulk_create(recipients_to_create)

    huddle_recipients = {}
    for recipient in Recipient.objects.filter(type=Recipient.HUDDLE):
        huddle_recipients[huddles_by_id[recipient.type_id].huddle_hash] = recipient

    subscriptions_to_create = []
    for (huddle_hash, huddle_user_ids) in huddle_set:
        for user_id in huddle_user_ids:
            subscriptions_to_create.append(Subscription(active=True, user_profile_id=user_id,
                                                        recipient=huddle_recipients[huddle_hash]))
    Subscription.objects.bulk_create(subscriptions_to_create)

# -*- coding: utf-8 -*-
from __future__ import absolute_import

import hashlib
from time import sleep
from django.conf import settings

def statsd_key(val, clean_periods=False):
    if not isinstance(val, str):
        val = str(val)

    if ':' in val:
        val = val.split(':')[0]
    val = val.replace('-', "_")
    if clean_periods:
        val = val.replace('.', '_')

    return val

class StatsDWrapper(object):
    """Transparently either submit metrics to statsd
    or do nothing without erroring out"""

    # Backported support for gauge deltas
    # as our statsd server supports them but supporting
    # pystatsd is not released yet
    def _our_gauge(self, stat, value, rate=1, delta=False):
            """Set a gauge value."""
            from django_statsd.clients import statsd
            if delta:
                value = '%+g|g' % (value,)
            else:
                value = '%g|g' % (value,)
            statsd._send(stat, value, rate)

    def __getattr__(self, name):
        # Hand off to statsd if we have it enabled
        # otherwise do nothing
        if name in ['timer', 'timing', 'incr', 'decr', 'gauge']:
            if settings.USING_STATSD:
                from django_statsd.clients import statsd
                if name == 'gauge':
                    return self._our_gauge
                else:
                    return getattr(statsd, name)
            else:
                return lambda *args, **kwargs: None

        raise AttributeError

statsd = StatsDWrapper()

# Runs the callback with slices of all_list of a given batch_size
def run_in_batches(all_list, batch_size, callback, sleep_time = 0, logger = None):
    if len(all_list) == 0:
        return

    limit = (len(all_list) / batch_size) + 1;
    for i in xrange(limit):
        start = i*batch_size
        end = (i+1) * batch_size
        if end >= len(all_list):
            end = len(all_list)
        batch = all_list[start:end]

        if logger:
            logger("Executing %s in batch %s of %s" % (end-start, i+1, limit))

        callback(batch)

        if i != limit - 1:
            sleep(sleep_time)

def make_safe_digest(string, hash_func=hashlib.sha1):
    """
    return a hex digest of `string`.
    """
    # hashlib.sha1, md5, etc. expect bytes, so non-ASCII strings must
    # be encoded.
    return hash_func(string.encode('utf-8')).hexdigest()


def log_statsd_event(name):
    """
    Sends a single event to statsd with the desired name and the current timestamp

    This can be used to provide vertical lines in generated graphs,
    for example when doing a prod deploy, bankruptcy request, or
    other one-off events

    Note that to draw this event as a vertical line in graphite
    you can use the drawAsInfinite() command
    """
    event_name = "events.%s" % (name,)
    statsd.incr(event_name)

from __future__ import absolute_import

import code
import traceback
import signal

# Interactive debugging code from
# http://stackoverflow.com/questions/132058/showing-the-stack-trace-from-a-running-python-application
# (that link also points to code for an interactive remote debugger
# setup, which we might want if we move Tornado to run in a daemon
# rather than via screen).
def interactive_debug(sig, frame):
    """Interrupt running process, and provide a python prompt for
    interactive debugging."""
    d={'_frame':frame}         # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    message  = "Signal recieved : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i = code.InteractiveConsole(d)
    i.interact(message)

# SIGUSR1 => Just print the stack
# SIGUSR2 => Print stack + open interactive debugging shell
def interactive_debug_listen():
    signal.signal(signal.SIGUSR1, lambda sig, stack: traceback.print_stack(stack))
    signal.signal(signal.SIGUSR2, interactive_debug)

from __future__ import absolute_import

import re
import os.path
import sourcemap


class SourceMap(object):
    '''Map (line, column) pairs from generated to source file.'''

    def __init__(self, sourcemap_dir):
        self._dir = sourcemap_dir
        self._indices = {}

    def _index_for(self, minified_src):
        '''Return the source map index for minified_src, loading it if not
           already loaded.'''
        if minified_src not in self._indices:
            with open(os.path.join(self._dir, minified_src + '.map')) as fp:
                self._indices[minified_src] = sourcemap.load(fp)

        return self._indices[minified_src]

    def annotate_stacktrace(self, stacktrace):
        out = ''
        for ln in stacktrace.splitlines():
            out += ln + '\n'
            match = re.search(r'/static/min/(.+)(\.[0-9a-f]+)\.js:(\d+):(\d+)', ln)
            if match:
                # Get the appropriate source map for the minified file.
                minified_src = match.groups()[0] + '.js'
                index = self._index_for(minified_src)

                gen_line, gen_col = map(int, match.groups()[2:4])
                # The sourcemap lib is 0-based, so subtract 1 from line and col.
                try:
                    result = index.lookup(line=gen_line-1, column=gen_col-1)
                    out += ('       = %s line %d column %d\n' %
                        (result.src, result.src_line+1, result.src_col+1))
                except IndexError:
                    out +=  '       [Unable to look up in source map]\n'

            if ln.startswith('    at'):
                out += '\n'
        return out

import re

from django.db.models import F, Q
import zephyr.models

# Match multi-word string between @** ** or match any one-word
# sequences after @
find_mentions = r'(?<![^\s\'\"\(,:<])@(?:\*\*([^\*]+)\*\*|(\w+))'

wildcards = ['all', 'everyone']

def find_user_for_mention(mention, realm):
    if mention in wildcards:
        return (True, None)

    try:
        user = zephyr.models.UserProfile.objects.filter(
                Q(full_name__iexact=mention) | Q(short_name__iexact=mention),
                is_active=True,
                realm=realm).order_by("id")[0]
    except IndexError:
        user = None

    return (False, user)

from __future__ import absolute_import

import datetime
import calendar
from django.utils.timezone import utc

def timestamp_to_datetime(timestamp):
    return datetime.datetime.utcfromtimestamp(float(timestamp)).replace(tzinfo=utc)

def datetime_to_timestamp(datetime_object):
    return calendar.timegm(datetime_object.timetuple())

from __future__ import absolute_import

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
import os.path
import glob
import twitter
import platform
import time

import httplib2

from hashlib import sha1

from django.core import mail
from django.conf import settings

from zephyr.lib.avatar  import gravatar_hash
from zephyr.lib.bugdown import codehilite, fenced_code
from zephyr.lib.bugdown.fenced_code import FENCE_RE
from zephyr.lib.timeout import timeout, TimeoutExpired
from zephyr.lib.cache import cache_with_key, cache_get_many, cache_set_many
import zephyr.lib.mention as mention


if settings.USING_EMBEDLY:
    from embedly import Embedly
    embedly_client = Embedly(settings.EMBEDLY_KEY, timeout=2.5)

# Format version of the bugdown rendering; stored along with rendered
# messages so that we can efficiently determine what needs to be re-rendered
version = 1

def list_of_tlds():
    # HACK we manually blacklist .py
    blacklist = ['PY\n', ]

    # tlds-alpha-by-domain.txt comes from http://data.iana.org/TLD/tlds-alpha-by-domain.txt
    tlds_file = os.path.join(os.path.dirname(__file__), 'tlds-alpha-by-domain.txt')
    tlds = [tld.lower().strip() for tld in open(tlds_file, 'r')
                if not tld in blacklist and not tld[0].startswith('#')]
    tlds.sort(key=len, reverse=True)
    return tlds

def walk_tree(root, processor, stop_after_first=False):
    results = []
    stack = [root]

    while stack:
        currElement = stack.pop()
        for child in currElement.getchildren():
            if child.getchildren():
                stack.append(child)

            result = processor(child)
            if result is not None:
                results.append(result)
                if stop_after_first:
                    return results

    return results

def add_a(root, url, link, height=None):
    div = markdown.util.etree.SubElement(root, "div")
    div.set("class", "message_inline_image");
    a = markdown.util.etree.SubElement(div, "a")
    a.set("href", link)
    a.set("target", "_blank")
    a.set("title", link)
    img = markdown.util.etree.SubElement(a, "img")
    img.set("src", url)

def hash_embedly_url(link):
    return 'embedly:' + sha1(link).hexdigest()

@cache_with_key(lambda tweet_id: tweet_id, cache_name="database", with_statsd_key="tweet_data")
def fetch_tweet_data(tweet_id):
    if settings.TEST_SUITE:
        import testing_mocks
        res = testing_mocks.twitter(tweet_id)
    else:
        if settings.STAGING_DEPLOYED or settings.TESTING_DEPLOYED:
            # Application: "Humbug HQ"
            api = twitter.Api(consumer_key = 'xxxxxxxxxxxxxxxxxxxxxx',
                              consumer_secret = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                              access_token_key = 'xxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                              access_token_secret = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        elif settings.DEPLOYED:
            # This is the real set of API credentials used by our real server,
            # and we probably shouldn't test with it just so we don't waste its requests
            # Application: "Humbug HQ - Production"
            api = twitter.Api(consumer_key = 'xxxxxxxxxxxxxxxxxxxxx',
                              consumer_secret = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                              access_token_key = 'xxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                              access_token_secret = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        else:
            # Application: "Humbug HQ Test"
            api = twitter.Api(consumer_key = 'xxxxxxxxxxxxxxxxxxxxxx',
                              consumer_secret = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                              access_token_key = 'xxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                              access_token_secret = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        try:
            # Sometimes Twitter hangs on responses.  Timing out here
            # will cause the Tweet to go through as-is with no inline
            # preview, rather than having the message be rejected
            # entirely. This timeout needs to be less than our overall
            # formatting timeout.
            res = timeout(3, api.GetStatus, tweet_id).AsDict()
        except TimeoutExpired as e:
            # We'd like to try again later and not cache the bad result,
            # so we need to re-raise the exception (just as though
            # we were being rate-limited)
            raise
        except twitter.TwitterError as e:
            t = e.args[0]
            if len(t) == 1 and ('code' in t[0]) and (t[0]['code'] == 34):
                # Code 34 means that the message doesn't exist; return
                # None so that we will cache the error
                return None
            elif len(t) == 1 and ('code' in t[0]) and (t[0]['code'] == 88 or
                                                       t[0]['code'] == 130):
                # Code 88 means that we were rate-limited and 130
                # means Twitter is having capacity issues; either way
                # just raise the error so we don't cache None and will
                # try again later.
                raise
            else:
                # It's not clear what to do in cases of other errors,
                # but for now it seems reasonable to log at error
                # level (so that we get notified), but then cache the
                # failure to proceed with our usual work
                logging.error(traceback.format_exc())
                return None
    return res

def get_tweet_id(url):
    parsed_url = urlparse.urlparse(url)
    if not (parsed_url.netloc == 'twitter.com' or parsed_url.netloc.endswith('.twitter.com')):
        return False

    tweet_id_match = re.match(r'^/.*?/status(es)?/(?P<tweetid>\d{18})$', parsed_url.path)
    if not tweet_id_match:
        return False
    return tweet_id_match.group("tweetid")


class InlineInterestingLinkProcessor(markdown.treeprocessors.Treeprocessor):
    def is_image(self, url):
        parsed_url = urlparse.urlparse(url)
        # List from http://support.google.com/chromeos/bin/answer.py?hl=en&answer=183093
        for ext in [".bmp", ".gif", ".jpg", "jpeg", ".png", ".webp"]:
            if parsed_url.path.lower().endswith(ext):
                return True
        return False

    def dropbox_image(self, url):
        if not self.is_image(url):
            return None
        parsed_url = urlparse.urlparse(url)
        if (parsed_url.netloc == 'dropbox.com' or parsed_url.netloc.endswith('.dropbox.com')) \
                and (parsed_url.path.startswith('/s/') or parsed_url.path.startswith('/sh/')):
            return "%s?dl=1" % (url,)
        return None

    def youtube_image(self, url):
        # Youtube video id extraction regular expression from http://pastebin.com/KyKAFv1s
        # If it matches, match.group(2) is the video id.
        youtube_re = r'^((?:https?://)?(?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/)(?:(?:(?:v|embed)/)|(?:(?:watch(?:_popup)?(?:\.php)?)?(?:\?|#!?)(?:.+&)?v=)))?([0-9A-Za-z_-]+)(?(1).+)?$'
        match = re.match(youtube_re, url)
        if match is None:
            return None
        return "http://i.ytimg.com/vi/%s/default.jpg" % (match.group(2),)

    def twitter_link(self, url):
        tweet_id = get_tweet_id(url)

        if not tweet_id:
            return None

        try:
            res = fetch_tweet_data(tweet_id)
            if res is None:
                return None
            user = res['user']
            tweet = markdown.util.etree.Element("div")
            tweet.set("class", "twitter-tweet")
            img_a = markdown.util.etree.SubElement(tweet, 'a')
            img_a.set("href", url)
            img_a.set("target", "_blank")
            profile_img = markdown.util.etree.SubElement(img_a, 'img')
            profile_img.set('class', 'twitter-avatar')
            # For some reason, for, e.g. tweet 285072525413724161,
            # python-twitter does not give us a
            # profile_image_url_https, but instead puts that URL in
            # profile_image_url. So use _https if available, but fall
            # back gracefully.
            image_url = user.get('profile_image_url_https', user['profile_image_url'])
            profile_img.set('src', image_url)
            p = markdown.util.etree.SubElement(tweet, 'p')
            p.text = res['text']
            span = markdown.util.etree.SubElement(tweet, 'span')
            span.text = "- %s (@%s)" % (user['name'], user['screen_name'])

            return tweet
        except:
            # We put this in its own try-except because it requires external
            # connectivity. If Twitter flakes out, we don't want to not-render
            # the entire message; we just want to not show the Twitter preview.
            logging.warning(traceback.format_exc())
            return None

    def do_embedly(self, root, supported_urls):
        # embed.ly support is disabled until it can be
        # properly debugged.
        #
        # We're not deleting the code for now, since we expect to
        # restore it and want to be able to update it along with
        # future refactorings rather than keeping it as a separate
        # branch.
        if not settings.USING_EMBEDLY:
            return

        # We want this to be able to easily reverse the hashing later
        keys_to_links = dict((hash_embedly_url(link), link) for link in supported_urls)
        cache_hits = cache_get_many(keys_to_links.keys(), cache_name="database")

        # Construct a dict of url => oembed_data pairs
        oembeds = dict((keys_to_links[key], cache_hits[key]) for key in cache_hits)

        to_process = [url for url in supported_urls if not url in oembeds]
        to_cache = {}

        if to_process:
            # Don't touch embed.ly if we have everything cached.
            try:
                responses = embedly_client.oembed(to_process, maxwidth=250)
            except httplib2.socket.timeout:
                # We put this in its own try-except because it requires external
                # connectivity. If embedly flakes out, we don't want to not-render
                # the entire message; we just want to not show the embedly preview.
                logging.warning("Embedly Embed timeout for URLs: %s" % (" ".join(to_process)))
                logging.warning(traceback.format_exc())
                return root
            except Exception:
                # If things break for any other reason, don't make things sad.
                logging.warning(traceback.format_exc())
                return root
            for oembed_data in responses:
                # Don't cache permanent errors
                if oembed_data["type"] == "error" and \
                        oembed_data["error_code"] in (500, 501, 503):
                    continue
                # Convert to dict because otherwise pickling won't work.
                to_cache[oembed_data["original_url"]] = dict(oembed_data)

            # Cache the newly collected data to the database
            cache_set_many(dict((hash_embedly_url(link), to_cache[link]) for link in to_cache),
                           cache_name="database")
            oembeds.update(to_cache)

        # Now let's process the URLs in order
        for link in supported_urls:
            oembed_data = oembeds[link]

            if oembed_data["type"] in ("link"):
                continue
            elif oembed_data["type"] in ("video", "rich") and "script" not in oembed_data["html"]:
                placeholder = self.markdown.htmlStash.store(oembed_data["html"], safe=True)
                el = markdown.util.etree.SubElement(root, "p")
                el.text = placeholder
            else:
                try:
                    add_a(root,
                          oembed_data["thumbnail_url"],
                          link,
                          height=oembed_data["thumbnail_height"])
                except KeyError:
                    # We didn't have a thumbnail, so let's just bail and keep on going...
                    continue
        return root

    def run(self, root):
        # Get all URLs from the blob
        found_urls = walk_tree(root, lambda e: e.get("href") if e.tag == "a" else None)

        # If there are more than 5 URLs in the message, don't do inline previews
        if len(found_urls) == 0 or len(found_urls) > 5:
            return

        rendered_tweet = False
        embedly_urls = []
        for url in found_urls:
            dropbox = self.dropbox_image(url)
            if dropbox is not None:
                add_a(root, dropbox, url)
                continue
            if self.is_image(url):
                add_a(root, url, url)
                continue
            if get_tweet_id(url):
                if rendered_tweet:
                    # Only render at most one tweet per message
                    continue
                twitter_data = self.twitter_link(url)
                if twitter_data is None:
                    # This link is not actually a tweet known to twitter
                    continue
                rendered_tweet = True
                div = markdown.util.etree.SubElement(root, "div")
                div.set("class", "inline-preview-twitter")
                div.insert(0, twitter_data)
                continue
            if settings.USING_EMBEDLY:
                if embedly_client.is_supported(url):
                    embedly_urls.append(url)
                    continue
            # NOTE: The youtube code below is inactive at least on
            # staging because embedy.ly is currently handling those
            youtube = self.youtube_image(url)
            if youtube is not None:
                add_a(root, youtube, url)
                continue

        if settings.USING_EMBEDLY:
            self.do_embedly(root, embedly_urls)

class Gravatar(markdown.inlinepatterns.Pattern):
    def handleMatch(self, match):
        img = markdown.util.etree.Element('img')
        img.set('class', 'message_body_gravatar img-rounded')
        img.set('src', 'https://secure.gravatar.com/avatar/%s?d=identicon&s=30'
            % (gravatar_hash(match.group('email')),))
        return img

path_to_emoji = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                             # This should be the root
                             'static', 'third', 'gemoji', 'images', 'emoji', '*.png')
emoji_list = [os.path.splitext(os.path.basename(fn))[0] for fn in glob.glob(path_to_emoji)]

def make_emoji(emoji_name, display_string):
    elt = markdown.util.etree.Element('img')
    elt.set('src', 'static/third/gemoji/images/emoji/%s.png' % (emoji_name,))
    elt.set('class', 'emoji')
    elt.set("alt", display_string)
    elt.set("title", display_string)
    return elt

class Emoji(markdown.inlinepatterns.Pattern):
    def handleMatch(self, match):
        orig_syntax = match.group("syntax")
        name = orig_syntax[1:-1]
        if name not in emoji_list:
            return orig_syntax
        return make_emoji(name, orig_syntax)

def fixup_link(link, target_blank=True):
    """Set certain attributes we want on every link."""
    if target_blank:
        link.set('target', '_blank')
    link.set('title',  link.get('href'))


def sanitize_url(url):
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

    # If there is no scheme or netloc and there is a '@' in the path,
    # treat it as a mailto: and set the appropriate scheme
    if scheme == '' and netloc == '' and '@' in path:
        scheme = 'mailto'

    # Humbug modification: If scheme is not specified, assume http://
    # It's unlikely that users want relative links within zulip.com.
    # We re-enter sanitize_url because netloc etc. need to be re-parsed.
    if not scheme:
        return sanitize_url('http://' + url)

    locless_schemes = ['mailto', 'news']
    if netloc == '' and scheme not in locless_schemes:
        # This fails regardless of anything else.
        # Return immediately to save additional proccessing
        return None

    # Upstream code will accept a URL like javascript://foo because it
    # appears to have a netloc.  Additionally there are plenty of other
    # schemes that do weird things like launch external programs.  To be
    # on the safe side, we whitelist the scheme.
    if scheme not in ('http', 'https', 'ftp', 'mailto'):
        return None

    # Upstream code scans path, parameters, and query for colon characters
    # because
    #
    #    some aliases [for javascript:] will appear to urlparse() to have
    #    no scheme. On top of that relative links (i.e.: "foo/bar.html")
    #    have no scheme.
    #
    # We already converted an empty scheme to http:// above, so we skip
    # the colon check, which would also forbid a lot of legitimate URLs.

    # Url passes all tests. Return url as-is.
    return urlparse.urlunparse((scheme, netloc, path, params, query, fragment))

def url_to_a(url, text = None):
    a = markdown.util.etree.Element('a')

    href = sanitize_url(url)
    if href is None:
        # Rejected by sanitize_url; render it as plain text.
        return url
    if text is None:
        text = url

    a.set('href', href)
    a.text = text
    fixup_link(a, not 'mailto:' in href[:7])
    return a

class AutoLink(markdown.inlinepatterns.Pattern):
    def __init__(self, pattern):
        markdown.inlinepatterns.Pattern.__init__(self, ' ')

        # HACK: we just had python-markdown compile an empty regex.
        # Now replace with the real regex compiled with the flags we want.

        self.pattern = pattern
        self.compiled_re = re.compile("^(.*?)%s(.*?)$" % pattern,
                                      re.DOTALL | re.UNICODE | re.VERBOSE)

    def handleMatch(self, match):
        url = match.group('url')
        return url_to_a(url)

class UListProcessor(markdown.blockprocessors.OListProcessor):
    """ Process unordered list blocks.

        Based on markdown.blockprocessors.UListProcessor, but does not accept
        '+' or '-' as a bullet character."""

    TAG = 'ul'
    RE = re.compile(r'^[ ]{0,3}[*][ ]+(.*)')

class BugdownUListPreprocessor(markdown.preprocessors.Preprocessor):
    """ Allows unordered list blocks that come directly after a
        paragraph to be rendered as an unordered list

        Detects paragraphs that have a matching list item that comes
        directly after a line of text, and inserts a newline between
        to satisfy Markdown"""

    LI_RE = re.compile(r'^[ ]{0,3}[*][ ]+(.*)', re.MULTILINE)
    HANGING_ULIST_RE = re.compile(r'^.+\n([ ]{0,3}[*][ ]+.*)', re.MULTILINE)

    def run(self, lines):
        """ Insert a newline between a paragraph and ulist if missing """
        inserts = 0
        fence = None
        copy = lines[:]
        for i in xrange(len(lines) - 1):
            # Ignore anything that is inside a fenced code block
            m = FENCE_RE.match(lines[i])
            if not fence and m:
                fence = m.group('fence')
            elif fence and m and fence == m.group('fence'):
                fence = None

            # If we're not in a fenced block and we detect an upcoming list
            #  hanging off a paragraph, add a newline
            if not fence and lines[i] and \
                self.LI_RE.match(lines[i+1]) and not self.LI_RE.match(lines[i]):
                copy.insert(i+inserts+1, '')
                inserts += 1
        return copy

# Based on markdown.inlinepatterns.LinkPattern
class LinkPattern(markdown.inlinepatterns.Pattern):
    """ Return a link element from the given match. """
    def handleMatch(self, m):
        # Return the original link syntax as plain text,
        # if the link fails checks.
        orig_syntax = m.group(0)

        href = m.group(9)
        if not href:
            return orig_syntax

        if href[0] == "<":
            href = href[1:-1]
        href = sanitize_url(self.unescape(href.strip()))
        if href is None:
            return orig_syntax

        el = markdown.util.etree.Element('a')
        el.text = m.group(2)
        el.set('href', href)
        fixup_link(el)
        return el

def prepare_realm_pattern(source):
    """ Augment a realm filter so it only matches after start-of-string,
    whitespace, or opening delimiters, won't match if there are word
    characters directly after, and saves what was matched as "name". """
    return r"""(?<![^\s'"\(,:<])(?P<name>""" + source + ')(?!\w)'

# Given a regular expression pattern, linkifies groups that match it
# using the provided format string to construct the URL.
class RealmFilterPattern(markdown.inlinepatterns.Pattern):
    """ Applied a given realm filter to the input """
    def __init__(self, source_pattern, format_string, markdown_instance=None):
        self.pattern = prepare_realm_pattern(source_pattern)
        self.format_string = format_string
        markdown.inlinepatterns.Pattern.__init__(self, self.pattern, markdown_instance)

    def handleMatch(self, m):
        return url_to_a(self.format_string % m.groupdict(),
                        m.group("name"))

class UserMentionPattern(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m):
        name = m.group(2) or m.group(3)

        if current_message:
            wildcard, user = mention.find_user_for_mention(name, current_message.sender.realm)

            if wildcard:
                current_message.mentions_wildcard = True
                email = "*"
            elif user:
                current_message.mentions_user_ids.add(user.id)
                name = user.full_name
                email = user.email
            else:
                # Don't highlight @mentions that don't refer to a valid user
                return None

            el = markdown.util.etree.Element("span")
            el.set('class', 'user-mention')
            el.set('data-user-email', email)
            el.text = "@%s" % (name,)
            return el

# This prevents realm_filters from running on the content of a
# Markdown link, breaking up the link.  This is a monkey-patch, but it
# might be worth sending a version of this change upstream.
class AtomicLinkPattern(LinkPattern):
    def handleMatch(self, m):
        ret = LinkPattern.handleMatch(self, m)
        if not isinstance(ret, basestring):
            ret.text = markdown.util.AtomicString(ret.text)
        return ret

class Bugdown(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        del md.preprocessors['reference']

        for k in ('image_link', 'image_reference', 'automail',
                  'autolink', 'link', 'reference', 'short_reference',
                  'escape', 'strong_em', 'emphasis', 'emphasis2',
                  'strong'):
            del md.inlinePatterns[k]

        # Custom bold syntax: **foo** but not __foo__
        md.inlinePatterns.add('strong',
            markdown.inlinepatterns.SimpleTagPattern(r'(\*\*)([^\n]+?)\2', 'strong'),
            '>not_strong')

        for k in ('hashheader', 'setextheader', 'olist', 'ulist'):
            del md.parser.blockprocessors[k]

        md.parser.blockprocessors.add('ulist', UListProcessor(md.parser), '>hr')

        md.inlinePatterns.add('gravatar', Gravatar(r'!gravatar\((?P<email>[^)]*)\)'), '_begin')
        md.inlinePatterns.add('usermention', UserMentionPattern(mention.find_mentions), '>backtick')
        md.inlinePatterns.add('emoji', Emoji(r'(?<!\S)(?P<syntax>:[^:\s]+:)(?!\S)'), '_begin')
        md.inlinePatterns.add('link', AtomicLinkPattern(markdown.inlinepatterns.LINK_RE, md), '>backtick')

        for (pattern, format_string) in self.getConfig("realm_filters"):
            md.inlinePatterns.add('realm_filters/%s' % (pattern,),
                                  RealmFilterPattern(pattern, format_string), '>link')

        # A link starts at a word boundary, and ends at space, punctuation, or end-of-input.
        #
        # We detect a url either by the `https?://` or by building around the TLD.
        tlds = '|'.join(list_of_tlds())
        link_regex = r"""
            (?<![^\s'"\(,:<])    # Start after whitespace or specified chars
                                 # (Double-negative lookbehind to allow start-of-string)
            (?P<url>             # Main group
                (?:(?:           # Domain part
                    https?://[\w.:@-]+?   # If it has a protocol, anything goes.
                   |(?:                   # Or, if not, be more strict to avoid false-positives
                        (?:[\w-]+\.)+     # One or more domain components, separated by dots
                        (?:%s)            # TLDs (filled in via format from tlds-alpha-by-domain.txt)
                    )
                )
                (?:/             # A path, beginning with /
                    [^\s()\"]*?            # Containing characters that won't end the URL
                    (?: \( [^\s()\"]* \)   # and more characters in matched parens
                        [^\s()\"]*?        # followed by more characters
                    )*                     # zero-or-more sets of paired parens
                )?)              # Path is optional
                | (?:[\w.-]+\@[\w.-]+\.[\w]+) # Email is separate, since it can't have a path
            )
            (?=                            # URL must be followed by (not included in group)
                [:;\?\),\.\'\"\>]*         # Optional punctuation characters
                (?:\Z|\s)                  # followed by whitespace or end of string
            )
            """ % (tlds,)
        md.inlinePatterns.add('autolink', AutoLink(link_regex), '>link')

        md.preprocessors.add('hanging_ulists',
                                 BugdownUListPreprocessor(md),
                                 "_begin")

        md.treeprocessors.add("inline_interesting_links", InlineInterestingLinkProcessor(md), "_end")


md_engines = {}

def make_md_engine(key, opts):
    md_engines[key] = markdown.Markdown(
        safe_mode     = 'escape',
        output_format = 'html',
        extensions    = ['nl2br',
                         codehilite.makeExtension(configs=[
                    ('force_linenos', False),
                    ('guess_lang',    False)]),
                         fenced_code.makeExtension(),
                         Bugdown(opts)])

realm_filters = {
    "default": [],
    "zulip.com": [
        ("#(?P<id>[0-9]{2,8})", "https://trac.humbughq.com/ticket/%(id)s"),
        ],
    }

def subject_links(domain, subject):
    matches = []
    for source_pattern, format_string in realm_filters.get(domain, []):
        pattern = prepare_realm_pattern(source_pattern)
        for m in re.finditer(pattern, subject):
            matches += [format_string % m.groupdict()]
    return matches

for realm in realm_filters.keys():
    # Because of how the Markdown config API works, this has confusing
    # large number of layers of dicts/arrays :(
    make_md_engine(realm, {"realm_filters": [realm_filters[realm], "Realm-specific filters for %s" % (realm,)]})

# We want to log Markdown parser failures, but shouldn't log the actual input
# message for privacy reasons.  The compromise is to replace all alphanumeric
# characters with 'x'.
#
# We also use repr() to improve reproducibility, and to escape terminal control
# codes, which can do surprisingly nasty things.
_privacy_re = re.compile(r'\w', flags=re.UNICODE)
def _sanitize_for_log(md):
    return repr(_privacy_re.sub('x', md))


# Filters such as UserMentionPattern need a message, but python-markdown
# provides no way to pass extra params through to a pattern. Thus, a global.
current_message = None

def do_convert(md, realm_domain=None, message=None):
    """Convert Markdown to HTML, with Humbug-specific settings and hacks."""

    if realm_domain in md_engines:
        _md_engine = md_engines[realm_domain]
    else:
        _md_engine = md_engines["default"]
    # Reset the parser; otherwise it will get slower over time.
    _md_engine.reset()

    global current_message
    current_message = message
    try:
        # Spend at most 5 seconds rendering.
        # Sometimes Python-Markdown is really slow; see
        # https://trac.humbughq.com/ticket/345
        return timeout(5, _md_engine.convert, md)
    except:
        from zephyr.lib.actions import internal_send_message

        cleaned = _sanitize_for_log(md)

        # Output error to log as well as sending a humbug and email
        logging.getLogger('').error('Exception in Markdown parser: %sInput (sanitized) was: %s'
            % (traceback.format_exc(), cleaned))
        subject = "Markdown parser failure on %s" % (platform.node(),)
        internal_send_message("error-bot@zulip.com", "stream",
                "errors", subject, "Markdown parser failed, email sent with details.")
        mail.mail_admins(subject, "Failed message: %s\n\n%s\n\n" % (
                                    cleaned, traceback.format_exc()),
                         fail_silently=False)
        return None
    finally:
        current_message = None

bugdown_time_start = 0
bugdown_total_time = 0
bugdown_total_requests = 0

def get_bugdown_time():
    return bugdown_total_time

def get_bugdown_requests():
    return bugdown_total_requests

def bugdown_stats_start():
    global bugdown_time_start
    bugdown_time_start = time.time()

def bugdown_stats_finish():
    global bugdown_total_time
    global bugdown_total_requests
    global bugdown_time_start
    bugdown_total_requests += 1
    bugdown_total_time += (time.time() - bugdown_time_start)

def convert(md, realm_domain=None, message=None):
    bugdown_stats_start()
    ret = do_convert(md, realm_domain, message)
    bugdown_stats_finish()
    return ret

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
FENCE_RE = re.compile(r'(?P<fence>^(?:~{3,}))[ ]*(\{?\.?(?P<lang>[a-zA-Z0-9_+-]*)\}?)$', re.MULTILINE|re.DOTALL)
FENCED_BLOCK_RE = re.compile( \
    r'(?P<fence>^(?:~{3,}))[ ]*(\{?\.?(?P<lang>[a-zA-Z0-9_+-]*)\}?)?[ ]*\n(?P<code>.*?)(?<=\n)(?P=fence)[ ]*$',
    re.MULTILINE|re.DOTALL
    )
CODE_WRAP = '<pre><code%s>%s</code></pre>'
LANG_TAG = ' class="%s"'

class FencedCodeExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        """ Add FencedBlockPreprocessor to the Markdown instance. """
        md.registerExtension(self)

        # Newer versions of Python-Markdown (starting at 2.3?) have
        # a normalize_whitespace preprocessor that needs to go first.
        position = ('>normalize_whitespace'
            if 'normalize_whitespace' in md.preprocessors
            else '_begin')

        md.preprocessors.add('fenced_code_block',
                                 FencedBlockPreprocessor(md),
                                 position)


class FencedBlockPreprocessor(markdown.preprocessors.Preprocessor):

    def __init__(self, md):
        markdown.preprocessors.Preprocessor.__init__(self, md)

        self.checked_for_codehilite = False
        self.codehilite_conf = {}


    def process_fence(self, m, text):
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
        return '%s\n%s\n%s'% (text[:m.start()], placeholder, text[m.end():])

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
        end = 0
        while 1:
            m = FENCED_BLOCK_RE.search(text)
            if m:
                end = m.end()
                text = self.process_fence(m, text)
            else:
                break


        fence = FENCE_RE.search(text, end)
        if fence:
            # If we found a starting fence but no ending fence,
            # then we add a closing fence before the two newlines that
            # markdown automatically inserts
            if text[-2:] == '\n\n':
                text = text[:-2] + '\n' + fence.group('fence') + text[-2:]
            else:
                text += fence.group('fence')
            m = FENCED_BLOCK_RE.search(text)
            if m:
                text = self.process_fence(m, text)

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


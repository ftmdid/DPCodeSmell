#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "humbug.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


import logging
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

class ReturnTrue(logging.Filter):
    def filter(self, record):
        return True

from django.contrib.auth.models import User
from django.conf import settings

from openid.consumer.consumer import SUCCESS

from zephyr.lib.cache import cache_with_key
from zephyr.lib.cache import user_by_id_cache_key

@cache_with_key(user_by_id_cache_key)
def get_user_by_id(user_id):
    try:
        return User.objects.select_related().get(id=user_id)
    except User.DoesNotExist:
        return None

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
        return get_user_by_id(user_id)

# Adapted from http://djangosnippets.org/snippets/2183/ by user Hangya (September 1, 2010)

class GoogleBackend:
    def authenticate(self, openid_response):
        if openid_response is None:
            return None
        if openid_response.status != SUCCESS:
            return None

        google_email = openid_response.getSigned('http://openid.net/srv/ax/1.0', 'value.email')

        try:
            user = User.objects.get(email__iexact=google_email)
        except User.DoesNotExist:
            # create a new user, or send a message to admins, etc.
            return None

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

# Django settings for humbug project.
import os
import platform
import logging

from zephyr.openid import openid_failure_handler

DEPLOYED = (('humbughq.com' in platform.node())
            or os.path.exists('/etc/humbug-server'))
STAGING_DEPLOYED = (platform.node() == 'staging.humbughq.com')

DEBUG = not DEPLOYED
TEMPLATE_DEBUG = DEBUG
TEST_SUITE = False

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

ADMINS = (
    ('Devel', 'devel@humbughq.com'),
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
    # We can delete this if statement and the whole else clause below
    # once everyone is off sqlite.
    if platform.system() == 'Linux' or False:
        DATABASES["default"].update({
                'PASSWORD': 'xxxxxxxxxxxx',
                'HOST': 'localhost',
                'OPTIONS': {}
                })
    else:
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
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

AUTHENTICATION_BACKENDS = ('humbug.backends.EmailAuthBackend',
                           'humbug.backends.GoogleBackend')

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
    'jstemplate',
    'confirmation',
    'pipeline',
    'zephyr',
)


# Static files and minification

STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# PipelineCachedStorage inserts a file hash into filenames,
# to prevent the browser from using stale files from cache.
#
# Unlike PipelineStorage, it requires the files to exist in
# STATIC_ROOT even for dev servers.  So we only use
# PipelineCachedStorage when not DEBUG.

if DEBUG:
    STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'
else:
    STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

STATIC_ROOT = 'prod-static/collected'

# This is the default behavior from Pipeline, but we set it
# here so that urls.py can read it.
PIPELINE = not DEBUG

# To use minified files in dev, set PIPELINE = True.
#
# You will need to run ./tools/update-prod-static after
# changing static files.

PIPELINE_CSS = {
    'activity': {
        'source_filenames': ('styles/activity.css',),
        'output_filename':  'min/activity.css'
    },
    'portico': {
        'source_filenames': (
            'styles/portico.css',
            'styles/pygments.css',
        ),
        'output_filename': 'min/portico.css'
    },
    'app': {
        'source_filenames': (
            'styles/zephyr.css',
            'styles/pygments.css',
        ),
        'output_filename': 'min/app.css'
    },
}

PIPELINE_JS = {
    'common': {
        'source_filenames': ('js/common.js',),
        'output_filename':  'min/common.js'
    },
    'signup': {
        'source_filenames': ('js/signup.js',),
        'output_filename':  'min/signup.js'
    },
    'app_debug': {
        'source_filenames': ('js/debug.js',),
        'output_filename':  'min/app_debug.js'
    },
    'app': {
        'source_filenames': (
            'js/blueslip.js',
            'js/util.js',
            'js/setup.js',
            'js/rows.js',
            'js/narrow.js',
            'js/reload.js',
            'js/notifications_bar.js',
            'js/compose.js',
            'js/subs.js',
            'js/ui.js',
            'js/typeahead_helper.js',
            'js/search.js',
            'js/composebox_typeahead.js',
            'js/hotkey.js',
            'js/notifications.js',
            'js/hashchange.js',
            'js/invite.js',
            'js/message_list.js',
            'js/zephyr.js',
            'js/activity.js',
            'js/colorspace.js',
            'js/timerender.js',
            'js/tutorial.js',
        ),
        'output_filename': 'min/app.js'
    },
}

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR  = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_YUI_BINARY     = '/usr/bin/env yui-compressor'

# Disable stuffing the entire JavaScript codebase inside an anonymous function.
# We need modules to be externally visible, so that methods can be called from
# event handlers defined in HTML.
PIPELINE_DISABLE_WRAPPER = True


USING_RABBITMQ = DEPLOYED
# This password also appears in servers/configure-rabbitmq
RABBITMQ_PASSWORD = 'xxxxxxxxxxxxxxxx'

# Caching
if DEPLOYED:
    CACHES = {
        'default': {
            'BACKEND':  'django.core.cache.backends.memcached.PyLibMCCache',
            'LOCATION': '127.0.0.1:11211',
            'TIMEOUT':  3600
        },
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
else:
    CACHES = { 'default': {
        'BACKEND':  'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'humbug-default-local-cache',
        'TIMEOUT':  3600,
        'OPTIONS': {
            'MAX_ENTRIES': 100000
        }
    } }
CACHES['database'] = {
            'BACKEND':  'django.core.cache.backends.db.DatabaseCache',
            'LOCATION':  'third_party_api_results',
            # Basically never timeout.  Setting to 0 isn't guaranteed
            # to work, see https://code.djangoproject.com/ticket/9595
            'TIMEOUT': 2000000000,
            'OPTIONS': {
                'MAX_ENTRIES': 100000000,
                'CULL_FREQUENCY': 10,
            },
        }

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
        },
        'nop': {
            '()': 'humbug.ratelimit.ReturnTrue',
        },
    },
    'handlers': {
        'inapp': {
            'level':     'ERROR',
            'class':     'zephyr.handlers.AdminHumbugHandler',
            # For testing the handler delete the next line
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
        # Django has some hardcoded code to add the
        # require_debug_false filter to the mail_admins handler if no
        # filters are specified.  So for testing, one is recommended
        # to replace the list of filters for mail_admins with 'nop'.
        'mail_admins': {
            'level': 'ERROR',
            'class': 'zephyr.handlers.HumbugAdminEmailHandler',
            # For testing the handler replace the filters list with just 'nop'
            'filters': ['EmailLimiter', 'require_debug_false'],
        },
    },
    'loggers': {
        '': {
            'handlers': ['inapp', 'console', 'file', 'mail_admins'],
            'level':    'INFO'
        },
        ## Uncomment the following to get all database queries logged to the console
        # 'django.db': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        # },
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
OPENID_SSO_SERVER_URL = 'https://www.google.com/accounts/o8/id'
OPENID_CREATE_USERS = True
OPENID_RENDER_FAILURE = openid_failure_handler

EVENT_LOG_DIR = 'event_log'

# Polling timeout for get_updates, in milliseconds.
# We configure this here so that the client test suite can override it.
# The default is 55 seconds, to deal with crappy home wireless routers that
# kill "inactive" http connections.
#POLL_TIMEOUT = 55 * 1000
# As a stopgap to deal with increased load, increase the polling
# timeout to 5 minutes.
POLL_TIMEOUT = 5 * 60 * 1000

# The new user tutorial is enabled by default, and disabled for
# client tests.
TUTORIAL_ENABLED = True

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
from django.conf.urls import patterns, url
from django.views.generic import TemplateView, RedirectView
import os.path
import zephyr.forms

urlpatterns = patterns('',
    url(r'^$', 'zephyr.views.home'),
    url(r'^accounts/login/openid/$', 'django_openid_auth.views.login_begin', name='openid-login'),
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

    # Portico-styled page used to provide email confirmation of terms acceptance.
    url(r'^accounts/accept_terms', 'zephyr.views.accounts_accept_terms'),

    # Terms of service and privacy policy
    url(r'^terms$',   TemplateView.as_view(template_name='zephyr/terms.html')),
    url(r'^privacy$', TemplateView.as_view(template_name='zephyr/privacy.html')),

    # "About Humbug" information
    url(r'^what-is-humbug$', TemplateView.as_view(template_name='zephyr/what-is-humbug.html')),
    url(r'^new-user$', TemplateView.as_view(template_name='zephyr/new-user.html')),

    # API and integrations documentation
    url(r'^api$', TemplateView.as_view(template_name='zephyr/api.html')),
    url(r'^integrations$', TemplateView.as_view(template_name='zephyr/integrations.html')),
    url(r'^zephyr$', TemplateView.as_view(template_name='zephyr/zephyr.html')),
    url(r'^apps$', TemplateView.as_view(template_name='zephyr/apps.html')),

    # Job postings
    url(r'^jobs$', TemplateView.as_view(template_name='zephyr/jobs/lead-designer.html')),
    url(r'^jobs/lead-designer$', TemplateView.as_view(template_name='zephyr/jobs/lead-designer.html')),

    # These are json format views used by the web client.  They require a logged in browser.
    url(r'^json/get_updates$',              'zephyr.tornadoviews.json_get_updates'),
    url(r'^json/update_pointer$',           'zephyr.views.json_update_pointer'),
    url(r'^json/get_old_messages$',         'zephyr.views.json_get_old_messages'),
    url(r'^json/get_public_streams$',       'zephyr.views.json_get_public_streams'),
    url(r'^json/send_message$',             'zephyr.views.json_send_message'),
    url(r'^json/invite_users$',             'zephyr.views.json_invite_users'),
    url(r'^json/settings/change$',          'zephyr.views.json_change_settings'),
    url(r'^json/subscriptions/list$',       'zephyr.views.json_list_subscriptions'),
    url(r'^json/subscriptions/remove$',     'zephyr.views.json_remove_subscriptions'),
    url(r'^json/subscriptions/add$',        'zephyr.views.json_add_subscriptions'),
    url(r'^json/subscriptions/exists$',     'zephyr.views.json_stream_exists'),
    url(r'^json/subscriptions/property$',   'zephyr.views.json_subscription_property'),
    url(r'^json/get_subscribers$',          'zephyr.views.json_get_subscribers'),
    url(r'^json/fetch_api_key$',            'zephyr.views.json_fetch_api_key'),
    url(r'^json/get_members$',              'zephyr.views.json_get_members'),
    url(r'^json/update_active_status$',     'zephyr.views.json_update_active_status'),
    url(r'^json/get_active_statuses$',      'zephyr.views.json_get_active_statuses'),
    url(r'^json/tutorial_send_message$',    'zephyr.views.json_tutorial_send_message'),
    url(r'^json/change_enter_sends$',       'zephyr.views.json_change_enter_sends'),
    url(r'^json/get_profile$',              'zephyr.views.json_get_profile'),
    url(r'^json/report_error$',             'zephyr.views.json_report_error'),
    url(r'^json/update_message_flags$',     'zephyr.views.json_update_flags'),

    # These are json format views used by the API.  They require an API key.
    url(r'^api/v1/get_messages$',           'zephyr.tornadoviews.api_get_messages'),
    url(r'^api/v1/get_profile$',            'zephyr.views.api_get_profile'),
    url(r'^api/v1/get_old_messages$',       'zephyr.views.api_get_old_messages'),
    url(r'^api/v1/get_public_streams$',     'zephyr.views.api_get_public_streams'),
    url(r'^api/v1/subscriptions/list$',     'zephyr.views.api_list_subscriptions'),
    url(r'^api/v1/subscriptions/add$',      'zephyr.views.api_add_subscriptions'),
    url(r'^api/v1/subscriptions/remove$',   'zephyr.views.api_remove_subscriptions'),
    url(r'^api/v1/get_subscribers$',        'zephyr.views.api_get_subscribers'),
    url(r'^api/v1/send_message$',           'zephyr.views.api_send_message'),
    url(r'^api/v1/update_pointer$',         'zephyr.views.api_update_pointer'),
    url(r'^api/v1/external/github$',        'zephyr.views.api_github_landing'),
    url(r'^api/v1/get_members$',            'zephyr.views.api_get_members'),

    # This json format view used by the API accepts a username password/pair and returns an API key.
    url(r'^api/v1/fetch_api_key$',          'zephyr.views.api_fetch_api_key'),

    url(r'^robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),

    # Used internally for communication between Django and Tornado processes
    url(r'^notify_new_message$',            'zephyr.tornadoviews.notify_new_message'),
    url(r'^notify_pointer_update$',         'zephyr.tornadoviews.notify_pointer_update'),
)

if not settings.DEPLOYED:
    use_prod_static = getattr(settings, 'PIPELINE', False)
    static_root = os.path.join(settings.SITE_ROOT,
        '../prod-static/serve' if use_prod_static else '../zephyr/static')

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
import time
import optparse
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
print "or AFS tokens."
print ""
sys.exit(1)


# Humbug Inc's internal git plugin configuration.
# The plugin and example config are under api/integrations/

# Leaving all the instructions out of this file to avoid having to
# sync them as we update the comments.

HUMBUG_USER = "humbug+commits@humbughq.com"
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
HUMBUG_SITE = "https://staging.humbughq.com"

#!/usr/bin/env python

"""
Script to provide information about send-receive times.

It supports both munin and nagios outputs

It must be run on a machine that is using the live database for the
Django ORM.
"""

import datetime
import os
import sys
import optparse
import random


def total_seconds(timedelta):
    return (timedelta.microseconds + (timedelta.seconds + timedelta.days * 24 * 3600) * 10**6) / 10.**6

usage = """Usage: send-receive.py [options] [config]

       'config' is optional, if present will return config info.
        Otherwise, returns the output data."""

parser = optparse.OptionParser(usage=usage)
parser.add_option('--site',
                  dest='site',
                  default="https://humbughq.com",
                  action='store')

parser.add_option('--nagios',
                  dest='nagios',
                  action='store_true')

parser.add_option('--munin',
                  dest='munin',
                  action='store_true')
(options, args) = parser.parse_args()

if not options.nagios and not options.munin:
    print 'No output options specified! Please provide --munin or --nagios'
    sys.exit(0)

if len(args) > 2:
    print usage
    sys.exit(0)

if options.munin:
    if len(args) and args[0] == 'config':
        print \
"""graph_title Send-Receive times
graph_info The number of seconds it takes to send and receive a message from the server
graph_args -u 5 -l 0
graph_vlabel RTT (seconds)
sendreceive.label Send-receive round trip time
sendreceive.warning 3
sendreceive.critical 5"""
        sys.exit(0)

sys.path.append('/home/humbug/humbug/api')
import humbug

states = {
    "OK": 0,
    "WARNING": 1,
    "CRITICAL": 2,
    "UNKNOWN": 3
    }

def report(state, time, msg=None):
    if msg:
        print "%s: %s" % (state, msg)
    else:
        print "%s: send time was %s" % (state, time)
    exit(states[state])

def send_humbug(sender, message, nagios):
    result = sender.send_message(message)
    if result["result"] != "success" and nagios:
        report("CRITICAL", "Error sending Humbug, args were: %s, %s" % (message, result))

def get_humbug(recipient, max_message_id):
    return recipient.get_messages({'last': str(max_message_id)})['messages']

# hamlet and othello are default users
sender = "hamlet@humbughq.com"
recipient = "othello@humbughq.com"

humbug_sender = humbug.Client(
    email=sender,
    api_key="dfe1c934d555f4b9538d0d4cfd3069c2",
    verbose=True,
    client="test: Humbug API",
    site=options.site)

humbug_recipient = humbug.Client(
    email=recipient,
    api_key="4e5d97591bec64bf57d2698ffbb563e3",
    verbose=True,
    client="test: Humbug API",
    site=options.site)


max_message_id = humbug_recipient.get_profile().get('max_message_id')
msg_to_send = str(random.getrandbits(64))
time_start = datetime.datetime.now()

send_humbug(humbug_sender, {
    "type": 'private',
    "content": msg_to_send,
    "subject": "time to send",
    "to": recipient,
    }, options.nagios)

msg_content = []

while msg_to_send not in msg_content:
    messages = get_humbug(humbug_recipient, max_message_id)
    time_diff = datetime.datetime.now() - time_start

    # Prevents checking the same messages everytime in the conditional
    # statement of the while loop
    max_message_id = max([msg['id'] for msg in messages])
    msg_content = [m['content'] for m in messages]

    if options.nagios:
        if time_diff.seconds > 3:
            report('WARNING', time_diff)
        if time_diff.seconds > 6:
            report('CRITICAL', time_diff)

if options.munin:
    print "sendreceive.value %s" % total_seconds(time_diff)
elif options.nagios:
    report('OK', time_diff)

# Humbug Inc's internal trac plugin configuration.
# The plugin and example config are under api/integrations/

# Leaving all the instructions out of this file to avoid having to
# sync them as we update the comments.

HUMBUG_USER = "humbug+trac@humbughq.com"
HUMBUG_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
STREAM_FOR_NOTIFICATIONS = "trac"
TRAC_BASE_TICKET_URL = "https://trac.humbughq.com/ticket"

TRAC_NOTIFY_FIELDS = ["description", "summary", "resolution", "comment",
                      "owner"]
HUMBUG_API_PATH = "/home/humbug/humbug/api"
HUMBUG_SITE = "https://staging.humbughq.com"

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
import tempfile
import random

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

DEFAULT_SITE = "https://humbughq.com"

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
            logger.exception("Error checking whether restart is required:")

        time.sleep(sleep_time)
        sleep_count += sleep_time
        if sleep_count > 15:
            sleep_count = 0
            if options.forward_class_messages:
                # Ask the Humbug server about any new classes to subscribe to
                try:
                    update_subscriptions()
                except Exception:
                    logger.exception("Error updating subscriptions from Humbug:")

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
            for line in message["content"].split("\n"))

    zwrite_args = ["zwrite", "-n", "-s", zsig_fullname, "-F", "Zephyr error: See http://zephyr.1ts.org/wiki/df"]
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
        res = humbug_client.add_subscriptions(list(zephyr_subscriptions))
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
synced to your Humbug subscriptions because they do not
use "*" as both the instance and recipient and not one of
the special cases (e.g. personals and mail zephyrs) that
Humbug has a mechanism for forwarding.  Humbug does not
allow subscribing to only some subjects on a Humbug
stream, so this tool has not created a corresponding
Humbug subscription to these lines in ~/.zephyr.subs:
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
If you wish to be subscribed to any Humbug streams related
to these .zephyrs.subs lines, please do so via the Humbug
web interface.
""")) + "\n")
    if verbose:
        logger.info("\nIMPORTANT: Please reload the Humbug app for these changes to take effect.\n")

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
        logger.info("Syncing your ~/.zephyr.subs to your Humbug Subscriptions!")
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
            zsig_fullname = fetch_fullname(options.user)
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

import subprocess

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

import glob
import os
from distutils.core import setup

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
      url='https://humbughq.com/dist/api/',
      packages=['humbug'],
      data_files=[('share/humbug/examples', ["examples/humbugrc", "examples/send-message"])] + \
          [(os.path.join('share/humbug/', relpath),
            glob.glob(os.path.join(relpath, '*'))) for relpath in
           glob.glob("integrations/*")] + \
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


__version__ = "0.1.4"

# Check that we have a recent enough version
# Older versions don't provide the 'json' attribute on responses.
assert(LooseVersion(requests.__version__) >= LooseVersion('0.12.1'))
# In newer versions, the 'json' attribute is a function, not a property
requests_json_is_function = not isinstance(requests.Response.json, property)

API_VERSTRING = "/api/v1/"

def generate_option_group(parser):
    group = optparse.OptionGroup(parser, 'API configuration')
    group.add_option('--site',
                      default=None,
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
                 site=None, client="API"):
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
            self.base_url = site
        else:
            self.base_url = "https://humbughq.com"
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

            if requests_json_is_function:
                json_result = res.json()
            else:
                json_result = res.json
            if json_result is not None:
                end_error_retry(True)
                return json_result
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
            elif options.get('last') is not None:
                options.pop('last')
            res = self.get_messages(options)
            if 'error' in res.get('result'):
                if res["result"] == "http-error":
                    if self.verbose:
                        print "HTTP error fetching messages -- probably a server restart"
                elif res["result"] == "connection-error":
                    if self.verbose:
                        print "Connection error fetching messages -- probably server is temporarily down?"
                else:
                    if self.verbose:
                        print "Server returned error:\n%s" % res["msg"]
                    if res["msg"].startswith("last value of") and \
                            "too old!  Minimum valid is" in res["msg"]:
                        # We may have missed some messages while the
                        # network was down or something, but there's
                        # not really anything we can do about it other
                        # than resuming getting new ones.
                        #
                        # Reset max_message_id to just subscribe to new messages
                        max_message_id = None
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
Client._register('get_members')
Client._register('list_subscriptions',   url='subscriptions/list')
Client._register('add_subscriptions',    url='subscriptions/add',    make_request=_mk_subs)
Client._register('remove_subscriptions', url='subscriptions/remove', make_request=_mk_subs)

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
HUMBUG_USER = "trac@example.com"
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
HUMBUG_SITE = "https://humbughq.com"

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
HUMBUG_USER = "git@example.com"
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
HUMBUG_SITE = "https://humbughq.com"

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import hashlib
from zephyr.lib.cache import cache_with_key, update_user_profile_cache, \
    update_user_cache
from zephyr.lib.initial_password import initial_api_key
import os
from django.db import transaction, IntegrityError
from zephyr.lib import bugdown
from zephyr.lib.avatar import gravatar_hash
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.utils.html import escape
from zephyr.lib.timestamp import datetime_to_timestamp
from django.db.models.signals import post_save

from bitfield import BitField

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

class Realm(models.Model):
    domain = models.CharField(max_length=40, db_index=True, unique=True)
    restricted_to_domain = models.BooleanField(default=True)

    def __repr__(self):
        return "<Realm: %s %s>" % (self.domain, self.id)
    def __str__(self):
        return self.__repr__()

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    full_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100)
    pointer = models.IntegerField()
    last_pointer_updater = models.CharField(max_length=64)
    realm = models.ForeignKey(Realm)
    api_key = models.CharField(max_length=32)
    enable_desktop_notifications = models.BooleanField(default=True)
    enter_sends = models.NullBooleanField(default=False)

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

# Make sure we flush the UserProfile object from our memcached
# whenever we save it.
post_save.connect(update_user_profile_cache, sender=UserProfile)
# And the same for the User object
post_save.connect(update_user_cache, sender=User)

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
    name = models.CharField(max_length=30, db_index=True)
    realm = models.ForeignKey(Realm, db_index=True)
    invite_only = models.NullBooleanField(default=False)

    def __repr__(self):
        return "<Stream: %s>" % (self.name,)
    def __str__(self):
        return self.__repr__()

    def is_public(self):
        return self.realm.domain in ["humbughq.com"]

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
        return "<Recipient: %s (%d, %s)>" % (display_recipient, self.type_id, self.type)

class Client(models.Model):
    name = models.CharField(max_length=30, db_index=True, unique=True)

@cache_with_key(lambda name: 'get_client:%s' % (hashlib.sha1(name).hexdigest(),))
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
    return "stream_by_realm_and_name:%s:%s" % (realm_id, hashlib.sha1(stream_name.strip().lower()).hexdigest())

# get_stream_backend takes either a realm id or a realm
@cache_with_key(get_stream_cache_key)
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

@cache_with_key(lambda type, type_id: "get_recipient:%s:%s" % (type, type_id,))
def get_recipient(type, type_id):
    return Recipient.objects.get(type_id=type_id, type=type)

# NB: This function is currently unused, but may come in handy.
def linebreak(string):
    return string.replace('\n\n', '<p/>').replace('\n', '<br/>')

class Message(models.Model):
    sender = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    subject = models.CharField(max_length=MAX_SUBJECT_LENGTH, db_index=True)
    content = models.TextField()
    rendered_content = models.TextField(null=True)
    rendered_content_version = models.IntegerField(null=True)
    pub_date = models.DateTimeField('date published', db_index=True)
    sending_client = models.ForeignKey(Client)

    def __repr__(self):
        display_recipient = get_display_recipient(self.recipient)
        return "<Message: %s / %s / %r>" % (display_recipient, self.subject, self.sender)
    def __str__(self):
        return self.__repr__()

    @cache_with_key(lambda self, apply_markdown, rendered_content=None: 'message_dict:%d:%d' % (self.id, apply_markdown))
    def to_dict(self, apply_markdown, rendered_content=None):
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
            gravatar_hash     = gravatar_hash(self.sender.user.email),
            client            = self.sending_client.name)

        if apply_markdown and self.rendered_content_version is not None:
            obj['content'] = self.rendered_content
            obj['content_type'] = 'text/html'
        elif apply_markdown:
            if rendered_content is None:
                rendered_content = bugdown.convert(self.content)
                if rendered_content is None:
                    rendered_content = '<p>[Humbug note: Sorry, we could not understand the formatting of your message]</p>'

                # Update the database cache of the rendered content
                self.rendered_content = rendered_content
                self.rendered_content_version = bugdown.version
                self.save()
            obj['content'] = rendered_content
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
    flags = BitField(flags=['read',], default=0)

    class Meta:
        unique_together = ("user_profile", "message")

    def __repr__(self):
        display_recipient = get_display_recipient(self.message.recipient)
        return "<UserMessage: %s / %s (%s)>" % (display_recipient, self.user_profile.user.email, self.flags_dict())

    def flags_dict(self):
        return dict(flags = [flag for flag in self.flags.keys() if getattr(self.flags, flag).is_set])


class Subscription(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    active = models.BooleanField(default=True)
    in_home_view = models.NullBooleanField(default=True)

    class Meta:
        unique_together = ("user_profile", "recipient")

    def __repr__(self):
        return "<Subscription: %r -> %r>" % (self.user_profile, self.recipient)
    def __str__(self):
        return self.__repr__()

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

class UserPresence(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    client = models.ForeignKey(Client)

    # Valid statuses
    ACTIVE = 1
    IDLE = 2

    timestamp = models.DateTimeField('presence changed')
    status = models.PositiveSmallIntegerField(default=ACTIVE)

    class Meta:
        unique_together = ("user_profile", "client")

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

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from zephyr.models import UserProfile, UserActivity, get_client
from zephyr.lib.response import json_success, json_error
from django.utils.timezone import now
from django.db import transaction, IntegrityError
from django.conf import settings
import simplejson
from zephyr.lib.cache import cache_with_key
from zephyr.lib.queue import SimpleQueueClient
from zephyr.lib.timestamp import datetime_to_timestamp
from zephyr.lib.cache import user_profile_by_email_cache_key, \
    user_profile_by_user_cache_key

from functools import wraps

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

if settings.USING_RABBITMQ:
    # Don't try to publish messages to rabbitmq if we're not using
    # it.  UserActivity updates aren't really important for most
    # local development, so skipping publishing them here is
    # reasonable.
    #
    # update_active_status also pushes to rabbitmq, and we don't
    #  want to log it

    activity_queue = SimpleQueueClient()

    def update_user_activity(request, user_profile, client):
        if request.META["PATH_INFO"] == '/json/update_active_status':
            return
        event={'type': 'user_activity',
               'query': request.META["PATH_INFO"],
               'user_profile_id': user_profile.id,
               'time': datetime_to_timestamp(now()),
               'client': client.name}
        activity_queue.json_publish("user_activity", event)
else:
   update_user_activity = lambda request, user_profile, client: None


# I like the all-lowercase name better
require_post = require_POST

@cache_with_key(user_profile_by_user_cache_key)
def get_user_profile_by_user_id(user_id):
    return UserProfile.objects.select_related().get(user_id=user_id)

@cache_with_key(user_profile_by_email_cache_key)
def get_user_profile_by_email(email):
    return UserProfile.objects.select_related().get(user__email__iexact=email)

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
            user_profile = get_user_profile_by_email(email)
        except UserProfile.DoesNotExist:
            return json_error("Invalid user: %s" % (email,))
        if api_key != user_profile.api_key:
            return json_error("Invalid API key for user '%s'" % (email,))
        request._client = client
        request._email = email
        update_user_activity(request, user_profile, client)
        return view_func(request, user_profile, *args, **kwargs)
    return _wrapped_view_func

def authenticate_log_and_execute_json(request, client, view_func, *args, **kwargs):
    if not request.user.is_authenticated():
        return json_error("Not logged in", status=401)
    request._client = client
    user_profile = get_user_profile_by_user_id(request.user.id)
    request._email = user_profile.user.email
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

def json_to_foo(json, type):
    data = simplejson.loads(json)
    if not isinstance(data, type):
        raise ValueError("argument is not a %s" % (type().__class__.__name__))
    return data

def json_to_dict(json):
    return json_to_foo(json, dict)

def json_to_list(json):
    return json_to_foo(json, list)

def json_to_bool(json):
    return json_to_foo(json, bool)

from django.conf import settings
from zephyr.models import Message, UserProfile, UserMessage, UserActivity, \
    Recipient, Stream, get_stream

from zephyr.decorator import asynchronous, authenticated_api_view, \
    authenticated_json_post_view, internal_notify_view, RespondAsynchronously, \
    has_request_variables, POST, json_to_list, to_non_negative_int, \
    JsonableError
from zephyr.lib.response import json_success, json_error

import os
import datetime
import simplejson
import socket
import time
import collections
import sys
import logging
import subprocess
from django.core.cache import cache
from zephyr.lib.cache import cache_with_key
from zephyr.lib.cache_helpers import cache_save_message, cache_get_message

SERVER_GENERATION = int(time.time())

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

    for um in UserMessage.objects.filter(message_id__gte=cache_minimum_id).order_by("message"):
        add_user_message(um.user_profile_id, um.message_id)

    streams = {}
    for stream in Stream.objects.select_related().all():
        streams[stream.id] = stream
    for m in (Message.objects.only("id", "recipient").select_related("recipient")
              .filter(id__gte=cache_minimum_id + (USERMESSAGE_CACHE_COUNT - STREAMMESSAGE_CACHE_COUNT),
                      recipient__type=Recipient.STREAM).order_by("id")):
        stream = streams[m.recipient.type_id]
        add_stream_message(stream.realm.id, stream.name, m.id)

    if not settings.DEPLOYED:
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

@internal_notify_view
def notify_new_message(request):
    recipient_profile_ids = map(int, json_to_list(request.POST['users']))
    message = cache_get_message(int(request.POST['message']))

    for user_profile_id in recipient_profile_ids:
        user_receive_message(user_profile_id, message)

    if 'stream_name' in request.POST:
        realm_id = int(request.POST['realm_id'])
        stream_name = request.POST['stream_name']
        stream_receive_message(realm_id, stream_name, message)

    return json_success()

@internal_notify_view
def notify_pointer_update(request):
    user_profile_id = int(request.POST['user'])
    new_pointer = int(request.POST['new_pointer'])

    update_pointer(user_profile_id, new_pointer)

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

    return ret

def return_messages_immediately(user_profile, client_id, last,
                                client_server_generation,
                                client_pointer, dont_block,
                                stream_name, **kwargs):
    update_types = []
    new_pointer = None
    if dont_block:
        update_types.append("nonblocking_request")

    if (client_server_generation is not None and
        client_server_generation != SERVER_GENERATION):
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
# notify_new_message. If a user makes a get_updates request for a
# nonexistent or non-public stream, they won't get an error -- they'll
# just never receive any messages.
@has_request_variables
def get_updates_backend(request, user_profile, handler, client_id,
                        last = POST(converter=to_non_negative_int, default=None),
                        client_server_generation = POST(whence='server_generation', default=None,
                                                        converter=int),
                        client_pointer = POST(whence='pointer', converter=int, default=None),
                        dont_block = POST(converter=simplejson.loads, default=False),
                        stream_name = POST(default=None), apply_markdown=True,
                        **kwargs):
    resp = return_messages_immediately(user_profile, client_id, last,
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

"""
Implements the per-domain data retention policy.

The goal is to have a single place where the policy is defined.  This is
complicated by needing to apply this policy both to the database and to log
files.  Additionally, we want to use an efficient query for the database,
rather than iterating through messages one by one.

The code in this module does not actually remove anything; it just identifies
which items should be kept or removed.
"""

import operator

from django.utils     import timezone
from django.db.models import Q
from datetime         import datetime, timedelta
from zephyr.models    import Realm, UserMessage, UserProfile

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
        domain = UserProfile.objects.get(user__email__iexact=user_email).realm.domain
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

import sys
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
        user = record.request.user
        user_info = "%s (%s)" % (user.userprofile.full_name, user.email)
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
        from zephyr.models import Recipient
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
            internal_send_message("humbug+errors@humbughq.com",
                    "stream", "devel", self.format_subject(subject),
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


from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import SetPasswordForm

from humbug import settings
from zephyr.models import Realm
from zephyr.lib.actions import do_change_password

def is_unique(value):
    try:
        User.objects.get(email__iexact=value)
        raise ValidationError(u'%s is already registered' % value)
    except User.DoesNotExist:
        pass

def is_inactive(value):
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

class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, max_length=100)
    terms = forms.BooleanField(required=True)

class ToSForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    terms = forms.BooleanField(required=True)

class HomepageForm(forms.Form):
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

from django.conf import settings

def add_settings(request):
    return {
        'full_navbar':   settings.FULL_NAVBAR,
    }

# Defer importing until later to avoid circular imports

def openid_failure_handler(request, message, status=403, template_name=None, exception=None):
    # We ignore template_name in this function

    from django_openid_auth.views import default_render_failure

    return default_render_failure(request, message, status=403, template_name="openid_error.html", exception=None)

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

from django.conf import settings
from decorator import RequestVariableMissingError, RequestVariableConversionError
from zephyr.lib.response import json_error
from django.db import connection

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

        # Get the amount of time spent doing database queries
        query_time = sum(float(query.get('time', 0)) for query in connection.queries)

        # Get the requestor's email address and client, if available.
        try:
            email = request._email
        except Exception:
            email = "unauth"
        try:
            client = request._client.name
        except Exception:
            client = "?"

        logger.info('%-15s %-7s %3d %.3fs (db: %.3fs/%sq) %s (%s via %s)'
            % (remote_ip, request.method, response.status_code,
               time_delta, query_time, len(connection.queries),
               request.get_full_path(), email, client))

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
from django.core.mail import send_mail, mail_admins
from zephyr.models import Message, UserProfile, Stream, Subscription, \
    Recipient, get_huddle, Realm, UserMessage, \
    PreregistrationUser, get_client, MitUser, User, UserActivity, \
    MAX_SUBJECT_LENGTH, MAX_MESSAGE_LENGTH, get_stream, UserPresence, \
    get_recipient, valid_stream_name
from zephyr.lib.actions import do_add_subscription, do_remove_subscription, \
    do_change_password, create_mit_user_if_needed, do_change_full_name, \
    do_change_enable_desktop_notifications, do_change_enter_sends, \
    do_activate_user, add_default_subs, do_create_user, check_send_message, \
    log_subscription_property_change, internal_send_message, \
    create_stream_if_needed, gather_subscriptions, subscribed_to_stream, \
    update_user_presence, set_stream_color, get_stream_colors, update_message_flags, \
    recipient_for_emails, extract_recipients
from zephyr.forms import RegistrationForm, HomepageForm, ToSForm, is_unique, \
    is_inactive, isnt_mit
from django.views.decorators.csrf import csrf_exempt

from zephyr.decorator import require_post, \
    authenticated_api_view, authenticated_json_post_view, \
    has_request_variables, POST, authenticated_json_view, \
    to_non_negative_int, json_to_dict, json_to_list, json_to_bool, \
    JsonableError, RequestVariableMissingError, get_user_profile_by_email, \
    get_user_profile_by_user_id
from zephyr.lib.query import last_n
from zephyr.lib.avatar import gravatar_hash
from zephyr.lib.response import json_success, json_error
from zephyr.lib.timestamp import timestamp_to_datetime, datetime_to_timestamp
from zephyr.lib.cache import cache_with_key

from confirmation.models import Confirmation

import datetime
import simplejson
import re
import urllib
import time
import requests
import os
import base64
from collections import defaultdict
from zephyr.lib import bugdown

SERVER_GENERATION = int(time.time())


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
        if len(stream_name) > 30:
            raise JsonableError("Stream name (%s) too long." % (stream_name,))
        if not valid_stream_name(stream_name):
            raise JsonableError("Invalid stream name (%s)." % (stream_name,))
        stream = get_stream(stream_name, user_profile.realm)

        if stream is None:
            rejects.append(stream_name)
        else:
            streams.append(stream)
            # Verify we can access the stream
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
            "%s <`%s`> just signed up for Humbug!%s(total: **%i**)" % (
                user_profile.full_name,
                user_profile.user.email,
                internal_blurb,
                UserProfile.objects.filter(realm=user_profile.realm,
                                           user__is_active=True).count(),
                )
            )

def notify_new_user(user_profile, internal=False):
    send_signup_message("humbug+signups@humbughq.com", "signups", user_profile, internal)

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

@require_post
def accounts_register(request):
    key = request.POST['key']
    confirmation = Confirmation.objects.get(confirmation_key=key)
    prereg_user = confirmation.content_object
    email = prereg_user.email
    mit_beta_user = isinstance(confirmation.content_object, MitUser)

    # If someone invited you, you are joining their realm regardless
    # of your e-mail address.
    #
    # MitUsers can't be referred and don't have a referred_by field.
    if not mit_beta_user and prereg_user.referred_by:
        domain = prereg_user.referred_by.realm.domain
    else:
        domain = email.split('@')[-1]

    try:
        if mit_beta_user:
            # MIT users already exist, but are supposed to be inactive.
            is_inactive(email)
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
                # We want to add the default subs list iff there were no subs
                # specified when the user was invited.
                streams = prereg_user.streams.all()
                if len(streams) == 0:
                    add_default_subs(user_profile)
                else:
                    for stream in streams:
                        do_add_subscription(user_profile, stream)
                if prereg_user.referred_by is not None:
                    # This is a cross-realm private message.
                    internal_send_message("humbug+signups@humbughq.com",
                            "private", prereg_user.referred_by.user.email, user_profile.realm.domain,
                            "%s <`%s`> accepted your invitation to join Humbug!" % (
                                user_profile.full_name,
                                user_profile.user.email,
                                )
                            )

            notify_new_user(user_profile)

            login(request, authenticate(username=email, password=password))
            return HttpResponseRedirect(reverse('zephyr.views.home'))

    return render_to_response('zephyr/register.html',
        { 'form': form, 'company_name': domain, 'email': email, 'key': key },
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

@authenticated_json_post_view
@has_request_variables
def json_invite_users(request, user_profile, invitee_emails=POST):
    # Validation
    if settings.ALLOW_REGISTER == False:
        try:
            isnt_mit(user_profile.user.email)
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

    new_prereg_users = []
    errors = []
    skipped = []
    for email in invitee_emails:
        if email == '':
            continue

        if not validators.email_re.match(email):
            errors.append((email, "Invalid address."))
            continue

        if user_profile.realm.restricted_to_domain and \
                email.split('@', 1)[-1] != user_profile.realm.domain:
            errors.append((email, "Outside your domain."))
            continue

        # Redundant check in case earlier validation preventing MIT users from
        # inviting people fails.
        if settings.ALLOW_REGISTER == False:
            try:
                isnt_mit(email)
            except ValidationError:
                errors.append((email, "Invitations are not enabled for MIT at this time."))
                continue

        try:
            is_unique(email)
        except ValidationError:
            skipped.append((email, "Already has an account."))
            continue

        # The logged in user is the referrer.
        user = PreregistrationUser(email=email, referred_by=user_profile)

        # We save twice because you cannot associate a ManyToMany field
        # on an unsaved object.
        user.save()
        user.streams = streams
        user.save()

        new_prereg_users.append(user)

    if errors:
        return json_error(data={'errors': errors},
                          msg="Some emails did not validate, so we didn't send any invitations.")

    if skipped and len(skipped) == len(invitee_emails):
        # All e-mails were skipped, so we didn't actually invite anyone.
        return json_error(data={'errors': skipped},
                          msg="We weren't able to invite anyone.")

    # If we encounter an exception at any point before now, there are no unwanted side-effects,
    # since it is totally fine to have duplicate PreregistrationUsers
    for user in new_prereg_users:
        Confirmation.objects.send_confirmation(user, user.email,
                additional_context={'referrer': user_profile},
                subject_template_path='confirmation/invite_email_subject.txt',
                body_template_path='confirmation/invite_email_body.txt')

    if skipped:
        return json_error(data={'errors': skipped},
                          msg="Some of those addresses are already using Humbug, \
so we didn't send them an invitation. We did send invitations to everyone else!")
    else:
        return json_success()

def login_page(request, **kwargs):
    template_response = django_login_page(request, **kwargs)
    try:
        template_response.context_data['email'] = request.GET['email']
    except KeyError:
        pass
    return template_response

@require_post
def logout_then_login(request, **kwargs):
    return django_logout_then_login(request, kwargs)

def accounts_home(request):
    if request.method == 'POST':
        form = HomepageForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = PreregistrationUser()
            user.email = email
            user.save()
            Confirmation.objects.send_confirmation(user, user.email)
            return HttpResponseRedirect(reverse('send_confirm', kwargs={'email':user.email}))
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

    user_profile = get_user_profile_by_user_id(request.user.id)

    num_messages = UserMessage.objects.filter(user_profile=user_profile).count()

    # Brand new users get the tutorial
    needs_tutorial = settings.TUTORIAL_ENABLED and user_profile.pointer == -1

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
              UserProfile.objects.select_related().filter(realm=user_profile.realm)]

    streams = simplejson.encoder.JSONEncoderForHTML().encode(gather_subscriptions(user_profile))

    js_bool = lambda x: 'true' if x else 'false'

    try:
        isnt_mit(user_profile.user.email)
        show_invites = True
    except ValidationError:
        show_invites = settings.ALLOW_REGISTER

    return render_to_response('zephyr/index.html',
                              {'user_profile': user_profile,
                               'email_hash'  : gravatar_hash(user_profile.user.email),
                               'people'      : people,
                               'streams'     : streams,
                               'poll_timeout': settings.POLL_TIMEOUT,
                               'debug'       : settings.DEBUG,
                               'have_initial_messages':
                                   js_bool(num_messages > 0),
                               'desktop_notifications_enabled':
                                   js_bool(user_profile.enable_desktop_notifications),
                               'enter_sends':
                                   js_bool(user_profile.enter_sends),
                               'show_debug':
                                   settings.DEBUG and ('show_debug' in request.GET),
                               'show_invites': show_invites,
                               'needs_tutorial': js_bool(needs_tutorial)
                               },
                              context_instance=RequestContext(request))

@authenticated_api_view
def api_update_pointer(request, user_profile):
    return update_pointer_backend(request, user_profile)

@authenticated_json_post_view
def json_update_pointer(request, user_profile):
    return update_pointer_backend(request, user_profile)

@has_request_variables
def update_pointer_backend(request, user_profile,
                           pointer=POST(converter=to_non_negative_int)):
    if pointer <= user_profile.pointer:
        return json_success()

    user_profile.pointer = pointer
    user_profile.save()

    if request._client.name.lower() in ['android', 'iphone']:
        # TODO (leo)
        # Until we handle the new read counts in the mobile apps natively,
        # this is a shim that will mark as read any messages up until the
        # pointer move
        UserMessage.objects.filter(user_profile=user_profile,
                                   message__id__lte=pointer,
                                   flags=~UserMessage.flags.read)        \
                           .update(flags=F('flags') | UserMessage.flags.read)

    if settings.TORNADO_SERVER:
        requests.post(settings.TORNADO_SERVER + '/notify_pointer_update', data=dict(
            secret          = settings.SHARED_SECRET,
            user            = user_profile.id,
            new_pointer     = pointer))

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

    def by_is(self, operand):
        if operand == 'private-message':
            return (Q(message__recipient__type=Recipient.PERSONAL) |
                    Q(message__recipient__type=Recipient.HUDDLE))
        raise BadNarrowOperator("unknown 'is' operand " + operand)

    def by_stream(self, operand):
        stream = get_stream(operand, self.user_profile.realm)
        if stream is None:
            raise BadNarrowOperator('unknown stream ' + operand)
        recipient = get_recipient(Recipient.STREAM, type_id=stream.id)
        return Q(message__recipient=recipient)

    def by_subject(self, operand):
        return Q(message__subject__iexact=operand)

    def by_sender(self, operand):
        return Q(message__sender__user__email__iexact=operand)

    def by_pm_with(self, operand):
        if ',' in operand:
            # Huddle
            try:
                emails = [e.strip() for e in operand.split(',')]
                recipient = recipient_for_emails(emails, False,
                    self.user_profile, self.user_profile)
            except ValidationError:
                raise BadNarrowOperator('unknown recipient ' + operand)
            return Q(message__recipient=recipient)
        else:
            # Personal message
            self_recipient = get_recipient(Recipient.PERSONAL, type_id=self.user_profile.id)
            if operand == self.user_profile.user.email:
                # Personals with self
                return Q(message__recipient__type=Recipient.PERSONAL,
                         message__sender=self.user_profile, message__recipient=self_recipient)

            # Personals with other user; include both directions.
            try:
                narrow_profile = get_user_profile_by_email(operand)
            except UserProfile.DoesNotExist:
                raise BadNarrowOperator('unknown user ' + operand)

            narrow_recipient = get_recipient(Recipient.PERSONAL, narrow_profile.id)
            return ((Q(message__sender=narrow_profile) & Q(message__recipient=self_recipient)) |
                    (Q(message__sender=self.user_profile) & Q(message__recipient=narrow_recipient)))

    def do_search(self, query, operand):
        if "postgres" in settings.DATABASES["default"]["ENGINE"]:
            sql = "search_tsvector @@ plainto_tsquery('pg_catalog.english', %s)"
            return query.extra(where=[sql], params=[operand])
        else:
            for word in operand.split():
                query = query.filter(Q(message__content__icontains=word) |
                                     Q(message__subject__icontains=word))
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

def get_public_stream(request, stream, realm):
    if not valid_stream_name(stream):
        raise JsonableError("Invalid stream name")
    stream = get_stream(stream, realm)
    if stream is None:
        raise JsonableError("Stream does not exist")
    if not stream.is_public():
        raise JsonableError("Stream is not public")
    return stream

@has_request_variables
def get_old_messages_backend(request, anchor = POST(converter=int),
                             num_before = POST(converter=to_non_negative_int),
                             num_after = POST(converter=to_non_negative_int),
                             narrow = POST('narrow', converter=narrow_parameter, default=None),
                             stream = POST(default=None),
                             user_profile=None, apply_markdown=True):
    if stream is not None:
        stream = get_public_stream(request, stream, user_profile.realm)
        recipient = get_recipient(Recipient.STREAM, stream.id)
        query = UserMessage.objects.select_related('message').filter(message__recipient=recipient,
                                                                     user_profile=user_profile) \
                                                    .order_by('id')
    else:
        query = UserMessage.objects.select_related().filter(user_profile=user_profile) \
                                                    .order_by('id')

    if narrow is not None:
        build = NarrowBuilder(user_profile)
        for operator, operand in narrow:
            query = build(query, operator, operand)

    # We add 1 to the number of messages requested to ensure that the
    # resulting list always contains the anchor message
    if num_before != 0 and num_after == 0:
        num_before += 1
        messages = last_n(num_before, query.filter(message__id__lte=anchor))
    elif num_before == 0 and num_after != 0:
        num_after += 1
        messages = query.filter(message__id__gte=anchor)[:num_after]
    else:
        num_after += 1
        messages = (last_n(num_before, query.filter(message__id__lt=anchor))
                    + list(query.filter(message__id__gte=anchor)[:num_after]))

    message_list = [dict(umessage.message.to_dict(apply_markdown),
                         **umessage.flags_dict())
                     for umessage in messages]
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
def json_update_flags(request, user_profile, messages=POST('messages', converter=json_to_list),
                                            operation=POST('op'),
                                            flag=POST('flag'),
                                            all=POST('all', converter=json_to_bool, default=False)):
    update_message_flags(user_profile, operation, flag, messages, all)
    return json_success({'result': 'success',
                         'msg': ''})

@authenticated_api_view
def api_send_message(request, user_profile):
    return send_message_backend(request, user_profile, request._client)

@authenticated_json_post_view
def json_send_message(request, user_profile):
    return send_message_backend(request, user_profile, request._client)

@authenticated_json_post_view
@has_request_variables
def json_change_enter_sends(request, user_profile, enter_sends=POST('enter_sends', json_to_bool)):
    do_change_enter_sends(user_profile, enter_sends)
    return json_success()

# Currently tabbott/extra@mit.edu is our only superuser.  TODO: Make
# this a real superuser security check.
def is_super_user_api(request):
    return request.POST.get("api-key") in ["xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"]

def mit_to_mit(user_profile, email):
    # Are the sender and recipient both @mit.edu addresses?
    # We have to handle this specially, inferring the domain from the
    # e-mail address, because the recipient may not existing in Humbug
    # and we may need to make a stub MIT user on the fly.
    if not validators.email_re.match(email):
        return False

    if user_profile.realm.domain != "mit.edu":
        return False

    domain = email.split("@", 1)[1]
    return user_profile.realm.domain == domain

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
def json_tutorial_send_message(request, user_profile,
                               message_type_name = POST('type'),
                               subject_name = POST('subject', lambda x: x.strip(), None),
                               message_content=POST('content')):
    """
    This function, used by the onboarding tutorial, causes the
    Tutorial Bot to send you the message you pass in here.
    (That way, the Tutorial Bot's messages to you get rendered
     by the server and therefore look like any other message.)
    """
    sender_name = "humbug+tutorial@humbughq.com"
    if message_type_name == 'private':
        # For now, we discard the recipient on PMs; the tutorial bot
        # can only send to you.
        internal_send_message(sender_name,
                              "private",
                              user_profile.user.email,
                              "",
                              message_content,
                              realm=user_profile.realm)
        return json_success()
    elif message_type_name == 'stream':
        tutorial_stream_name = 'tutorial-%s' % user_profile.user.email.split('@')[0]
        ## TODO: For open realms, we need to use the full name here,
        ## so that me@gmail.com and me@hotmail.com don't get the same stream.
        internal_send_message(sender_name,
                              "stream",
                              tutorial_stream_name,
                              subject_name,
                              message_content,
                              realm=user_profile.realm)
        return json_success()
    return json_error('Bad data passed in to tutorial_send_message')

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
    streams = sorted(stream.name for stream in
                     Stream.objects.filter(id__in = stream_ids,
                                           realm=user_profile.realm,
                                           invite_only=False))
    return json_success({"streams": streams})

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

    streams = list_to_streams(streams_raw, user_profile)

    result = dict(removed=[], not_subscribed=[])
    for stream in streams:
        did_remove = do_remove_subscription(user_profile, stream)
        if did_remove:
            result["removed"].append(stream.name)
        else:
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
                              streams_raw = POST('subscriptions', json_to_list),
                              invite_only = POST('invite_only', json_to_bool, default=False),
                              principals = POST('principals', json_to_list, default=None),):

    stream_names = []
    for stream_name in streams_raw:
        stream_name = stream_name.strip()
        if len(stream_name) > 30:
            return json_error("Stream name (%s) too long." % (stream_name,))
        if not valid_stream_name(stream_name):
            return json_error("Invalid stream name (%s)." % (stream_name,))
        stream_names.append(stream_name)

    if principals is not None:
        subscribers = set(principal_to_user_profile(user_profile, principal) for principal in principals)
    else:
        subscribers = [user_profile]

    streams = list_to_streams(streams_raw, user_profile, autocreate=True, invite_only=invite_only)
    private_streams = {}
    result = dict(subscribed=[], already_subscribed=[])

    result = dict(subscribed=defaultdict(list), already_subscribed=defaultdict(list))
    for stream in streams:
        for subscriber in subscribers:
            did_subscribe = do_add_subscription(subscriber, stream)
            if did_subscribe:
                result["subscribed"][subscriber.user.email].append(stream.name)
            else:
                result["already_subscribed"][subscriber.user.email].append(stream.name)
        private_streams[stream.name] = stream.invite_only

    # Inform the user if someone else subscribed them to stuff
    if principals and result["subscribed"]:
        for email, subscriptions in result["subscribed"].iteritems():
            if email == user_profile.user.email:
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
            internal_send_message("humbug+notifications@humbughq.com",
                                  "private", email, "", msg)

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
    members = [(profile.full_name, profile.user.email) for profile in \
                   UserProfile.objects.select_related().filter(realm=user_profile.realm)]
    return json_success({'members': members})

@authenticated_api_view
def api_get_subscribers(request, user_profile):
    return get_subscribers_backend(request, user_profile)

@authenticated_json_post_view
def json_get_subscribers(request, user_profile):
    return get_subscribers_backend(request, user_profile)

@has_request_variables
def get_subscribers_backend(request, user_profile, stream_name=POST('stream')):
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

    return json_success({'subscribers': [subscription.user_profile.user.email
                                         for subscription in subscriptions]})

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
        recipient = get_recipient(Recipient.STREAM, stream.id)
        result["subscribed"] = Subscription.objects.filter(user_profile=user_profile,
                                                           recipient=recipient,
                                                           active=True).exists()
    return json_success(result)

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

def set_in_home_view(user_profile, stream_name, value):
    subscription = get_subscription_or_die(stream_name, user_profile)[0]

    subscription.in_home_view = value
    subscription.save()

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
        try:
            return request_dict[property].strip()
        except KeyError:
            raise RequestVariableMissingError(property)

    def get_stream_colors(self, request, user_profile):
        return json_success({"stream_colors": get_stream_colors(user_profile)})

    def post_stream_colors(self, request, user_profile):
        stream_name = self.request_property(request.POST, "stream_name")
        color = self.request_property(request.POST, "color")

        set_stream_color(user_profile, stream_name, color)
        log_subscription_property_change(user_profile.user.email, "stream_color",
                                         {"stream_name": stream_name, "color": color})
        return json_success()

    def post_in_home_view(self, request, user_profile):
        stream_name = self.request_property(request.POST, "stream_name")
        value = self.request_property(request.POST, "in_home_view").lower()

        if value == "true":
            value = True
        elif value == "false":
            value = False
        else:
            raise JsonableError("Invalid value for `in_home_view`.")

        set_in_home_view(user_profile, stream_name, value)

        return json_success()

subscription_properties = SubscriptionProperties()

def make_property_call(request, query_dict, user_profile):
    try:
        property = query_dict["property"].strip()
    except KeyError:
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
                    client__name=client_name).select_related():
                row = self.rows.setdefault(record.user_profile.user.email, {})
                row['realm'] = record.user_profile.realm.domain
                row['full_name'] = record.user_profile.full_name
                row['email'] = record.user_profile.user.email
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
            'API':     ActivityTable('API',           api_queries),
            'Android': ActivityTable('Android',       api_queries),
            'iPhone':  ActivityTable('iPhone',        api_queries)
        }}, context_instance=RequestContext(request))

@authenticated_api_view
@has_request_variables
def api_github_landing(request, user_profile, event=POST,
                       payload=POST(converter=json_to_dict)):
    # TODO: this should all be moved to an external bot

    repository = payload['repository']

    # CUSTOMER18 has requested not to get pull request notifications
    if event == 'pull_request' and user_profile.realm.domain not in ['customer18.invalid', 'humbughq.com']:
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
        if short_ref != 'master' and user_profile.realm.domain in ['customer18.invalid', 'humbughq.com']:
            return json_success()

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

@cache_with_key(lambda user_profile: user_profile.realm_id, timeout=60)
def get_status_list(requesting_user_profile):
    def presence_to_dict(presence):
        if presence.status == UserPresence.ACTIVE:
            presence_val = 'active'
        elif presence.status == UserPresence.IDLE:
            presence_val = 'idle'
        else:
            raise JsonableError("Invalid presence value in db: %s" % (presence,))

        return {'status'   : presence_val,
                'timestamp': datetime_to_timestamp(presence.timestamp)}


    user_statuses = defaultdict(dict)

    # Return no status info for MIT
    if requesting_user_profile.realm.domain == 'mit.edu':
        return {'presences': user_statuses}

    for presence in UserPresence.objects.filter(
        user_profile__realm=requesting_user_profile.realm).select_related(
        'user_profile', 'user_profile__user', 'client'):

        user_statuses[presence.user_profile.user.email][presence.client.name] = \
            presence_to_dict(presence)

    return {'presences': user_statuses}

@authenticated_json_post_view
@has_request_variables
def json_update_active_status(request, user_profile,
                              status=POST):
    if status == 'active':
        status_val = UserPresence.ACTIVE
    elif status == 'idle':
        status_val = UserPresence.IDLE
    else:
        raise JsonableError("Invalid presence status: %s" % (status,))

    update_user_presence(user_profile, request._client, now(), status_val)

    ret = get_status_list(user_profile)
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

    return json_success(ret)

@authenticated_json_post_view
def json_get_active_statuses(request, user_profile):
    return json_success(get_status_list(user_profile))

@authenticated_json_post_view
@has_request_variables
def json_report_error(request, user_profile, message=POST, stacktrace=POST,
                      user_agent=POST):
    mail_admins("Browser error for %s" % (user_profile.user.email,),
                "Message:\n%s\n\nStacktrace:\n%s\n\nUser agent:\n%s"
                % (message, stacktrace, user_agent))
    return json_success()

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Stream.invite_only'
        db.add_column('zephyr_stream', 'invite_only',
                      self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Stream.invite_only'
        db.delete_column('zephyr_stream', 'invite_only')


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
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings

class Migration(SchemaMigration):

    def forwards(self, orm):
        # This schema migration is only for use in automated migrations.  To
        # deploy on the production database (the migration only needs to be
        # done once for both of staging and prod because they share a
        # database), you should instead execute the following SQL manually:
        #
        # $ ssh postgres.humbughq.com
        # $ psql
        # humbug=> CREATE INDEX CONCURRENTLY zephyr_message_search_tsvector ON zephyr_message USING gin(search_tsvector);
        #
        # Note the addition of the "CONCURRENTLY" keyword.  The problem is that
        # creating the index takes non-trivial time and requires a write lock
        # on the table while the index is being created.  This would mean that
        # users would be unable to send messages while we were generating the
        # index, which isn't acceptable.  We can't create the index
        # concurrently in the South migration because concurrent index
        # creations can't happen inside of a transaction and South forces a
        # transaction on migration functions.
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return
        if len(db.execute("""SELECT relname FROM pg_class
                             WHERE relname = 'zephyr_message_search_tsvector'""")) != 0:
            print "Not creating index because it already exists"
        else:
            db.execute("""CREATE INDEX zephyr_message_search_tsvector ON zephyr_message
                          USING gin(search_tsvector)""")

    def backwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return
        db.execute("DROP INDEX zephyr_message_search_tsvector")

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

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'PreregistrationUser', fields ['email']
        db.delete_unique('zephyr_preregistrationuser', ['email'])

        # Adding field 'PreregistrationUser.referred_by'
        db.add_column('zephyr_preregistrationuser', 'referred_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'], null=True),
                      keep_default=False)

        # Adding field 'PreregistrationUser.invited_at'
        db.add_column('zephyr_preregistrationuser', 'invited_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.datetime(1969, 12, 31, 0, 0), blank=True),
                      keep_default=False)

        # Adding M2M table for field streams on 'PreregistrationUser'
        db.create_table('zephyr_preregistrationuser_streams', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('preregistrationuser', models.ForeignKey(orm['zephyr.preregistrationuser'], null=False)),
            ('stream', models.ForeignKey(orm['zephyr.stream'], null=False))
        ))
        db.create_unique('zephyr_preregistrationuser_streams', ['preregistrationuser_id', 'stream_id'])


    def backwards(self, orm):
        # Deleting field 'PreregistrationUser.referred_by'
        db.delete_column('zephyr_preregistrationuser', 'referred_by_id')

        # Deleting field 'PreregistrationUser.invited_at'
        db.delete_column('zephyr_preregistrationuser', 'invited_at')

        # Removing M2M table for field streams on 'PreregistrationUser'
        db.delete_table('zephyr_preregistrationuser_streams')

        # Adding unique constraint on 'PreregistrationUser', fields ['email']
        db.create_unique('zephyr_preregistrationuser', ['email'])


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

# -*- coding: utf-8 -*-
import datetime
import logging

from south.db import db
from south.v2 import DataMigration
from django.db import models, transaction, connection
from django.conf import settings

from zephyr.lib import utils

class Migration(DataMigration):

    def forwards(self, orm):
        # Mark all messages not sent by this user, but past her saved pointer,
        # as unread.
        for user_profile in orm.UserProfile.objects.all().order_by("realm__id"):
            pointer = user_profile.pointer
            if pointer == -1:
                try:
                    pointer = (orm.UserMessage.objects.filter(user_profile=user_profile)
                                                      .order_by('message')
                                                      .reverse()[0]).message_id
                except IndexError:
                    pass

            # We have to use the `long` representation of the unread bit,
            # as we don't have access to BitHandler or BitFields here.
            #
            # 'read' is the first bit in flags
            msgs = [m.id for m in orm.UserMessage.objects.filter(user_profile=user_profile,
                                                                 message_id__lte=pointer)
                                                         .exclude(flags=1)]

            def update_batch(batch):
                with transaction.commit_on_success():
                    orm.UserMessage.objects.filter(id__in=batch) \
                                           .update(flags=1)

            logging.info("Starting to migrate %s" % (user_profile.user.email))
            # Batch in set of 5000
            utils.run_in_batches(msgs, 250, update_batch, sleep_time=3,
                                                           logger=logging.info)

    def backwards(self, orm):
        "Write your backwards methods here."
        # Nothing to do, flags field is dropped in schema migration

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
        # Adding field 'UserProfile.enter_sends'
        db.add_column('zephyr_userprofile', 'enter_sends',
                      self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'UserProfile.enter_sends'
        db.delete_column('zephyr_userprofile', 'enter_sends')


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
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['zephyr']
# -*- coding: utf-8 -*-
import datetime
import logging
from south.db import db
from south.v2 import SchemaMigration
from django.db import models, transaction, connection
from django.conf import settings

from zephyr.lib import utils

class Migration(SchemaMigration):

    def forwards(self, orm):

        if "postgres" in settings.DATABASES["default"]["ENGINE"]:
            cursor = connection.cursor()
            cursor.execute("ALTER TABLE zephyr_usermessage ADD COLUMN flags bigint;")
            cursor.execute("""
    CREATE FUNCTION set_flags_trigger() RETURNS TRIGGER AS $set_flags_trigger$
        BEGIN
            NEW.flags := 0;
            RETURN NEW;
        END;
    $set_flags_trigger$ LANGUAGE plpgsql;

    CREATE TRIGGER set_flags_trigger BEFORE INSERT ON zephyr_usermessage
        FOR EACH ROW EXECUTE PROCEDURE set_flags_trigger();
    """)
            transaction.commit_unless_managed()

            for user_profile in orm.UserProfile.objects.all():
                msgs = [m.id for m in orm.UserMessage.objects.filter(user_profile=user_profile).order_by('id')]

                def update_batch(batch):
                    with transaction.commit_on_success():
                        orm.UserMessage.objects.filter(id__in=batch) \
                                               .update(flags=0)
                # Batch in set of 5000
                utils.run_in_batches(msgs, 250, update_batch, sleep_time=3,
                                                               logger=logging.info)

            cursor.execute("ALTER TABLE zephyr_usermessage ALTER COLUMN flags SET NOT NULL;")
            cursor.execute("ALTER TABLE zephyr_usermessage ALTER COLUMN flags SET DEFAULT 0;")
            cursor.execute("DROP TRIGGER set_flags_trigger ON zephyr_usermessage;")
            cursor.execute("DROP FUNCTION set_flags_trigger();")
            transaction.commit_unless_managed()
        else:
            db.add_column('zephyr_usermessage', 'flags',
                          self.gf('django.db.models.fields.BigIntegerField')(default=0),
                          keep_default=True)




    def backwards(self, orm):
        # Deleting field 'UserMessage.flags'
        db.delete_column('zephyr_usermessage', 'flags')


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

    idx_name = "zephyr_message_full_text_idx";
    def forwards(self, orm):
        # This schema migration is only for use in automated migrations.  To
        # deploy on the production database (the migration only needs to be
        # done once for both of staging and prod because they share a
        # database), you should instead execute the following SQL manually:
        #
        # $ ssh postgres.humbughq.com
        # $ psql
        # humbug=> CREATE INDEX CONCURRENTLY zephyr_message_full_text_idx ON zephyr_message USING gin(to_tsvector('english', subject || ' ' || content));
        #
        # Note the addition of the "CONCURRENTLY" keyword.  The problem is that
        # creating the index takes non-trivial time and requires a write lock
        # on the table while the index is being created.  This would mean that
        # users would be unable to send messages while we were generating the
        # index, which isn't acceptable.  We can't create the index
        # concurrently in the South migration because concurrent index
        # creations can't happen inside of a transaction and South forces a
        # transaction on migration functions.
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return
        if len(db.execute("SELECT relname FROM pg_class WHERE relname = %s",
                          params=[self.idx_name])) != 0:
            print "Not creating index '%s' because it already exists" % (self.idx_name,)
        else:
            db.execute("CREATE INDEX %s ON zephyr_message USING "
                       "gin(to_tsvector('english', subject || ' ' || content));"
                       % (self.idx_name,))

    def backwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return
        db.execute("DROP INDEX %s" % (self.idx_name,))

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

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserPresence'
        db.create_table('zephyr_userpresence', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.UserProfile'])),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zephyr.Client'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal('zephyr', ['UserPresence'])

        # Adding unique constraint on 'UserPresence', fields ['user_profile', 'client']
        db.create_unique('zephyr_userpresence', ['user_profile_id', 'client_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'UserPresence', fields ['user_profile', 'client']
        db.delete_unique('zephyr_userpresence', ['user_profile_id', 'client_id'])

        # Deleting model 'UserPresence'
        db.delete_table('zephyr_userpresence')


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
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Subscription.in_home_view'
        db.add_column('zephyr_subscription', 'in_home_view',
                      self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Subscription.in_home_view'
        db.delete_column('zephyr_subscription', 'in_home_view')


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

        db.execute("ALTER TABLE zephyr_message ADD COLUMN search_tsvector tsvector")

        # Create a temporary trigger to update new message rows while
        # we set search_tsvector on existing rows
        db.execute("""CREATE TRIGGER zephyr_message_update_search_tsvector_tmp
                      BEFORE INSERT ON zephyr_message FOR EACH ROW
                      EXECUTE PROCEDURE tsvector_update_trigger(search_tsvector,
                      'pg_catalog.english', subject, content)""");

    def backwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return

        db.execute("DROP TRIGGER zephyr_message_update_search_tsvector_tmp ON zephyr_message")
        db.execute("ALTER TABLE zephyr_message DROP COLUMN search_tsvector")

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

# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Realm.restricted_to_domain'
        db.add_column('zephyr_realm', 'restricted_to_domain',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Realm.restricted_to_domain'
        db.delete_column('zephyr_realm', 'restricted_to_domain')


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
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Message.rendered_content'
        db.add_column('zephyr_message', 'rendered_content',
                      self.gf('django.db.models.fields.TextField')(null=True),
                      keep_default=False)

        # Adding field 'Message.rendered_content_version'
        db.add_column('zephyr_message', 'rendered_content_version',
                      self.gf('django.db.models.fields.IntegerField')(null=True),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'Message.rendered_content'
        db.delete_column('zephyr_message', 'rendered_content')

        # Deleting field 'Message.rendered_content_version'
        db.delete_column('zephyr_message', 'rendered_content_version')


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
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
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

        (min_id, max_id) = db.execute("""SELECT MIN(id), MAX(id) FROM zephyr_message
                                         WHERE search_tsvector IS NULL""")[0]
        if min_id is not None:
            self.set_search_tsvector(min_id, max_id)

        db.execute("""CREATE TRIGGER zephyr_message_update_search_tsvector
                      BEFORE INSERT OR UPDATE ON zephyr_message FOR EACH ROW
                      EXECUTE PROCEDURE tsvector_update_trigger(search_tsvector,
                      'pg_catalog.english', subject, content)""");
        db.execute("DROP TRIGGER zephyr_message_update_search_tsvector_tmp ON zephyr_message")

    def set_search_tsvector(self, min_id, max_id):
        lower_bound = min_id
        batch_size = 100
        for upper_bound in xrange(min_id + batch_size, max_id + batch_size, batch_size):
            db.start_transaction()
            db.execute("""UPDATE zephyr_message SET
                              search_tsvector=to_tsvector('pg_catalog.english', subject || ' ' || content)
                              WHERE id >= %s AND id < %s AND search_tsvector IS NULL""",
                       params=[lower_bound, upper_bound])
            db.commit_transaction()
            lower_bound = upper_bound
            time.sleep(1)

    def backwards(self, orm):
        if "postgres" not in settings.DATABASES["default"]["ENGINE"]:
            return

        db.execute("""CREATE TRIGGER zephyr_message_update_search_tsvector_tmp
                      BEFORE INSERT ON zephyr_message FOR EACH ROW
                      EXECUTE PROCEDURE tsvector_update_trigger(search_tsvector,
                      'pg_catalog.english', subject, content)""");
        db.execute("DROP TRIGGER zephyr_message_update_search_tsvector ON zephyr_message")

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
    symmetrical = True


from optparse import make_option
import logging
import sys

from django.core.management.base import BaseCommand

from zephyr.lib.actions import do_deactivate, user_sessions
from zephyr.lib import utils
from zephyr.models import UserMessage, UserProfile
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

        user_profile = UserProfile.objects.get(user__email=email)

        if not all_until:
            message_ids = [mid.strip() for mid in sys.stdin.read().split(',')]
            mids = [m.id for m in UserMessage.objects.filter(user_profile=user_profile,
                                                             message__id__in=message_ids)
                                                     .order_by('-id')]
        else:
            mids = [m.id for m in UserMessage.objects.filter(user_profile=user_profile,
                                                             id__lte=all_until)
                                                      .order_by('-id')]
        if options["for_real"]:
            sys.stdin.close()
            sys.stdout.close()
            sys.stderr.close()

        def do_update(batch):
            with transaction.commit_on_success():
                msgs = UserMessage.objects.filter(id__in=batch)
                if op == 'add':
                    msgs.update(flags=models.F('flags') | flag)
                elif op == 'remove':
                    msgs.update(flags=models.F('flags') & ~flag)

        if not options["for_real"]:
            logging.info("Updating %s by %s %s" % (mids, op, flag))
            logging.info("Dry run completed. Run with --for-real to change message flags.")
            exit(1)

        utils.run_in_batches(mids, 400, do_update, sleep_time=3)
        exit(0)

import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.core import validators

from zephyr.models import Realm
from zephyr.lib.actions import do_create_user
from zephyr.views import notify_new_user
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
            user_profiles = UserProfile.objects.filter(realm=realm, user__is_active=True)
            print "%d users" % (len(user_profiles),)
            print "%d streams" % (len(Stream.objects.filter(realm=realm)),)

            for user_profile in user_profiles:
                print "%35s" % (user_profile.user.email,),
                for week in range(10):
                    print "%5d" % (self.messages_sent_by(user_profile, week)),
                print ""

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


from optparse import make_option

from django.core.management.base import BaseCommand
from django.db.models import Count
from zephyr.models import Realm, StreamColor, Stream, UserProfile, Subscription, \
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
        users_who_need_colors = filter(lambda profile: StreamColor.objects.filter(
                subscription__user_profile=profile).count() == 0, user_profiles)

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

                StreamColor(subscription=subscription, color=color).save()

from django.core.management.base import BaseCommand
from zephyr.models import StreamColor, UserProfile, Subscription, Recipient

class Command(BaseCommand):
    help = """Reset all colors for a person to the default grey"""

    def handle(self, *args, **options):
        if not args:
            self.print_help("python manage.py", "reset_colors")
            exit(1)

        for email in args:
            user_profile = UserProfile.objects.get(user__email__iexact=email)
            subs = Subscription.objects.filter(user_profile=user_profile,
                                               active=True,
                                               recipient__type=Recipient.STREAM)

            for sub in subs:
                stream_color, _ = StreamColor.objects.get_or_create(subscription=sub)
                stream_color.color = StreamColor.DEFAULT_STREAM_COLOR
                stream_color.save()

from django.core.management.base import BaseCommand

from zephyr.lib.actions import do_change_user_email
from zephyr.models import User

class Command(BaseCommand):
    help = """Change the email address for a user.

Usage: python manage.py change_user_email <old email> <new email>"""

    def handle(self, *args, **options):
        if len(args) != 2:
            print "Please provide both the old and new address."
            exit(1)

        old_email, new_email = args
        try:
            user = User.objects.get(email__iexact=old_email)
        except User.DoesNotExist:
            print "Old e-mail doesn't exist in the system."
            exit(1)

        do_change_user_email(user, new_email)

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

from zephyr.models import UserProfile
from zephyr.lib.actions import compute_mit_user_fullname

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

from django.core.management.base import BaseCommand
from zephyr.models import UserProfile, Subscription, Recipient, Message, Stream
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

        tutorial_bot = UserProfile.objects.get(user__email="humbug+tutorial@humbughq.com")

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
                        tutorial_user.save()

        if options["for_real"]:
            print "Subscriptions deactivated."
        else:
            print "This was a dry run. Pass -f to actually deactivate."

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.lib.cache_helpers import fill_memcached_caches

class Command(BaseCommand):
    option_list = BaseCommand.option_list
    help = "Populate the memcached cache of messages."

    def handle(self, *args, **options):
        fill_memcached_caches()

from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from zephyr.lib.actions import do_deactivate, user_sessions
from zephyr.models import UserProfile

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
        user = User.objects.get(email__iexact=args[0])
        user_profile = UserProfile.objects.get(user=user)

        sessions = user_sessions(user)
        print "Deactivating %s (%s) - %s" % (user_profile.full_name, user.email,
                                             user_profile.realm.domain)
        print "%s has the following active sessions:" % (user.email,)
        for session in sessions:
            print session.expire_date, session.get_decoded()
        print ""

        if not options["for_real"]:
            print "This was a dry run. Pass -f to actually deactivate."
            exit(1)

        do_deactivate(user_profile)
        print "Sessions deleted, user deactivated."

from optparse import make_option

from django.core.management.base import BaseCommand

from zephyr.lib.actions import do_remove_subscription
from zephyr.models import Realm, User, UserProfile, get_stream

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
                user_profiles.append(UserProfile.objects.get(
                        user=User.objects.get(email__iexact=email)))

        for user_profile in user_profiles:
            did_remove = do_remove_subscription(user_profile, stream)
            print "%s %s from %s" % (
                "Removed" if did_remove else "Couldn't remove",
                user_profile.user.email, stream_name)

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
from zephyr.lib.debug import interactive_debug_listen
from zephyr.lib.response import json_response

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
        interactive_debug_listen()

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

                                               ], debug=django.conf.settings.DEBUG,
                                              # Disable Tornado's own request logging, since we have our own
                                              log_function=lambda x: None)

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
        return self.finish(django_response.content)

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import Realm, UserProfile, Message, UserMessage
from zephyr.lib.timestamp import datetime_to_timestamp, timestamp_to_datetime
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
from zephyr.lib.actions import do_create_realm

class Command(BaseCommand):
    help = "Create a realm for the specified domain(s)."

    def handle(self, *args, **options):
        for domain in args:
            realm, created = do_create_realm(domain)
            if created:
                print domain + ": Created."
            else:
                print domain + ": Already exists."


from optparse import make_option
from django.core.management.base import BaseCommand
import simplejson
import pika
from zephyr.lib.actions import process_user_activity_event, \
        process_user_presence_event, process_update_message_flags
from zephyr.lib.queue import SimpleQueueClient
import sys
import signal

class Command(BaseCommand):
    option_list = BaseCommand.option_list
    help = "Process UserActivity log messages."

    def handle(self, *args, **options):
        activity_queue = SimpleQueueClient()

        def callback_activity(ch, method, properties, event):
            print " [x] Received activity %r" % (event,)
            msg_type = event['type']
            if msg_type == 'user_activity':
                process_user_activity_event(event)
            elif msg_type == 'user_presence':
                process_user_presence_event(event)
            elif msg_type == 'update_message':
                process_update_message_flags(event)
            else:
                print("[*] Unknown message type: %s" (msg_type,))

        def signal_handler(signal, frame):
            print("[*] Closing and disconnecting from queues")
            activity_queue.stop_consuming()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        print ' [*] Waiting for messages. To exit press CTRL+C'
        activity_queue.register_json_consumer('user_activity', callback_activity)
        activity_queue.start_consuming()

from optparse import make_option

from django.core.management.base import BaseCommand

from zephyr.lib.actions import create_stream_if_needed, do_add_subscription
from zephyr.models import Realm, User, UserProfile

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
                user_profiles.append(UserProfile.objects.get(
                        user=User.objects.get(email__iexact=email)))

        for stream_name in set(stream_names):
            for user_profile in user_profiles:
                stream, _ = create_stream_if_needed(user_profile.realm, stream_name)
                did_subscribe = do_add_subscription(user_profile, stream)
                print "%s %s to %s" % (
                    "Subscribed" if did_subscribe else "Already subscribed",
                    user_profile.user.email, stream_name)

from optparse import make_option
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from confirmation.models import Confirmation
from zephyr.models import User, PreregistrationUser

class Command(BaseCommand):
    help = "Generate activation links for users and print them to stdout."

    def handle(self, *args, **options):
        duplicates = False
        for email in args:
            try:
                User.objects.get(email=email)
                print email + ": There is already a user registered with that address."
                duplicates = True
                continue
            except User.DoesNotExist:
                pass

        if duplicates:
            return

        for email in args:
            prereg_user, created = PreregistrationUser.objects.get_or_create(email=email)
            print email + ": " + Confirmation.objects.get_link_for_object(prereg_user)


from django.core.management.base import BaseCommand
from django.utils.timezone import utc, now

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from zephyr.models import Message, UserProfile, Stream, Recipient, Client, \
    Subscription, Huddle, get_huddle, Realm, UserMessage, StreamColor, \
    get_huddle_hash, clear_database, get_client
from zephyr.lib.actions import get_user_profile_by_id, \
    do_send_message, set_default_streams, do_activate_user
from zephyr.lib.parallel import run_parallel
from django.db import transaction, connection
from django.conf import settings
from zephyr.lib.bulk_create import batch_bulk_create, bulk_create_realms, \
    bulk_create_streams, bulk_create_users, bulk_create_huddles, \
    bulk_create_clients
from zephyr.lib.timestamp import timestamp_to_datetime
from zephyr.models import MAX_MESSAGE_LENGTH

import simplejson
import datetime
import random
import glob
import sys
import os
from os import path
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
                ("Humbug Notification Bot", "humbug+notifications@humbughq.com"),
                ("Humbug Tutorial Bot", "humbug+tutorial@humbughq.com"),
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

            # Mark all messages as read
            with transaction.commit_on_success():
                UserMessage.objects.all().update(flags=0)

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
    email_set = set([u.email for u in User.objects.all()])
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
            user_profile = UserProfile.objects.get(user__email__iexact=old_message["user"])
            user_profile.full_name = old_message["full_name"]
            user_profile.save()
            continue
        elif message_type == "enable_desktop_notifications_changed":
            # Just handle these the slow way
            user_profile = UserProfile.objects.get(user__email__iexact=old_message["user"])
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

from optparse import make_option
import logging

from django.core.management.base import BaseCommand

from zephyr.lib.actions import do_deactivate, user_sessions
from zephyr.lib import utils
from zephyr.models import UserMessage, UserProfile
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
            users = [UserProfile.objects.get(user__email__iexact=args[0])]


        for user_profile in users:
            pointer = user_profile.pointer
            msgs = UserMessage.objects.filter(user_profile=user_profile,
                                              flags=~UserMessage.flags.read,
                                              message__id__lte=pointer)
            if not options["for_real"]:
                for msg in msgs:
                    print "Adding read flag to msg: %s - %s/%s (own msg: %s)"   \
                            % (user_profile.user.email,
                               msg.message.id,
                               msg.id,
                               msg.message.sender.user.email == user_profile.user.email)
            else:
                def do_update(batch):
                    with transaction.commit_on_success():
                        UserMessage.objects.filter(id__in=batch).update(flags=models.F('flags') | UserMessage.flags.read)

                mids = [m.id for m in msgs]
                utils.run_in_batches(mids, 250, do_update, 3, logging.info)

        if not options["for_real"]:
            print "Dry run completed. Run with --for-real to change message flags."
            exit(1)

        print "User messages updated."

import datetime
import pytz

from django.core.management.base import BaseCommand
from zephyr.models import UserProfile, Realm, Stream, Message, Recipient, StreamColor

class Command(BaseCommand):
    help = "Generate statistics on realm activity."

    def messages_sent_by(self, user, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return Message.objects.filter(sender=user, pub_date__gt=sent_time_cutoff).count()

    def stream_messages(self, realm, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return Message.objects.filter(sender__realm=realm, pub_date__gt=sent_time_cutoff,
                                      recipient__type=Recipient.STREAM).count()

    def private_messages(self, realm, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return Message.objects.filter(sender__realm=realm, pub_date__gt=sent_time_cutoff).exclude(
            recipient__type=Recipient.STREAM).exclude(recipient__type=Recipient.HUDDLE).count()

    def group_private_messages(self, realm, days_ago):
        sent_time_cutoff = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=days_ago)
        return Message.objects.filter(sender__realm=realm, pub_date__gt=sent_time_cutoff).exclude(
            recipient__type=Recipient.STREAM).exclude(recipient__type=Recipient.PERSONAL).count()

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
            user_profiles = UserProfile.objects.filter(realm=realm)
            print "%d users" % (len(user_profiles),)
            print "%d streams" % (Stream.objects.filter(realm=realm).count(),)

            for days_ago in (1, 7, 30):
                print "In last %d days, users sent:" % (days_ago,)
                sender_quantities = [self.messages_sent_by(user, days_ago) for user in user_profiles]
                for quantity in sorted(sender_quantities, reverse=True):
                    print quantity,
                print ""

                print "%d stream messages" % (self.stream_messages(realm, days_ago),)
                print "%d one-on-one private messages" % (self.private_messages(realm, days_ago),)
                print "%d group private messages" % (self.group_private_messages(realm, days_ago),)
            print "%.2f%% have desktop notifications enabled" % (float(len(user_profiles.filter(
                            enable_desktop_notifications=True))) * 100 /len(user_profiles),)
            colorizers = 0
            for profile in user_profiles:
                if StreamColor.objects.filter(subscription__user_profile=profile).count() > 0:
                    colorizers += 1
            print "%.2f%% have colorized streams" % (float(colorizers) * 100/len(user_profiles),)
            all_message_count = Message.objects.filter(sender__realm=realm).count()
            multi_paragraph_message_count = Message.objects.filter(sender__realm=realm,
                                                                   content__contains="\n\n").count()
            print "%.2f%% of all messages are multi-paragraph" % (
                float(multi_paragraph_message_count) * 100 / all_message_count)
            print ""

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
            except KeyboardInterrupt:
                raise
            except:
                print >>sys.stderr, 'WARNING: Could not expunge from', infile
                traceback.print_exc()

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import Realm, UserProfile, Recipient, Message, get_client
import simplejson
from zephyr.lib.timestamp import datetime_to_timestamp, timestamp_to_datetime
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
        mit_query = mit_query.exclude(sender__user__email__startswith=(bot_sender_start))
    # Filtering for "/" covers tabbott/extra@ and all the daemon/foo bots.
    mit_query = mit_query.exclude(sender__user__email__contains=("/"))
    mit_query = mit_query.exclude(sender__user__email__contains=("aim.com"))
    mit_query = mit_query.exclude(
        sender__user__email__in=["rss@mit.edu", "bash@mit.edu", "apache@mit.edu",
                                 "bitcoin@mit.edu", "lp@mit.edu", "clocks@mit.edu",
                                 "root@mit.edu", "nagios@mit.edu",
                                 "www-data|local-realm@mit.edu"])
    user_counts = {}
    for m in mit_query.select_related("sending_client", "sender", "sender__user"):
        email = m.sender.user.email
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

from optparse import make_option
from django.core.management.base import BaseCommand
from zephyr.models import Realm, UserProfile, UserActivity, get_client
import simplejson
from zephyr.lib.timestamp import datetime_to_timestamp, timestamp_to_datetime

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
        user_profile = UserProfile.objects.get(user__email__iexact=email)
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

from django.conf import settings
import pika
import logging
import simplejson
import random

# This simple queuing library doesn't expose much of the power of
# rabbitmq/pika's queuing system; its purpose is to just provide an
# interface for external files to put things into queues and take them
# out from bots without having to import pika code all over our codebase.
class SimpleQueueClient(object):
    def __init__(self):
        self.log = logging.getLogger('humbug.queue')
        self.queues = set()
        self.channel = None
        self._connect()

    def _connect(self):
        self.connection = pika.BlockingConnection(self._get_parameters())
        self.channel    = self.connection.channel()
        self.log.info('SimpleQueueClient connected')

    def _get_parameters(self):
        return pika.ConnectionParameters('localhost',
            credentials = pika.PlainCredentials(
                'humbug', settings.RABBITMQ_PASSWORD))

    def _generate_ctag(self, queue_name):
        return "%s_%s" % (queue_name, str(random.getrandbits(16)))

    def ready(self):
        return self.channel is not None

    def create_queue(self, queue_name):
        # Initialize the queues we need
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.queues.add(queue_name)

    def publish(self, queue_name, body):
        if queue_name not in self.queues:
            self.create_queue(queue_name)
        self.channel.basic_publish(exchange='',
                                   routing_key=queue_name,
                                   properties=pika.BasicProperties(delivery_mode = 2,),
                                   body=body)

    def json_publish(self, queue_name, body):
        return self.publish(queue_name, simplejson.dumps(body))

    def register_consumer(self, queue_name, callback):
        if queue_name not in self.queues:
            self.create_queue(queue_name)

        def wrapped_callback(ch, method, properties, body):
            callback(ch, method, properties, body)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(wrapped_callback, queue=queue_name,
            consumer_tag=self._generate_ctag(queue_name))

    def register_json_consumer(self, queue_name, callback):
        def wrapped_callback(ch, method, properties, body):
            return callback(ch, method, properties, simplejson.loads(body))
        return self.register_consumer(queue_name, wrapped_callback)

    def start_consuming(self):
        self.channel.start_consuming()

    def stop_consuming(self):
        self.channel.stop_consuming()

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import UserManager
from django.utils import timezone
from zephyr.models import UserProfile
import base64
import hashlib

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

def last_n(n, query_set):
    """Get the last n results from a Django QuerySet, in a semi-efficient way.
       Returns a list."""

    # We don't use reversed() because we would get a generator,
    # which causes bool(last_n(...)) to be True always.

    xs = list(query_set.reverse()[:n])
    xs.reverse()
    return xs

# This file needs to be different from cache.py because cache.py
# cannot import anything from zephyr.models or we'd have an import
# loop
from zephyr.models import Message, UserProfile
from zephyr.lib.cache import cache_with_key, djcache, message_cache_key, \
    user_profile_by_email_cache_key, user_profile_by_user_cache_key, \
    user_by_id_cache_key, user_profile_by_id_cache_key

MESSAGE_CACHE_SIZE = 25000

def cache_save_message(message):
    djcache.set(message_cache_key(message.id), (message,), timeout=3600*24)

@cache_with_key(message_cache_key)
def cache_get_message(message_id):
    return Message.objects.select_related().get(id=message_id)

# Called on Tornado startup to ensure our message cache isn't empty
def populate_message_cache():
    items_for_memcached = {}
    BATCH_SIZE = 1000
    count = 0
    for m in Message.objects.select_related().all().order_by("-id")[0:MESSAGE_CACHE_SIZE]:
        items_for_memcached[message_cache_key(m.id)] = (m,)
        count += 1
        if (count % BATCH_SIZE == 0):
            djcache.set_many(items_for_memcached, timeout=3600*24)
            items_for_memcached = {}

    djcache.set_many(items_for_memcached, timeout=3600*24)

# Fill our various caches of User/UserProfile objects used by Tornado
def populate_user_cache():
    items_for_memcached = {}
    for user_profile in UserProfile.objects.select_related().all():
        items_for_memcached[user_profile_by_email_cache_key(user_profile.user.email)] = (user_profile,)
        items_for_memcached[user_profile_by_user_cache_key(user_profile.user.id)] = (user_profile,)
        items_for_memcached[user_by_id_cache_key(user_profile.user.id)] = (user_profile.user,)
        items_for_memcached[user_profile_by_id_cache_key(user_profile.id)] = (user_profile,)

    djcache.set_many(items_for_memcached, timeout=3600*24*7)

def fill_memcached_caches():
    populate_user_cache()
    populate_message_cache()

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
            self.exn    = None

            # Don't block the whole program from exiting
            # if this is the only thread left.
            self.daemon = True

        def run(self):
            try:
                self.result = func(*args, **kwargs)
            except BaseException, e:
                self.exn = e

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
        # http://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python
        #
        # We need to retry, because an async exception received while the
        # thread is in a system call is simply ignored.
        for i in xrange(10):
            thread.raise_async_timeout()
            time.sleep(0.1)
            if not thread.isAlive():
                break
        raise TimeoutExpired

    if thread.exn:
        raise thread.exn
    return thread.result

from functools import wraps
import hashlib

from django.core.cache import cache as djcache
from django.core.cache import get_cache

def cache_with_key(keyfunc, cache_name=None, timeout=None):
    """Decorator which applies Django caching to a function.

       Decorator argument is a function which computes a cache key
       from the original function's arguments.  You are responsible
       for avoiding collisions with other uses of this decorator or
       other uses of caching."""

    def decorator(func):
        @wraps(func)
        def func_with_caching(*args, **kwargs):
            if cache_name is None:
                cache_backend = djcache
            else:
                cache_backend = get_cache(cache_name)

            key = keyfunc(*args, **kwargs)
            val = cache_backend.get(key)

            # Values are singleton tuples so that we can distinguish
            # a result of None from a missing key.
            if val is not None:
                return val[0]

            val = func(*args, **kwargs)
            cache_backend.set(key, (val,), timeout=timeout)
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

def message_cache_key(message_id):
    return "message:%d" % (message_id,)

def user_profile_by_email_cache_key(email):
    return 'user_profile_by_email:%s' % (hashlib.sha1(email).hexdigest(),)

def user_profile_by_user_cache_key(user_id):
    return 'user_profile_by_user_id:%d' % (user_id,)

def user_profile_by_id_cache_key(user_profile_id):
    return "user_profile_by_id:%s" % (user_profile_id,)

def user_by_id_cache_key(user_id):
    return 'user_by_id:%d' % (user_id,)

# Called by models.py to flush the user_profile cache whenever we save
# a user_profile object
def update_user_profile_cache(sender, **kwargs):
    user_profile = kwargs['instance']
    items_for_memcached = {}
    items_for_memcached[user_profile_by_email_cache_key(user_profile.user.email)] = (user_profile,)
    items_for_memcached[user_profile_by_user_cache_key(user_profile.user.id)] = (user_profile,)
    items_for_memcached[user_profile_by_id_cache_key(user_profile.id)] = (user_profile,)
    djcache.set_many(items_for_memcached)

# Called by models.py to flush the user_profile cache whenever we save
# a user_profile object
def update_user_cache(sender, **kwargs):
    user = kwargs['instance']
    items_for_memcached = {}
    items_for_memcached[user_by_id_cache_key(user.id)] = (user,)
    djcache.set_many(items_for_memcached)


from django.conf import settings
from django.contrib.sessions.models import Session
from zephyr.lib.context_managers import lockfile
from zephyr.models import Realm, Stream, UserProfile, UserActivity, \
    Subscription, Recipient, Message, UserMessage, valid_stream_name, \
    DefaultStream, StreamColor, UserPresence, MAX_SUBJECT_LENGTH, \
    MAX_MESSAGE_LENGTH, get_client, get_stream, get_recipient, get_huddle
from django.db import transaction, IntegrityError
from django.db.models import F
from django.core.exceptions import ValidationError

from zephyr.lib.initial_password import initial_password
from zephyr.lib.timestamp import timestamp_to_datetime, datetime_to_timestamp
from zephyr.lib.cache_helpers import cache_save_message
from zephyr.lib.queue import SimpleQueueClient
from django.utils import timezone
from zephyr.lib.create_user import create_user
from zephyr.lib.bulk_create import batch_bulk_create
from zephyr.lib import bugdown
from zephyr.lib.cache import cache_with_key, user_profile_by_id_cache_key, \
    user_profile_by_email_cache_key
from zephyr.decorator import get_user_profile_by_email, json_to_list

import subprocess
import simplejson
import time
import traceback
import re
import requests
import datetime
import os
import platform
import logging
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
            log.write(simplejson.dumps(event) + '\n')

def do_create_user(email, password, realm, full_name, short_name,
                   active=True):
    log_event({'type': 'user_created',
               'timestamp': time.time(),
               'full_name': full_name,
               'short_name': short_name,
               'user': email,
               'domain': realm.domain})
    return create_user(email, password, realm, full_name, short_name, active)

def user_sessions(user):
    return [s for s in Session.objects.all() if s.get_decoded().get('_auth_user_id') == user.id]

def do_deactivate(user_profile):
    user_profile.user.set_unusable_password()
    user_profile.user.is_active = False
    user_profile.user.save()

    for session in user_sessions(user_profile.user):
        session.delete()

    log_event({'type': 'user_deactivated',
               'timestamp': time.time(),
               'user': user_profile.user.email,
               'domain': user_profile.realm.domain})

def do_change_user_email(user, new_email):
    old_email = user.email
    user.email = new_email
    user.save()

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

@cache_with_key(lambda realm, email: user_profile_by_email_cache_key(email))
@transaction.commit_on_success
def create_mit_user_if_needed(realm, email):
    try:
        return UserProfile.objects.get(user__email__iexact=email)
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
            return UserProfile.objects.get(user__email__iexact=email)

def log_message(message):
    if not message.sending_client.name.startswith("test:"):
        log_event(message.to_log_dict())

@cache_with_key(user_profile_by_id_cache_key)
def get_user_profile_by_id(uid):
    return UserProfile.objects.select_related().get(id=uid)

def do_send_message(message, rendered_content=None, no_log=False,
                    stream=None):
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
                      s in Subscription.objects.select_related(
                "user_profile", "user_profile__user").filter(recipient=message.recipient, active=True)]
    else:
        raise ValueError('Bad recipient type')

    # Save the message receipts in the database
    with transaction.commit_on_success():
        message.save()
        ums_to_create = [UserMessage(user_profile=user_profile, message=message)
                         for user_profile in recipients
                         if user_profile.user.is_active]
        for um in ums_to_create:
            sent_by_human = message.sending_client.name.lower() in \
                                ['website', 'iphone', 'android']
            if um.user_profile == message.sender and sent_by_human:
                um.flags |= UserMessage.flags.read
        batch_bulk_create(UserMessage, ums_to_create)

    cache_save_message(message)

    # We can only publish messages to longpolling clients if the Tornado server is running.
    if settings.TORNADO_SERVER:
        # Render Markdown etc. here and store (automatically) in
        # memcached, so that the single-threaded Tornado server
        # doesn't have to.
        message.to_dict(apply_markdown=True, rendered_content=rendered_content)
        message.to_dict(apply_markdown=False)
        data = dict(
            secret   = settings.SHARED_SECRET,
            message  = message.id,
            users    = simplejson.dumps([str(user.id) for user in recipients]))
        if message.recipient.type == Recipient.STREAM:
            # Note: This is where authorization for single-stream
            # get_updates happens! We only attach stream data to the
            # notify_new_message request if it's a public stream,
            # ensuring that in the tornado server, non-public stream
            # messages are only associated to their subscribed users.
            if stream is None:
                stream = Stream.objects.select_related("realm").get(id=message.recipient.type_id)
            if stream.is_public():
                data['realm_id'] = stream.realm.id
                data['stream_name'] = stream.name
        requests.post(settings.TORNADO_SERVER + '/notify_new_message', data=data)

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
    except (simplejson.decoder.JSONDecodeError, ValueError):
        recipients = [raw_recipients]

    # Strip recipients, and then remove any duplicates and any that
    # are the empty string after being stripped.
    recipients = [recipient.strip() for recipient in recipients]
    return list(set(recipient for recipient in recipients if recipient))

# check_send_message:
# Returns None on success or the error message on error.
def check_send_message(sender, client, message_type_name, message_to,
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
        if len(stream_name) > 30:
            return "Stream name too long"
        if not valid_stream_name(stream_name):
            return "Invalid stream name"

        if subject_name is None:
            return "Missing subject"
        subject = subject_name.strip()
        if subject == "":
            return "Subject can't be empty"
        if len(subject) > MAX_SUBJECT_LENGTH:
            return "Subject too long"
        ## FIXME: Commented out temporarily while we figure out what we want
        # if not valid_stream_name(subject):
        #     return json_error("Invalid subject name")

        stream = get_stream(stream_name, realm)
        if stream is None:
            return "Stream does not exist"
        recipient = get_recipient(Recipient.STREAM, stream.id)
    elif message_type_name == 'private':
        not_forged_zephyr_mirror = client and client.name == "zephyr_mirror" and not forged
        try:
            recipient = recipient_for_emails(message_to, not_forged_zephyr_mirror,
                                             forwarder_user_profile, sender)
        except ValidationError, e:
            return e.messages[0]
    else:
        return "Invalid message type"

    rendered_content = bugdown.convert(message_content)
    if rendered_content is None:
        return "We were unable to render your message"

    message = Message()
    message.sender = sender
    message.content = message_content
    message.rendered_content = rendered_content
    message.rendered_content_version = bugdown.version
    message.recipient = recipient
    if message_type_name == 'stream':
        message.subject = subject
    if forged:
        # Forged messages come with a timestamp
        message.pub_date = timestamp_to_datetime(forged_timestamp)
    else:
        message.pub_date = timezone.now()
    message.sending_client = client

    if client.name == "zephyr_mirror" and already_sent_mirrored_message(message):
        return None

    do_send_message(message, rendered_content=rendered_content,
                    stream=stream)

    return None

def internal_send_message(sender_email, recipient_type_name, recipients,
                          subject, content, realm=None):
    if len(content) > MAX_MESSAGE_LENGTH:
        content = content[0:3900] + "\n\n[message was too long and has been truncated]"

    sender = get_user_profile_by_email(sender_email)
    if realm is None:
        realm = sender.realm
    parsed_recipients = extract_recipients(recipients)
    if recipient_type_name == "stream":
        stream, _ = create_stream_if_needed(realm, parsed_recipients[0])

    ret = check_send_message(sender, get_client("Internal"), recipient_type_name,
                             parsed_recipients, subject, content, realm)
    if ret is not None:
        logging.error("Error sending internal message by %s: %s" % (sender_email, ret))

def get_stream_colors(user_profile):
    return [(sub["name"], sub["color"]) for sub in gather_subscriptions(user_profile)]

def pick_color(user_profile):
    # These colors are shared with the palette in subs.js.
    stream_assignment_colors = [
        "#76ce90", "#fae589", "#a6c7e5", "#e79ab5",
        "#bfd56f", "#f4ae55", "#b0a5fd", "#addfe5",
        "#f5ce6e", "#c2726a", "#94c849", "#bd86e5",
        "#ee7e4a", "#a6dcbf", "#95a5fd", "#53a063",
        "#9987e1", "#e4523d", "#c2c2c2", "#4f8de4",
        "#c6a8ad", "#e7cc4d", "#c8bebf", "#a47462"]
    used_colors = [elt[1] for elt in get_stream_colors(user_profile) if elt[1]]
    available_colors = filter(lambda x: x not in used_colors,
                              stream_assignment_colors)

    if available_colors:
        return available_colors[0]
    else:
        return stream_assignment_colors[len(used_colors) % len(stream_assignment_colors)]

def get_subscription(stream_name, user_profile):
    stream = get_stream(stream_name, user_profile.realm)
    recipient = get_recipient(Recipient.STREAM, stream.id)
    return Subscription.objects.filter(user_profile=user_profile,
                                       recipient=recipient, active=True)

def set_stream_color(user_profile, stream_name, color=None):
    subscription = get_subscription(stream_name, user_profile)
    stream_color, _ = StreamColor.objects.get_or_create(subscription=subscription[0])
    # TODO: sanitize color.
    if not color:
        color = pick_color(user_profile)
    stream_color.color = color
    stream_color.save()

def do_add_subscription(user_profile, stream, no_log=False):
    recipient = get_recipient(Recipient.STREAM, stream.id)
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
    set_stream_color(user_profile, stream.name)
    return did_subscribe

def do_remove_subscription(user_profile, stream, no_log=False):
    recipient = get_recipient(Recipient.STREAM, stream.id)
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
        domain = UserProfile.objects.get(user=user).realm.domain
        log_event({'type': 'user_activated',
                   'user': user.email,
                   'domain': domain})

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

        internal_send_message("humbug+signups@humbughq.com", "stream",
                              "signups", domain, "Signups enabled.")
    return (realm, created)

def do_change_enable_desktop_notifications(user_profile, enable_desktop_notifications, log=True):
    user_profile.enable_desktop_notifications = enable_desktop_notifications
    user_profile.save()
    if log:
        log_event({'type': 'enable_desktop_notifications_changed',
                   'user': user_profile.user.email,
                   'enable_desktop_notifications': enable_desktop_notifications})

def do_change_enter_sends(user_profile, enter_sends):
    user_profile.enter_sends = enter_sends
    user_profile.save()

def set_default_streams(realm, stream_names):
    DefaultStream.objects.filter(realm=realm).delete()
    for stream_name in stream_names:
        stream, _ = create_stream_if_needed(realm, stream_name)
        DefaultStream.objects.create(stream=stream, realm=realm)

def add_default_subs(user_profile):
    for default in DefaultStream.objects.filter(realm=user_profile.realm):
        do_add_subscription(user_profile, default.stream)

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
    activity.save()

def process_user_activity_event(event):
    user_profile = UserProfile.objects.get(id=event["user_profile_id"])
    client = get_client(event["client"])
    log_time = timestamp_to_datetime(event["time"])
    query = event["query"]
    return do_update_user_activity(user_profile, client, query, log_time)

@transaction.commit_on_success
def do_update_user_presence(user_profile, client, log_time, status):
    try:
        (presence, created) = UserPresence.objects.get_or_create(
            user_profile = user_profile,
            client = client,
            defaults = {'timestamp': log_time})
    except IntegrityError:
        transaction.commit()
        presence = UserPresence.objects.get(user_profile = user_profile,
                                            client = client)
    presence.timestamp = log_time
    presence.status = status
    presence.save()

if settings.USING_RABBITMQ or settings.TEST_SUITE:
    # RabbitMQ is required for idle and unread functionality
    if settings.USING_RABBITMQ:
        actions_queue = SimpleQueueClient()

    def update_user_presence(user_profile, client, log_time, status):
        event={'type': 'user_presence',
               'user_profile_id': user_profile.id,
               'status': status,
               'time': datetime_to_timestamp(log_time),
               'client': client.name}

        if settings.USING_RABBITMQ:
            actions_queue.json_publish("user_activity", event)
        elif settings.TEST_SUITE:
            process_user_presence_event(event)

    def update_message_flags(user_profile, operation, flag, messages, all):
        rest_until = None

        if all:
            # Do the first 450 message updates in-process, as this is a
            # bankruptcy request and the user is about to reload. We don't
            # want them to see a bunch of unread messages while we go about
            # doing the work
            first_batch = 450
            flagattr = getattr(UserMessage.flags, flag)

            all_ums = UserMessage.objects.filter(user_profile=user_profile)
            if operation == "add":
                umessages = all_ums.filter(flags=~flagattr)
            elif operation == "remove":
                umessages = all_ums.filter(flags=flagattr)

            mids = [m.id for m in umessages.order_by('-id')[:first_batch]]
            to_update = UserMessage.objects.filter(id__in=mids)

            if operation == "add":
                to_update.update(flags=F('flags') | flagattr)
            elif operation == "remove":
                to_update.update(flags=F('flags') & ~flagattr)

            if len(mids) == 0:
                return True

            rest_until = mids[len(mids) - 1]

        event = {'type':            'update_message',
                 'user_profile_id': user_profile.id,
                 'operation':       operation,
                 'flag':            flag,
                 'messages':        messages,
                 'until_id':        rest_until}
        if settings.USING_RABBITMQ:
            actions_queue.json_publish("user_activity", event)
        else:
            return process_update_message_flags(event)
else:
    update_user_presence = lambda user_profile, client, log_time, status: None
    update_message_flags = lambda user_profile, operation, flag, messages, all: None

def process_user_presence_event(event):
    user_profile = UserProfile.objects.get(id=event["user_profile_id"])
    client = get_client(event["client"])
    log_time = timestamp_to_datetime(event["time"])
    status = event["status"]
    return do_update_user_presence(user_profile, client, log_time, status)

def process_update_message_flags(event):
    user_profile = UserProfile.objects.get(id=event["user_profile_id"])
    try:
        until_id = event["until_id"]
        messages = event["messages"]
        flag = event["flag"]
        op = event["operation"]
    except (KeyError, AttributeError):
        return False

    # Shell out bankruptcy requests as we split them up into many
    # pieces to avoid swamping the db
    if until_id and not settings.TEST_SUITE:
        update_flags_externally(op, flag, user_profile, until_id)
        return True

    flagattr = getattr(UserMessage.flags, flag)
    msgs = UserMessage.objects.filter(user_profile=user_profile,
                                      message__id__in=messages)

    # If we're running in the test suite, don't shell out to manage.py.
    # Updates that the manage.py command makes don't seem to be immediately
    # reflected in the next in-process sqlite queries.
    # TODO(leo) remove when tests switch to postgres
    if settings.TEST_SUITE and until_id:
        msgs = UserMessage.objects.filter(user_profile=user_profile,
                                          id__lte=until_id)

    if op == 'add':
        msgs.update(flags=F('flags') | flagattr)
    elif op == 'remove':
        msgs.update(flags=F('flags') & ~flagattr)

    return True

def update_flags_externally(op, flag, user_profile, until_id):
    args = ['python', os.path.join(os.path.dirname(__file__), '../..', 'manage.py'),
            'set_message_flags', '--for-real', '-o', op, '-f', flag, '-m', user_profile.user.email,
            '-u', str(until_id)]

    subprocess.Popen(args, stdin=subprocess.PIPE, stdout=None, stderr=None)

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

    stream_ids = [sc.subscription.recipient.type_id for sc in with_color] + \
        [sub.recipient.type_id for sub in no_color]

    stream_hash = {}
    for stream in Stream.objects.filter(id__in=stream_ids):
        stream_hash[stream.id] = (stream.name, stream.invite_only)

    result = []
    for sc in with_color:
        (stream_name, invite_only) = stream_hash[sc.subscription.recipient.type_id]
        result.append({'name': stream_name,
                       'in_home_view': sc.subscription.in_home_view,
                       'invite_only': invite_only,
                       'color': sc.color})
    for sub in no_color:
        (stream_name, invite_only) = stream_hash[sub.recipient.type_id]
        result.append({'name': stream_name,
                       'in_home_view': sub.in_home_view,
                       'invite_only': invite_only,
                       'color': StreamColor.DEFAULT_STREAM_COLOR})

    return sorted(result)


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

from zephyr.lib.initial_password import initial_password, initial_api_key
from zephyr.models import Realm, Stream, User, UserProfile, Huddle, \
    Subscription, Recipient, Client, Message, \
    get_huddle_hash
from zephyr.lib.create_user import create_user_base

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

def bulk_create_realms(realm_list):
    existing_realms = set(r.domain for r in Realm.objects.select_related().all())

    realms_to_create = []
    for domain in realm_list:
        if domain not in existing_realms:
            realms_to_create.append(Realm(domain=domain))
            existing_realms.add(domain)
    batch_bulk_create(Realm, realms_to_create)

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

def bulk_create_clients(client_list):
    existing_clients = set(client.name for client in Client.objects.select_related().all())

    clients_to_create = []
    for name in client_list:
        if name not in existing_clients:
            clients_to_create.append(Client(name=name))
            existing_clients.add(name)
    batch_bulk_create(Client, clients_to_create)

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

# -*- coding: utf-8 -*-
from time import sleep

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

import datetime
import calendar
from django.utils.timezone import utc

def timestamp_to_datetime(timestamp):
    return datetime.datetime.utcfromtimestamp(float(timestamp)).replace(tzinfo=utc)

def datetime_to_timestamp(datetime_object):
    return calendar.timegm(datetime_object.timetuple())

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
import urllib2
import simplejson
import twitter

from django.core import mail
from django.conf import settings

from zephyr.lib.avatar  import gravatar_hash
from zephyr.lib.bugdown import codehilite, fenced_code
from zephyr.lib.bugdown.fenced_code import FENCE_RE
from zephyr.lib.timeout import timeout
from zephyr.lib.cache import cache_with_key

# Format version of the bugdown rendering; stored along with rendered
# messages so that we can efficiently determine what needs to be re-rendered
version = 1

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

class InlineImagePreviewProcessor(markdown.treeprocessors.Treeprocessor):
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

    # Search the tree for <a> tags and read their href values
    def find_images(self, root):
        def process_image_links(element):
            if element.tag != "a":
                return None

            url = element.get("href")
            youtube = self.youtube_image(url)
            if youtube is not None:
                return (youtube, url)
            dropbox = self.dropbox_image(url)
            if dropbox is not None:
                return (dropbox, url)
            if self.is_image(url):
                return (url, url)

        return walk_tree(root, process_image_links)

    def run(self, root):
        image_urls = self.find_images(root)
        for (url, link) in image_urls:
            a = markdown.util.etree.SubElement(root, "a")
            a.set("href", link)
            a.set("target", "_blank")
            a.set("title", link)
            img = markdown.util.etree.SubElement(a, "img")
            img.set("src", url)
            img.set("class", "message_inline_image")

        return root

@cache_with_key(lambda tweet_id: tweet_id, cache_name="database")
def fetch_tweet_data(tweet_id):
    if settings.TEST_SUITE:
        import testing_mocks
        res = testing_mocks.twitter(tweet_id)
    else:
        if settings.STAGING_DEPLOYED:
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
            res = api.GetStatus(tweet_id).AsDict()
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

class InlineInterestingLinkProcessor(markdown.treeprocessors.Treeprocessor):
    def twitter_link(self, url):
        parsed_url = urlparse.urlparse(url)
        if not (parsed_url.netloc == 'twitter.com' or parsed_url.netloc.endswith('.twitter.com')):
            return None

        tweet_id_match = re.match(r'^/.*?/status/(\d{18})$', parsed_url.path)
        if not tweet_id_match:
            return None

        tweet_id = tweet_id_match.groups()[0]
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

            return ('twitter', tweet)
        except:
            # We put this in its own try-except because it requires external
            # connectivity. If Twitter flakes out, we don't want to not-render
            # the entire message; we just want to not show the Twitter preview.
            logging.warning(traceback.format_exc())
            return None

    # Search the tree for <a> tags and read their href values
    def find_interesting_links(self, root):
        def process_interesting_links(element):
            if element.tag != "a":
                return None

            url = element.get("href")
            return self.twitter_link(url)

        return walk_tree(root, process_interesting_links, stop_after_first=True)

    def run(self, root):
        interesting_links = self.find_interesting_links(root)
        for (service_name, data) in interesting_links:
            div = markdown.util.etree.SubElement(root, "div")
            div.set("class", "inline-preview-%s" % service_name)
            div.insert(0, data)
        return root

class Gravatar(markdown.inlinepatterns.Pattern):
    def handleMatch(self, match):
        img = markdown.util.etree.Element('img')
        img.set('class', 'message_body_gravatar img-rounded')
        img.set('src', 'https://secure.gravatar.com/avatar/%s?d=identicon&s=30'
            % (gravatar_hash(match.group('email')),))
        return img

path_to_emoji = os.path.join(os.path.dirname(__file__), '..', '..',
                             # This should be zephyr/
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

def fixup_link(link):
    """Set certain attributes we want on every link."""
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

    # Humbug modification: If scheme is not specified, assume http://
    # It's unlikely that users want relative links within humbughq.com.
    # We re-enter sanitize_url because netloc etc. need to be re-parsed.
    if not scheme:
        return sanitize_url('http://' + url)

    locless_schemes = ['', 'mailto', 'news']
    if netloc == '' and scheme not in locless_schemes:
        # This fails regardless of anything else.
        # Return immediately to save additional proccessing
        return None

    for part in parts[2:]:
        if ":" in part:
            # Not a safe url
            return None

    # Url passes all tests. Return url as-is.
    return urlparse.urlunparse(parts)

def url_to_a(url):
    a = markdown.util.etree.Element('a')
    if '@' in url:
        href = 'mailto:' + url
    else:
        href = url

    href = sanitize_url(href)
    if href is None:
        # Rejected by sanitize_url; render it as plain text.
        return url

    a.set('href', href)
    a.text = url
    fixup_link(a)
    return a

class AutoLink(markdown.inlinepatterns.Pattern):
    def handleMatch(self, match):
        url = match.group('url')
        # As this will also match already-matched https?:// links,
        # don't doubly-link them
        if url[:5] == 'http:' or url[:6] == 'https:':
            return url
        return url_to_a(url)

class HttpLink(markdown.inlinepatterns.Pattern):
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
        md.inlinePatterns.add('emoji', Emoji(r'(?<!\S)(?P<syntax>:[^:\s]+:)(?!\S)'), '_begin')
        md.inlinePatterns.add('link', LinkPattern(markdown.inlinepatterns.LINK_RE, md), '>backtick')

        # markdown.inlinepatterns.Pattern compiles this with re.UNICODE, which
        # is important because we're using \w.
        #
        # This rule must come after the built-in 'link' markdown linkifier to
        # avoid errors.
        http_link_regex = r'\b(?P<url>https?://[^\s]+?)(?=[^\w/]*(\s|\Z))'
        md.inlinePatterns.add('http_autolink', HttpLink(http_link_regex), '>link')

        # A link starts at a word boundary, and ends at space, punctuation, or end-of-input.
        #
        # We detect a url by checking for the TLD, and building around it.
        #
        # To support () in urls but not match ending ) when a url is inside a parenthesis,
        # we match at maximum one set of matching parens in a url. We could extend this
        # to match two parenthetical groups, at the cost of more regex complexity.
        #
        # This rule must come after the http_autolink rule we add above to avoid double
        # linkifying.
        tlds = '|'.join(['co.uk', 'com', 'co', 'biz', 'gd', 'org', 'net', 'ly', 'edu', 'mil',
                         'gov', 'info', 'me', 'it', '.ca', 'tv', 'fm', 'io', 'gl'])
        link_regex = r"\b(?P<url>[^\s]+\.(%s)(?:/[^\s()\":]*?|([^\s()\":]*\([^\s()\":]*\)[^\s()\":]*))?)(?=([:;\?\),\.\'\"]\Z|[:;\?\),\.\'\"]\s|\Z|\s))" % (tlds,)
        md.inlinePatterns.add('autolink', AutoLink(link_regex), '>http_autolink')

        md.preprocessors.add('hanging_ulists',
                                 BugdownUListPreprocessor(md),
                                 "_begin")

        md.treeprocessors.add("inline_images", InlineImagePreviewProcessor(md), "_end")
        md.treeprocessors.add("inline_interesting_links", InlineInterestingLinkProcessor(md), "_end")

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

def convert(md):
    """Convert Markdown to HTML, with Humbug-specific settings and hacks."""

    # Reset the parser; otherwise it will get slower over time.
    _md_engine.reset()

    try:
        # Spend at most 5 seconds rendering.
        # Sometimes Python-Markdown is really slow; see
        # https://trac.humbughq.com/ticket/345
        return timeout(5, _md_engine.convert, md)
    except:
        from zephyr.models import Recipient
        from zephyr.lib.actions import internal_send_message

        cleaned = _sanitize_for_log(md)

        # Output error to log as well as sending a humbug and email
        logging.getLogger('').error('Exception in Markdown parser: %sInput (sanitized) was: %s'
            % (traceback.format_exc(), cleaned))
        subject = "Markdown parser failure"
        internal_send_message("humbug+errors@humbughq.com", "stream",
                "devel", subject, "Markdown parser failed, message sent to devel@")
        mail.mail_admins(subject, "Failed message: %s\n\n%s\n\n" % (
                                    cleaned, traceback.format_exc()),
                         fail_silently=False)
        return None

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

        md.preprocessors.add('fenced_code_block',
                                 FencedBlockPreprocessor(md),
                                 "_begin")


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


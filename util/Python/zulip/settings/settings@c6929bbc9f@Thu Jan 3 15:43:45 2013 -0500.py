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
        'HOST': ''
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
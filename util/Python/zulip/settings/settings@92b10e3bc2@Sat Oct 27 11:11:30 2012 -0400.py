# Django settings for humbug project.
import os
import platform

deployed = (('humbughq.com' in platform.node())
            or os.path.exists('/etc/humbug-server'))

DEBUG = not deployed
TEMPLATE_DEBUG = DEBUG

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

ADMINS = (
    ('Jessica McKellar', 'jessica.mckellar@gmail.com'),
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

if deployed:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': '/etc/mysql/my.cnf',
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
if deployed:
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

# Are we running in an environment with the Tornado server?
# This should be True for both deployment and local development.
# We set it to False when running tests or populate_db.
HAVE_TORNADO_SERVER = True

# URL where Django code posts to the Tornado code to notify of new messages
NOTIFY_NEW_MESSAGE_URL = 'http://localhost:9993/notify_new_message'
# URL where Django code posts to the Tornado code to notify of pointer updates
NOTIFY_POINTER_UPDATE_URL = 'http://localhost:9993/notify_pointer_update'

# Make redirects work properly behind a reverse proxy
USE_X_FORWARDED_HOST = True

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'zephyr.middleware.LogRequests',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = ('humbug.backends.EmailAuthBackend',)

ROOT_URLCONF = 'humbug.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'humbug.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'jstemplate',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'confirmation',
    'zephyr',
)

# Caching
CACHES = {
    'default': {
        'BACKEND':  'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'humbug-default-local-cache',
        'TIMEOUT':  3600,
        'OPTIONS': {
            'MAX_ENTRIES': 100000
        }
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
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
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
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

MESSAGE_LOG="all_messages_log"

if deployed:
    ALLOW_REGISTER = False
    FULL_NAVBAR    = False
    NOT_LOGGED_IN_REDIRECT = 'django.contrib.auth.views.login'
else:
    ALLOW_REGISTER = True
    FULL_NAVBAR    = True
    NOT_LOGGED_IN_REDIRECT = 'zephyr.views.accounts_home'

# For testing, you may want to have emails be printed to the console.
if not deployed:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

    # Use fast password hashing for creating testing users when not
    # deployed
    PASSWORD_HASHERS = (
                'django.contrib.auth.hashers.SHA1PasswordHasher',
            )
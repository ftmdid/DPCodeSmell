#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "humbug.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


from django.contrib.auth.models import User, check_password

class EmailAuthBackend(object):
    """
    Email Authentication Backend

    Allows a user to sign in using an email/password pair rather than
    a username/password pair.
    """

    def authenticate(self, username=None, password=None):
        """ Authenticate a user based on email address as the user name. """
        try:
            user = User.objects.get(email=username)
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

deployed = (platform.node() == 'humbug-dev')

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

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# A fixed salt used for hashing in certain places, e.g. email-based
# username generation.
HASH_SALT = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

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
    'django.contrib.staticfiles',
    'jstemplate',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
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

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
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
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level':    'INFO'
        }
    }
}

ACCOUNT_ACTIVATION_DAYS=7
EMAIL_HOST='localhost'
EMAIL_PORT=9991
EMAIL_HOST_USER='username'
EMAIL_HOST_PASSWORD='password'

LOGIN_REDIRECT_URL='/'

from django.conf import settings
from django.conf.urls import patterns, url
import os.path

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'zephyr.views.home', name='home'),
    url(r'^update$', 'zephyr.views.update', name='update'),
    url(r'^get_updates_longpoll$', 'zephyr.views.get_updates_longpoll', name='get_updates_longpoll'),
    url(r'^zephyr/', 'zephyr.views.zephyr', name='zephyr'),
    url(r'^forge_zephyr/', 'zephyr.views.forge_zephyr', name='forge_zephyr'),
    url(r'^accounts/home/', 'zephyr.views.accounts_home', name='accounts_home'),
    url(r'^accounts/login/', 'django.contrib.auth.views.login', {'template_name': 'zephyr/login.html'}),
    url(r'^accounts/logout/', 'django.contrib.auth.views.logout', {'template_name': 'zephyr/index.html'}),
    url(r'^accounts/register/', 'zephyr.views.register', name='register'),
    url(r'^settings/manage/$', 'zephyr.views.manage_settings', name='manage_settings'),
    url(r'^settings/change/$', 'zephyr.views.change_settings', name='change_settings'),
    url(r'^subscriptions/$', 'zephyr.views.subscriptions', name='subscriptions'),
    url(r'^json/subscriptions/list$', 'zephyr.views.json_list_subscriptions', name='list_subscriptions'),
    url(r'^json/subscriptions/remove$', 'zephyr.views.json_remove_subscription', name='remove_subscription'),
    url(r'^json/subscriptions/add$', 'zephyr.views.json_add_subscription', name='add_subscription'),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(settings.SITE_ROOT, '..', 'zephyr', 'static/')}),
    url(r'^subscriptions/exists/(?P<zephyr_class>.*)$', 'zephyr.views.class_exists', name='class_exists'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

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

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.signals import post_save
import hashlib
import base64
import calendar
import datetime
from zephyr.lib.cache import cache_with_key

from django.db.models.signals import class_prepared
import markdown
md_engine = markdown.Markdown(
    extensions    = ['fenced_code', 'codehilite'],
    safe_mode     = True,
    output_format = 'xhtml' )

def get_display_recipient(recipient):
    """
    recipient: an instance of Recipient.

    returns: an appropriate string describing the recipient (the class
    name, for a class, or the email, for a user).
    """
    if recipient.type == Recipient.CLASS:
        zephyr_class = ZephyrClass.objects.get(id=recipient.type_id)
        return zephyr_class.name
    elif recipient.type == Recipient.HUDDLE:
        user_profile_list = [UserProfile.objects.get(user=s.userprofile) for s in
                             Subscription.objects.filter(recipient=recipient)]
        return [{'email': user_profile.user.email,
                 'name': user_profile.short_name} for user_profile in user_profile_list]
    else:
        user = User.objects.get(id=recipient.type_id)
        return user.email

callback_table = {}
mit_sync_table = {}

class Realm(models.Model):
    domain = models.CharField(max_length=40, db_index=True)

    def __repr__(self):
        return "<Realm: %s %s>" % (self.domain, self.id)
    def __str__(self):
        return self.__repr__()

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    full_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100)
    pointer = models.IntegerField()
    realm = models.ForeignKey(Realm)

    # The user receives this message
    def receive(self, message):
        global callback_table

        # Should also store in permanent database the receipt
        um = UserMessage(user_profile=self, message=message)
        um.save()

        for cb in callback_table.get(self.user.id, []):
            cb([message])

        callback_table[self.user.id] = []

    def add_callback(self, cb, last_received):
        global callback_table

        new_zephyrs = [um.message for um in
                       UserMessage.objects.filter(user_profile=self,
                                                  message__id__gt=last_received)]

        if new_zephyrs:
            return cb(new_zephyrs)
        callback_table.setdefault(self.user.id, []).append(cb)

    def __repr__(self):
        return "<UserProfile: %s %s>" % (self.user.email, self.realm)
    def __str__(self):
        return self.__repr__()

    @classmethod
    def create(cls, user, realm, full_name, short_name):
        """When creating a new user, make a profile for him or her."""
        if not cls.objects.filter(user=user):
            profile = cls(user=user, pointer=-1, realm_id=realm.id,
                          full_name=full_name, short_name=short_name)
            profile.save()
            # Auto-sub to the ability to receive personals.
            recipient = Recipient(type_id=profile.id, type=Recipient.PERSONAL)
            recipient.save()
            Subscription(userprofile=profile, recipient=recipient).save()

def create_user(email, password, realm, full_name, short_name):
    # NB: the result of Base32 + truncation is not a valid Base32 encoding.
    # It's just a unique alphanumeric string.
    # Use base32 instead of base64 so we don't have to worry about mixed case.
    # Django imposes a limit of 30 characters on usernames.
    email_hash = hashlib.sha256(settings.HASH_SALT + email).digest()
    username = base64.b32encode(email_hash)[:30]
    user = User.objects.create_user(username=username, password=password,
                                    email=email)
    user.save()
    UserProfile.create(user, realm, full_name, short_name)

class ZephyrClass(models.Model):
    name = models.CharField(max_length=30, db_index=True)
    realm = models.ForeignKey(Realm, db_index=True)

    def __repr__(self):
        return "<ZephyrClass: %s>" % (self.name,)
    def __str__(self):
        return self.__repr__()

    @classmethod
    def create(cls, name, realm):
        zephyr_class = cls(name=name, realm=realm)
        zephyr_class.save()

        recipient = Recipient(type_id=zephyr_class.id, type=Recipient.CLASS)
        recipient.save()
        return (zephyr_class, recipient)

class Recipient(models.Model):
    type_id = models.IntegerField(db_index=True)
    type = models.PositiveSmallIntegerField(db_index=True)
    # Valid types are {personal, class, huddle}
    PERSONAL = 1
    CLASS = 2
    HUDDLE = 3

    def type_name(self):
        if self.type == self.PERSONAL:
            return "personal"
        elif self.type == self.CLASS:
            return "class"
        elif self.type == self.HUDDLE:
            return "huddle"
        else:
            raise

    def __repr__(self):
        display_recipient = get_display_recipient(self)
        return "<Recipient: %s (%d, %s)>" % (display_recipient, self.type_id, self.type)

class Zephyr(models.Model):
    sender = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    instance = models.CharField(max_length=30)
    content = models.TextField()
    pub_date = models.DateTimeField('date published')

    def __repr__(self):
        display_recipient = get_display_recipient(self.recipient)
        return "<Zephyr: %s / %s / %r>" % (display_recipient, self.instance, self.sender)
    def __str__(self):
        return self.__repr__()

    @cache_with_key(lambda self: 'zephyr_dict:%d' % (self.id,))
    def to_dict(self):
        return {'id'               : self.id,
                'sender_email'     : self.sender.user.email,
                'sender_name'      : self.sender.full_name,
                'type'             : self.recipient.type_name(),
                'display_recipient': get_display_recipient(self.recipient),
                'recipient_id'     : self.recipient.id,
                'instance'         : self.instance,
                'content'          : md_engine.convert(self.content),
                'timestamp'        : calendar.timegm(self.pub_date.timetuple()),
                'gravatar_hash'    : hashlib.md5(settings.HASH_SALT + self.sender.user.email).hexdigest(),
                }

class UserMessage(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    message = models.ForeignKey(Zephyr)
    # We're not using the archived field for now, but create it anyway
    # since this table will be an unpleasant one to do schema changes
    # on later
    archived = models.BooleanField()

    def __repr__(self):
        display_recipient = get_display_recipient(self.message.recipient)
        return "<UserMessage: %s / %s>" % (display_recipient, self.user_profile.user.email)

user_hash = {}
def get_user_profile_by_id(uid):
    if uid in user_hash:
        return user_hash[uid]
    return UserProfile.objects.get(id=uid)

def do_send_zephyr(zephyr, synced_from_mit=False):
    mit_sync_table[zephyr.id] = synced_from_mit
    zephyr.save()
    if zephyr.recipient.type == Recipient.PERSONAL:
        recipients = list(set([get_user_profile_by_id(zephyr.recipient.type_id),
                               get_user_profile_by_id(zephyr.sender_id)]))
        # For personals, you send out either 1 or 2 copies of the zephyr, for
        # personals to yourself or to someone else, respectively.
        assert((len(recipients) == 1) or (len(recipients) == 2))
    elif (zephyr.recipient.type == Recipient.CLASS or
          zephyr.recipient.type == Recipient.HUDDLE):
        recipients = [get_user_profile_by_id(s.userprofile_id) for
                      s in Subscription.objects.filter(recipient=zephyr.recipient, active=True)]
    else:
        raise
    for recipient in recipients:
        recipient.receive(zephyr)

class Subscription(models.Model):
    userprofile = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    active = models.BooleanField(default=True)

    def __repr__(self):
        return "<Subscription: %r -> %r>" % (self.userprofile, self.recipient)
    def __str__(self):
        return self.__repr__()

class Huddle(models.Model):
    # TODO: We should consider whether using
    # CommaSeparatedIntegerField would be better.
    huddle_hash = models.CharField(max_length=40, db_index=True)

def get_huddle(id_list):
    id_list = sorted(set(id_list))
    hash_key = ",".join(str(x) for x in id_list)
    huddle_hash = hashlib.sha1(hash_key).hexdigest()
    if Huddle.objects.filter(huddle_hash=huddle_hash):
        return Huddle.objects.get(huddle_hash=huddle_hash)
    else:
        # since we don't have one, make a new huddle
        huddle = Huddle(huddle_hash = huddle_hash)
        huddle.save()
        recipient = Recipient(type_id=huddle.id, type=Recipient.HUDDLE)
        recipient.save()

        # Add subscriptions
        for uid in id_list:
            s = Subscription(recipient = recipient,
                             userprofile = UserProfile.objects.get(id=uid))
            s.save()
        return huddle

# This is currently dead code since all the places where we used to
# use it now have faster implementations, but I expect this to be
# potentially useful for code in the future, so not deleting it yet.
def filter_by_subscriptions(zephyrs, user):
    userprofile = UserProfile.objects.get(user=user)
    subscribed_zephyrs = []
    subscriptions = [sub.recipient for sub in
                     Subscription.objects.filter(userprofile=userprofile, active=True)]
    for zephyr in zephyrs:
        # If you are subscribed to the personal or class, or if you
        # sent the personal, you can see the zephyr.
        if (zephyr.recipient in subscriptions) or \
                (zephyr.recipient.type == Recipient.PERSONAL and
                 zephyr.sender == userprofile):
            subscribed_zephyrs.append(zephyr)

    return subscribed_zephyrs

import types

class TornadoAsyncException(Exception): pass

class _DefGen_Return(BaseException):
    def __init__(self, value):
        self.value = value

def returnResponse(value):
    raise _DefGen_Return(value)

def asynchronous(method):
    def wrapper(request, *args, **kwargs):
        try:
            v = method(request, request._tornado_handler, *args, **kwargs)
            if v == None or type(v) == types.GeneratorType:
                raise TornadoAsyncException
        except _DefGen_Return, e:
            request._tornado_handler.finish(e.value.content)
        return v
    return wrapper

#!/usr/bin/python
import mechanize
import urllib
import sys
import logging
import zephyr
import traceback
import simplejson
import re
import time
import subprocess
import optparse
import os
zephyr.init()

parser = optparse.OptionParser()
parser.add_option('--forward-class-messages',
                  dest='forward_class_messages',
                  default=False,
                  action='store_true')
parser.add_option('--resend-log',
                  dest='resend_log',
                  default=False,
                  action='store_true')
parser.add_option('--no-forward-personals',
                  dest='forward_personals',
                  default=True,
                  action='store_false')
parser.add_option('--forward-from-humbug',
                  dest='forward_to_humbug',
                  default=True,
                  action='store_false')
(options, args) = parser.parse_args()

browser = None
csrf_token = None

def browser_login():
    logger = logging.getLogger("mechanize")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)

    global browser
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    ## debugging code to consider
    # browser.set_debug_http(True)
    # browser.set_debug_responses(True)
    # browser.set_debug_redirects(True)
    # browser.set_handle_refresh(False)

    browser.add_password("https://app.humbughq.com/", "tabbott", "xxxxxxxxxxxxxxxxx", "wiki")
    browser.open("https://app.humbughq.com/")
    browser.follow_link(text_regex="\s*Log in\s*")
    browser.select_form(nr=0)
    browser["username"] = "starnine@mit.edu"
    browser["password"] = "xxxxxxxx"

    global csrf_token
    csrf_token = browser["csrfmiddlewaretoken"]

    browser.submit()

def send_humbug(zeph):
    zeph["sender"] = zeph["sender"].lower().replace("athena.mit.edu", "mit.edu")
    if "recipient" in zeph:
        zeph["recipient"] = zeph["recipient"].lower().replace("athena.mit.edu", "mit.edu")
    zeph['fullname']  = username_to_fullname(zeph['sender'])
    zeph['shortname'] = zeph['sender'].split('@')[0]

    browser.addheaders.append(('X-CSRFToken', csrf_token))

    humbug_data = []
    for key in zeph.keys():
        try: val = zeph[key].decode("utf-8").encode("utf-8")
        except:
            try:
                val = zeph[key].encode("utf-8")
            except:
                print "wtf!", zeph[key]
        humbug_data.append((key, val))
    browser.open("https://app.humbughq.com/forge_zephyr/", urllib.urlencode(humbug_data))

def fetch_fullname(username):
    try:
        match_user = re.match(r'([a-zA-Z0-9_]+)@mit\.edu', username)
        if match_user:
            proc = subprocess.Popen(['hesinfo', match_user.group(1), 'passwd'], stdout=subprocess.PIPE)
            out, _err_unused = proc.communicate()
            if proc.returncode == 0:
                return out.split(':')[4].split(',')[0]
    except:
        print >>sys.stderr, 'Error getting fullname for', username
        traceback.print_exc()

    return username.title().replace('@', ' at ').replace('.', ' dot ')

fullnames = {}
def username_to_fullname(username):
    if username not in fullnames:
        fullnames[username] = fetch_fullname(username)
    return fullnames[username]


def process_loop(log):
    import mit_subs_list
    while True:
        try:
            notice = zephyr.receive(block=True)
            zsig, body = notice.message.split("\x00", 1)
            is_personal = False
            is_huddle = False

            if zsig.endswith("`") and zsig.startswith("`"):
                print "Skipping message from Humbug!"
                continue

            sender = notice.sender.lower().replace("athena.mit.edu", "mit.edu")
            recipient = notice.recipient.lower().replace("athena.mit.edu", "mit.edu")

            if (notice.cls == "message" and
                notice.instance == "personal"):
                is_personal = True
                if body.startswith("CC:"):
                    is_huddle = True
                    # Map "CC: sipbtest espuser" => "starnine@mit.edu,espuser@mit.edu"
                    huddle_recipients_list = [x + "@mit.edu" for x in
                                              body.split("\n")[0][4:].split()]
                    if sender not in huddle_recipients_list:
                        huddle_recipients_list.append(sender)
                    huddle_recipients = ",".join(huddle_recipients_list)

            if notice.opcode != "":
                # skip PING messages
                continue

            # Drop messages not to the listed subscriptions
            if (notice.cls not in mit_subs_list.all_subs) and not (is_personal and
                                                                   options.forward_personals):
                print "Skipping ...", notice.cls, notice.instance, is_personal
                continue

            if is_huddle:
                zeph = { 'type'      : 'personal',
                         'time'      : str(notice.time),
                         'sender'    : sender,
                         'recipient' : huddle_recipients,
                         'zsig'      : zsig,  # logged here but not used by app
                         'new_zephyr': body.split("\n", 1)[1] }
            elif is_personal:
                zeph = { 'type'      : 'personal',
                         'time'      : str(notice.time),
                         'sender'    : sender,
                         'recipient' : recipient,
                         'zsig'      : zsig,  # logged here but not used by app
                         'new_zephyr': body }
            else:
                zeph = { 'type'      : 'class',
                         'time'      : str(notice.time),
                         'sender'    : sender,
                         'class'     : notice.cls,
                         'instance'  : notice.instance,
                         'zsig'      : zsig,  # logged here but not used by app
                         'new_zephyr': body }

            log.write(simplejson.dumps(zeph) + '\n')
            log.flush()

            print "received a message on %s/%s from %s..." % \
                (notice.cls, notice.instance, notice.sender)
            send_humbug(zeph)
        except:
            print >>sys.stderr, 'Error relaying zephyr'
            traceback.print_exc()
            time.sleep(2)


def zephyr_to_humbug(options):
    browser_login()

    import mit_subs_list
    subs = zephyr.Subscriptions()
    if options.forward_class_messages:
        for sub in mit_subs_list.all_subs:
            subs.add((sub, '*', '*'))
    if options.forward_personals:
        subs.add(("message", "personal", "*"))

    if options.resend_log:
        with open('zephyrs', 'r') as log:
            for ln in log:
                try:
                    zeph = simplejson.loads(ln)
                    print "sending saved message to %s from %s..." % \
                        (zeph.get('class', zeph.get('recipient')), zeph['sender'])
                    send_humbug(zeph)
                except:
                    print >>sys.stderr, 'Could not send saved zephyr'
                    traceback.print_exc()
                    time.sleep(2)

    print "Starting receive loop"

    with open('zephyrs', 'a') as log:
        process_loop(log)

def get_zephyrs(last_received):
        browser.addheaders.append(('X-CSRFToken', csrf_token))
        submit_hash = {'last_received': last_received,
                       "mit_sync_bot": 'yes'}
        submit_data = urllib.urlencode([(k, v.encode('utf-8')) for k,v in submit_hash.items()])
        res = browser.open("https://app.humbughq.com/get_updates_longpoll", submit_data)
        return simplejson.loads(res.read())['zephyrs']


def send_zephyr(message):
    zsig = "`Timothy G. Abbott`"
    if message['type'] == "class":
        zeph = zephyr.ZNotice(sender=message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                              auth=True, cls="tabbott-test4",
                              instance=message["display_recipient"] + "/" + message["instance"])
        body = "%s\0%s" % (zsig, message['content'])
    elif message['type'] == "personal":
        zeph = zephyr.ZNotice(sender=message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                              auth=True, cls="tabbott-test4",
                              instance=message["display_recipient"])
        body = "%s\0%s" % (zsig, message['content'])
    elif message['type'] == "huddle":
        # TODO: This needs to send one message to each person, I think
        zeph = zephyr.ZNotice(sender=message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                              auth=True, cls="tabbott-test4",
                              instance="huddle!")
        cc_list = ["CC:"]
        cc_list.extend([user["email"].replace("@mit.edu", "")
                        for user in message["display_recipient"]])
        body = "%s\0%s\n%s" % (zsig, " ".join(cc_list), message['content'])
    zeph.setmessage(body)
    zeph.send()

def humbug_to_zephyr(options):
    # Sync messages from zephyr to humbug
    browser_login()
    print "Starting get_updates_longpoll."
    zephyrs = get_zephyrs('0')
    while True:
        last_received = str(max([z["id"] for z in zephyrs]))
        new_zephyrs = get_zephyrs(last_received)
        for zephyr in new_zephyrs:
            print zephyr
            if zephyr["sender_email"] == os.environ["USER"] + "@mit.edu":
                send_zephyr(zephyr)
        zephyrs.extend(new_zephyrs)

if options.forward_to_humbug:
    zephyr_to_humbug(options)
else:
    humbug_to_zephyr(options)


from django import forms

class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    short_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, max_length=100)

subs_lists = {}
subs_lists['default'] = """\
""".split()

all_subs = set()
for sub_list in subs_lists.values():
    for sub in sub_list:
        all_subs.add(sub)

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import render
from django.utils.timezone import utc

from django.contrib.auth.models import User
from zephyr.models import Zephyr, UserProfile, ZephyrClass, Subscription, \
    Recipient, get_display_recipient, get_huddle, Realm, UserMessage, \
    create_user, do_send_zephyr, mit_sync_table
from zephyr.forms import RegistrationForm

from zephyr.decorator import asynchronous

import datetime
import simplejson
import socket
import re
import hashlib

def require_post(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if request.method != "POST":
            return HttpResponseBadRequest('This form can only be submitted by POST.')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

def json_response(res_type="success", msg="", data={}, status=200):
    content = {"result":res_type, "msg":msg}
    content.update(data)
    return HttpResponse(content=simplejson.dumps(content),
                        mimetype='application/json', status=status)

def json_success(data={}):
    return json_response(data=data)

def json_error(msg, data={}):
    return json_response(res_type="error", msg=msg, data=data, status=400)

def strip_html(x):
    """Sanitize an email, class name, etc."""
    # We remove <> in order to avoid </script> within JSON embedded in HTML.
    #
    # FIXME: consider a whitelist
    return x.replace('<','&lt;').replace('>','&gt;')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email      = strip_html(request.POST['email'])
            password   = request.POST['password']
            full_name  = strip_html(request.POST['full_name'])
            short_name = strip_html(request.POST['short_name'])
            email      = strip_html(request.POST['email'])
            domain     = strip_html(request.POST['domain'])
            realm = Realm.objects.filter(domain=domain)
            if not realm:
                realm = Realm(domain=domain)
                realm.save()
            else:
                realm = Realm.objects.get(domain=domain)
            # FIXME: sanitize email addresses
            create_user(email, password, realm, full_name, short_name)
            login(request, authenticate(username=email, password=password))
            return HttpResponseRedirect(reverse('zephyr.views.home'))
    else:
        form = RegistrationForm()

    return render(request, 'zephyr/register.html', {
        'form': form,
    })

def accounts_home(request):
    return render_to_response('zephyr/accounts_home.html',
                              context_instance=RequestContext(request))

def home(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('accounts/home/')
    user_profile = UserProfile.objects.get(user=request.user)

    zephyrs = Zephyr.objects.filter(usermessage__user_profile=user_profile)

    if user_profile.pointer == -1 and zephyrs:
        user_profile.pointer = min([zephyr.id for zephyr in zephyrs])
        user_profile.save()

    zephyr_json = simplejson.dumps([zephyr.to_dict() for zephyr in zephyrs])

    # Populate personals autocomplete list based on everyone in your
    # realm.  Later we might want a 2-layer autocomplete, where we
    # consider specially some sort of "buddy list" who e.g. you've
    # talked to before, but for small organizations, the right list is
    # everyone in your realm.
    people = [profile.user.email for profile in
              UserProfile.objects.filter(realm=user_profile.realm) if
              profile != user_profile]

    subscriptions = Subscription.objects.filter(userprofile_id=user_profile, active=True)
    classes = [get_display_recipient(sub.recipient) for sub in subscriptions
               if sub.recipient.type == Recipient.CLASS]

    class_zephyrs = Zephyr.objects.filter(
        usermessage__user_profile = user_profile,
        recipient__type = Recipient.CLASS)

    instances = list(set(zephyr.instance for zephyr in class_zephyrs))

    return render_to_response('zephyr/index.html',
                              {'zephyr_array' : zephyr_json,
                               'user_profile': user_profile,
                               'email_hash'  : hashlib.md5(settings.HASH_SALT + user_profile.user.email).hexdigest(),
                               'people'      : simplejson.dumps(people),
                               'classes'     : simplejson.dumps(classes),
                               'instances'   : simplejson.dumps(instances),
                               'show_debug':
                                   settings.DEBUG and ('show_debug' in request.GET) },
                              context_instance=RequestContext(request))

@login_required
@require_post
def update(request):
    user_profile = UserProfile.objects.get(user=request.user)
    pointer = request.POST.get('pointer')
    if not pointer:
        return json_error("Missing pointer")

    try:
        pointer = int(pointer)
    except ValueError:
        return json_error("Invalid pointer: must be an integer")

    if pointer < 0:
        return json_error("Invalid pointer value")

    user_profile.pointer = pointer
    user_profile.save()
    return json_success()

@login_required
@asynchronous
@require_post
def get_updates_longpoll(request, handler):
    last_received = request.POST.get('last_received')
    if not last_received:
        return json_error("Missing last_received argument")
    user_profile = UserProfile.objects.get(user=request.user)

    def on_receive(zephyrs):
        if handler.request.connection.stream.closed():
            return
        try:
            # Avoid message loop by not sending the MIT sync bot any
            # messages that we got from it in the first place.
            if request.POST.get('mit_sync_bot'):
                zephyrs = [zephyr for zephyr in zephyrs if not mit_sync_table.get(zephyr.id)]
            handler.finish({'zephyrs': [zephyr.to_dict() for zephyr in zephyrs]})
        except socket.error:
            pass

    # We need to replace this abstraction with the message list
    user_profile.add_callback(handler.async_callback(on_receive), last_received)

@login_required
@require_post
def zephyr(request):
    if 'time' in request.POST:
        return json_error("Invalid field 'time'")
    return zephyr_backend(request, request.user)

@login_required
@require_post
def forge_zephyr(request):
    email = strip_html(request.POST['sender']).lower()
    user_profile = UserProfile.objects.get(user=request.user)

    if "time" not in request.POST:
        return json_error("Missing time")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # forge a user for this person
        create_user(email, "test", user_profile.realm,
                    strip_html(request.POST['fullname']),
                    strip_html(request.POST['shortname']))
        user = User.objects.get(email=email)

    if (request.POST['type'] == 'personal' and ',' in request.POST['recipient']):
        # Huddle message, need to make sure we're not syncing it twice!
        if Zephyr.objects.filter(sender__user__email=email,
                                 content=request.POST['new_zephyr'],
                                 pub_date__gt=datetime.datetime.utcfromtimestamp(float(request.POST['time']) - 1).replace(tzinfo=utc),
                                 pub_date__lt=datetime.datetime.utcfromtimestamp(float(request.POST['time']) + 1).replace(tzinfo=utc)):
            # This is a duplicate huddle message, deduplicate!
            return json_success()

        # Now confirm all the other recipients exist in our system
        for user_email in request.POST["recipient"].split(","):
            try:
                User.objects.get(email=user_email)
            except User.DoesNotExist:
                # forge a user for this person
                create_user(user_email, "test", user_profile.realm,
                            user_email.split('@')[0],
                            user_email.split('@')[0])

    return zephyr_backend(request, user)

@login_required
@require_post
def zephyr_backend(request, sender):
    user_profile = UserProfile.objects.get(user=request.user)
    if "type" not in request.POST:
        return json_error("Missing type")
    if "new_zephyr" not in request.POST:
        return json_error("Missing message contents")

    zephyr_type_name = request.POST["type"]
    if zephyr_type_name == 'class':
        if "class" not in request.POST or not request.POST["class"]:
            return json_error("Missing class")
        if "instance" not in request.POST:
            return json_error("Missing instance")

        class_name = strip_html(request.POST['class']).strip()
        my_classes = ZephyrClass.objects.filter(name=class_name, realm=user_profile.realm)
        if my_classes:
            my_class = my_classes[0]
        else:
            my_class = ZephyrClass()
            my_class.name = class_name
            my_class.realm = user_profile.realm
            my_class.save()
            recipient = Recipient(type_id=my_class.id, type=Recipient.CLASS)
            recipient.save()
        try:
            recipient = Recipient.objects.get(type_id=my_class.id, type=Recipient.CLASS)
        except Recipient.DoesNotExist:
            return json_error("Invalid class")
    elif zephyr_type_name == 'personal':
        if "recipient" not in request.POST:
            return json_error("Missing recipient")

        recipient_data = strip_html(request.POST['recipient'])
        if ',' in recipient_data:
            # This is actually a huddle message, which shares the
            # "personal" zephyr sending form
            recipients = [r.strip() for r in recipient_data.split(',')]
            # Ignore any blank recipients
            recipients = [r for r in recipients if r]
            recipient_ids = []
            for recipient in recipients:
                try:
                    recipient_ids.append(
                        UserProfile.objects.get(user=User.objects.get(email=recipient)).id)
                except User.DoesNotExist:
                    return json_error("Invalid email '%s'" % (recipient))
            # Make sure the sender is included in the huddle
            recipient_ids.append(UserProfile.objects.get(user=request.user).id)
            huddle = get_huddle(recipient_ids)
            recipient = Recipient.objects.get(type_id=huddle.id, type=Recipient.HUDDLE)
        else:
            # This is actually a personal message
            if not User.objects.filter(email=recipient_data):
                return json_error("Invalid email")

            recipient_user = User.objects.get(email=recipient_data)
            recipient_user_profile = UserProfile.objects.get(user=recipient_user)
            recipient = Recipient.objects.get(type_id=recipient_user_profile.id,
                                              type=Recipient.PERSONAL)
    else:
        return json_error("Invalid zephyr type")

    new_zephyr = Zephyr()
    new_zephyr.sender = UserProfile.objects.get(user=sender)
    new_zephyr.content = strip_html(request.POST['new_zephyr'])
    new_zephyr.recipient = recipient
    if zephyr_type_name == 'class':
        new_zephyr.instance = strip_html(request.POST['instance'])
    if 'time' in request.POST:
        # Forged zephyrs come with a timestamp
        new_zephyr.pub_date = datetime.datetime.utcfromtimestamp(float(request.POST['time'])).replace(tzinfo=utc)
    else:
        new_zephyr.pub_date = datetime.datetime.utcnow().replace(tzinfo=utc)

    # To avoid message loops, we must pass whether the message was
    # synced from MIT zephyr here.
    do_send_zephyr(new_zephyr, synced_from_mit = 'time' in request.POST)

    return json_success()

def gather_subscriptions(user_profile):
    subscriptions = Subscription.objects.filter(userprofile=user_profile, active=True)
    # For now, don't display the subscription for your ability to receive personals.
    return sorted([get_display_recipient(sub.recipient) for sub in subscriptions
            if sub.recipient.type == Recipient.CLASS])

@login_required
def subscriptions(request):
    user_profile = UserProfile.objects.get(user=request.user)

    return render_to_response('zephyr/subscriptions.html',
                              {'subscriptions': gather_subscriptions(user_profile),
                               'user_profile': user_profile},
                              context_instance=RequestContext(request))

@login_required
def json_list_subscriptions(request):
    subs = gather_subscriptions(UserProfile.objects.get(user=request.user))
    return HttpResponse(content=simplejson.dumps({"subscriptions": subs}),
                        mimetype='application/json', status=200)

@login_required
@require_post
def json_remove_subscription(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if 'subscription' not in request.POST:
        return json_error("Missing subscriptions")

    sub_name = request.POST.get('subscription')
    zephyr_class = ZephyrClass.objects.get(name=sub_name, realm=user_profile.realm)
    recipient = Recipient.objects.get(type_id=zephyr_class.id,
                                      type=Recipient.CLASS)
    subscription = Subscription.objects.get(
        userprofile=user_profile, recipient=recipient)
    subscription.active = False
    subscription.save()

    return json_success({"data": sub_name})

@login_required
@require_post
def json_add_subscription(request):
    user_profile = UserProfile.objects.get(user=request.user)

    if "new_subscription" not in request.POST:
        return HttpResponseRedirect(reverse('zephyr.views.subscriptions'))

    sub_name = request.POST.get('new_subscription').strip()
    if not re.match('^[a-z A-z0-9_-]+$', sub_name):
        return json_error("Invalid characters in class names")

    zephyr_class = ZephyrClass.objects.filter(name=sub_name, realm=user_profile.realm)
    if zephyr_class:
        zephyr_class = zephyr_class[0]
        recipient = Recipient.objects.get(type_id=zephyr_class.id,
                                          type=Recipient.CLASS)
    else:
        (_, recipient) = ZephyrClass.create(sub_name, user_profile.realm)

    subscription = Subscription.objects.filter(userprofile=user_profile,
                                               recipient=recipient)
    if subscription:
        subscription = subscription[0]
        if not subscription.active:
            # Activating old subscription.
            subscription.active = True
            subscription.save()
            actually_new_sub = sub_name
        else:
            # Subscription already exists and is active
            return json_error("Subscription already exists")
    else:
        new_subscription = Subscription(userprofile=user_profile,
                                            recipient=recipient)
        new_subscription.save()
        actually_new_sub = sub_name
    return json_success({"data": actually_new_sub})


@login_required
def manage_settings(request):
    user_profile = UserProfile.objects.get(user=request.user)

    return render_to_response('zephyr/settings.html',
                              {'user_profile': user_profile,
                               'gravatar_hash': hashlib.md5(settings.MD5_SALT + user_profile.user.email).hexdigest(),
                               },
                              context_instance=RequestContext(request))

@login_required
@require_post
def change_settings(request):
    user_profile = UserProfile.objects.get(user=request.user)

    # First validate all the inputs
    if "full_name" not in request.POST:
        return json_error("Invalid settings request -- missing full_name.")
    if "short_name" not in request.POST:
        return json_error("Invalid settings request -- missing short_name.")
    if "timezone" not in request.POST:
        return json_error("Invalid settings request -- missing timezone.")
    if "new_password" not in request.POST:
        return json_error("Invalid settings request -- missing new_password.")
    if "old_password" not in request.POST:
        return json_error("Invalid settings request -- missing old_password.")
    if "confirm_password" not in request.POST:
        return json_error("Invalid settings request -- missing confirm_password.")

    old_password     = request.POST['old_password']
    new_password     = request.POST['new_password']
    confirm_password = request.POST['confirm_password']
    full_name        = strip_html(request.POST['full_name'])
    short_name       = strip_html(request.POST['short_name'])
    timezone         = strip_html(request.POST['timezone'])

    if new_password != "":
        if new_password != confirm_password:
            return json_error("New password must match confirmation password!")
        if not authenticate(username=user_profile.user.email, password=old_password):
            return json_error("Wrong password!")
        user_profile.user.set_password(new_password)

    result = {}
    if user_profile.full_name != full_name:
        user_profile.full_name = full_name
        result['full_name'] = full_name
    if user_profile.short_name != short_name:
        user_profile.short_name = short_name
        result['short_name'] = short_name
    # TODO: Change the timezone
    # user_profile.timezone = timezone
    user_profile.user.save()
    user_profile.save()

    return json_success(result)

@login_required
def class_exists(request, zephyr_class):
    return HttpResponse(bool(ZephyrClass.objects.filter(name=zephyr_class)))


from django.core.management.base import NoArgsCommand

from django.contrib.auth.models import User
from zephyr.models import Zephyr, UserProfile, ZephyrClass, Recipient
from django.contrib.sessions.models import Session

class Command(NoArgsCommand):
    help = "Clear only tables we change: zephyr + sessions"

    def handle_noargs(self, **options):
        for klass in [Zephyr, ZephyrClass, UserProfile, User, Recipient]:
            klass.objects.all().delete()
        Session.objects.all().delete()

        self.stdout.write("Successfully cleared the database.\n")


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

    def handle(self, *addrport, **options):
        # setup unbuffered I/O
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
        sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

        if len(addrport) == 0:
            self.run_one(**options)
        elif len(addrport) == 1:
            self.run_one(addrport[0], **options)
        else:
            from multiprocessing import Process

            plist = []
            for ap in addrport:
                p = Process(target=self.run_one, args=(ap,), kwargs=options)
                p.start()
                plist.append(p)

            while plist:
                if plist[0].exitcode is None:
                    plist.pop(0)
                else:
                    plist[0].join()

    def run_one(self, addrport, **options):
        import django
        from django.core.handlers.wsgi import WSGIHandler
        from tornado import httpserver, wsgi, ioloop, web

        if not addrport:
            addr = ''
            port = '8000'
        else:
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

            from tornado.web import FallbackHandler
            django_app = wsgi.WSGIContainer(WSGIHandler())

            try:
                # Application is an instance of Django's standard wsgi handler.
                application = web.Application([(r"/get_updates_longpoll", AsyncDjangoHandler),
                                               (r".*", FallbackHandler, dict(fallback=django_app)),
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

            # Apply response middleware
            for middleware_method in self._response_middleware:
                response = middleware_method(request, response)
            response = self.apply_response_fixes(request, response)
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
                for middleware_method in self._view_middleware:
                    response = middleware_method(request, callback, callback_args, callback_kwargs)
                    if response:
                        break

                from ...decorator import TornadoAsyncException

                try:
                    response = callback(request, *callback_args, **callback_kwargs)
                except TornadoAsyncException, e:
                    # TODO: Maybe add debugging output here
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

from django.core.management.base import BaseCommand
from django.utils.timezone import utc

from django.contrib.auth.models import User
from zephyr.models import Zephyr, UserProfile, ZephyrClass, Recipient, \
    Subscription, Huddle, get_huddle, Realm, UserMessage, get_user_profile_by_id, \
    create_user, do_send_zephyr
from zephyr.lib.parallel import run_parallel
from django.db import transaction
from django.conf import settings
from zephyr import mit_subs_list

import datetime
import random
import hashlib
from optparse import make_option

def create_users(name_list):
    for name, email in name_list:
        (short_name, domain) = email.split("@")
        password = short_name
        if User.objects.filter(email=email):
            # We're trying to create the same user twice!
            raise
        realm = Realm.objects.get(domain=domain)
        create_user(email, password, realm, name, short_name)

def create_classes(class_list, realm):
    for name in class_list:
        if ZephyrClass.objects.filter(name=name, realm=realm):
            # We're trying to create the same zephyr class twice!
            raise
        ZephyrClass.create(name, realm)

class Command(BaseCommand):
    help = "Populate a test database"

    option_list = BaseCommand.option_list + (
        make_option('-n', '--num-zephyrs',
                    dest='num_zephyrs',
                    type='int',
                    default=600,
                    help='The number of zephyrs to create.'),
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

        )

    def handle(self, **options):
        if options["percent_huddles"] + options["percent_personals"] > 100:
            self.stderr.write("Error!  More than 100% of messages allocated.\n")
            return

        class_list = ["Verona", "Denmark", "Scotland", "Venice", "Rome"]

        if options["delete"]:
            for klass in [Zephyr, ZephyrClass, UserProfile, User, Recipient,
                          Realm, Subscription, Huddle, UserMessage]:
                klass.objects.all().delete()

            # Create a test realm
            humbug_realm = Realm(domain="humbughq.com")
            humbug_realm.save()

            # Create test Users (UserProfiles are automatically created,
            # as are subscriptions to the ability to receive personals).
            names = [("Othello, the Moor of Venice", "othello@humbughq.com"), ("Iago", "iago@humbughq.com"),
                     ("Prospero from The Tempest", "prospero@humbughq.com"),
                     ("Cordelia Lear", "cordelia@humbughq.com"), ("King Hamlet", "hamlet@humbughq.com")]
            for i in xrange(options["extra_users"]):
                names.append(('Extra User %d' % (i,), 'extrauser%d' % (i,)))

            create_users(names)

            # Create public classes.
            create_classes(class_list, humbug_realm)
            recipient_classes = [klass.type_id for klass in
                                 Recipient.objects.filter(type=Recipient.CLASS)]

            # Create subscriptions to classes
            profiles = UserProfile.objects.all()
            for i, profile in enumerate(profiles):
                # Subscribe to some classes.
                for recipient in recipient_classes[:int(len(recipient_classes) *
                                                        float(i)/len(profiles)) + 1]:
                    r = Recipient.objects.get(type=Recipient.CLASS, type_id=recipient)
                    new_subscription = Subscription(userprofile=profile,
                                                    recipient=r)
                    new_subscription.save()
        else:
            humbug_realm = Realm.objects.get(domain="humbughq.com")
            recipient_classes = [klass.type_id for klass in
                                 Recipient.objects.filter(type=Recipient.CLASS)]

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
            count = options["num_zephyrs"] / threads
            if i < options["num_zephyrs"] % threads:
                count += 1
            jobs.append((count, personals_pairs, options, self.stdout.write))
        for status, job in run_parallel(send_zephyrs, jobs, threads=threads):
            pass

        if options["delete"]:
            mit_realm = Realm(domain="mit.edu")
            mit_realm.save()

            # Create internal users
            internal_mit_users = []
            create_users(internal_mit_users)

            create_classes(mit_subs_list.all_subs, mit_realm)

            # Now subscribe everyone to these classes
            profiles = UserProfile.objects.filter(realm=mit_realm)
            for cls in mit_subs_list.all_subs:
                zephyr_class = ZephyrClass.objects.get(name=cls, realm=mit_realm)
                recipient = Recipient.objects.get(type=Recipient.CLASS, type_id=zephyr_class.id)
                for i, profile in enumerate(profiles):
                    if profile.user.email in mit_subs_list.subs_lists:
                        key = profile.user.email
                    else:
                        key = "default"
                    if cls in mit_subs_list.subs_lists[key]:
                        new_subscription = Subscription(userprofile=profile, recipient=recipient)
                        new_subscription.save()

            internal_humbug_users = []
            create_users(internal_humbug_users)
            humbug_class_list = ["devel", "all", "humbug", "design", "support"]
            create_classes(humbug_class_list, humbug_realm)

            # Now subscribe everyone to these classes
            profiles = UserProfile.objects.filter(realm=humbug_realm)
            for cls in humbug_class_list:
                zephyr_class = ZephyrClass.objects.get(name=cls, realm=humbug_realm)
                recipient = Recipient.objects.get(type=Recipient.CLASS, type_id=zephyr_class.id)
                for i, profile in enumerate(profiles):
                    # Subscribe to some classes.
                    new_subscription = Subscription(userprofile=profile, recipient=recipient)
                    new_subscription.save()

            self.stdout.write("Successfully populated test database.\n")

recipient_hash = {}
def get_recipient_by_id(rid):
    if rid in recipient_hash:
        return recipient_hash[rid]
    return Recipient.objects.get(id=rid)

# Create some test zephyrs, including:
# - multiple classes
# - multiple instances per class
# - multiple huddles
# - multiple personals converastions
# - multiple zephyrs per instance
# - both single and multi-line content
def send_zephyrs(data):
    (tot_zephyrs, personals_pairs, options, output) = data
    from django.db import connection
    connection.close()
    texts = file("zephyr/management/commands/test_zephyrs.txt", "r").readlines()
    offset = 0

    recipient_classes = [klass.id for klass in
                         Recipient.objects.filter(type=Recipient.CLASS)]
    recipient_huddles = [h.id for h in Recipient.objects.filter(type=Recipient.HUDDLE)]

    huddle_members = {}
    for h in recipient_huddles:
        huddle_members[h] = [s.userprofile.id for s in
                             Subscription.objects.filter(recipient_id=h)]

    num_zephyrs = 0
    random_max = 1000000
    recipients = {}
    while num_zephyrs < tot_zephyrs:
      with transaction.commit_on_success():
        saved_data = ''
        new_zephyr = Zephyr()
        length = random.randint(1, 5)
        lines = (t.strip() for t in texts[offset: offset + length])
        new_zephyr.content = '\n'.join(lines)
        offset += length
        offset = offset % len(texts)

        randkey = random.randint(1, random_max)
        if (num_zephyrs > 0 and
            random.randint(1, random_max) * 100. / random_max < options["stickyness"]):
            # Use an old recipient
            zephyr_type, recipient_id, saved_data = recipients[num_zephyrs - 1]
            if zephyr_type == Recipient.PERSONAL:
                personals_pair = saved_data
                random.shuffle(personals_pair)
            elif zephyr_type == Recipient.CLASS:
                new_zephyr.instance = saved_data
                new_zephyr.recipient = get_recipient_by_id(recipient_id)
            elif zephyr_type == Recipient.HUDDLE:
                new_zephyr.recipient = get_recipient_by_id(recipient_id)
        elif (randkey <= random_max * options["percent_huddles"] / 100.):
            zephyr_type = Recipient.HUDDLE
            new_zephyr.recipient = get_recipient_by_id(random.choice(recipient_huddles))
        elif (randkey <= random_max * (options["percent_huddles"] + options["percent_personals"]) / 100.):
            zephyr_type = Recipient.PERSONAL
            personals_pair = random.choice(personals_pairs)
            random.shuffle(personals_pair)
        elif (randkey <= random_max * 1.0):
            zephyr_type = Recipient.CLASS
            new_zephyr.recipient = get_recipient_by_id(random.choice(recipient_classes))

        if zephyr_type == Recipient.HUDDLE:
            sender_id = random.choice(huddle_members[new_zephyr.recipient.id])
            new_zephyr.sender = get_user_profile_by_id(sender_id)
        elif zephyr_type == Recipient.PERSONAL:
            new_zephyr.recipient = Recipient.objects.get(type=Recipient.PERSONAL,
                                                         type_id=personals_pair[0])
            new_zephyr.sender = get_user_profile_by_id(personals_pair[1])
            saved_data = personals_pair
        elif zephyr_type == Recipient.CLASS:
            zephyr_class = ZephyrClass.objects.get(id=new_zephyr.recipient.type_id)
            # Pick a random subscriber to the class
            new_zephyr.sender = random.choice(Subscription.objects.filter(
                    recipient=new_zephyr.recipient)).userprofile
            new_zephyr.instance = zephyr_class.name + str(random.randint(1, 3))
            saved_data = new_zephyr.instance

        new_zephyr.pub_date = datetime.datetime.utcnow().replace(tzinfo=utc)
        do_send_zephyr(new_zephyr)

        recipients[num_zephyrs] = [zephyr_type, new_zephyr.recipient.id, saved_data]
        num_zephyrs += 1
    return tot_zephyrs

import django.core.cache

def cache_with_key(keyfunc):
    """Decorator which applies Django caching to a function.

       Decorator argument is a function which computes a cache key
       from the original function's arguments.  You are responsible
       for avoiding collisions with other uses of this decorator or
       other uses of caching."""

    def decorator(func):
        djcache = django.core.cache.cache

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

    def keyfunc(*args, **kwargs):
        # Django complains about spaces because memcached rejects them
        key = func_uniqifier + repr((args, kwargs))
        return key.replace('-','--').replace(' ','-s')

    return cache_with_key(keyfunc)(func)


import os
import signal
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
    import random
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



from sqlalchemy import create_engine
engine = create_engine('sqlite:////tmp/humbug.db', echo=False)
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    realm_id = Column(Integer)
    email = Column(String)
    password = Column(String) # obviously going to be replaced with Django stuff here

    def __init__(self, username, realm_id, email, password):
        self.username = username
        self.email = email
        self.realm_id = realm_id
        self.password = password

    def __repr__(self):
       return "<User('%s','%s', '%s', '%s')>" % (self.username, self.email, self.realm_id, self.password)

class Stream(Base):
    __tablename__ = 'streams'

    id = Column(Integer, primary_key=True)
    realm_id = Column(Integer, ForeignKey('realms.id'))
    name = Column(String)

    def __init__(self, realm_id, name):
        self.realm_id = realm_id
        self.name = name

    def __repr__(self):
        # In theory this should maybe look up the realm name
        return "<Stream('%s', '%s')>" % (self.realm_id, self.name)

class Recipient(Base):
    __tablename__ = 'recipients'

    id = Column(Integer, primary_key=True)
    # type is either "user" or "stream"
    type = Column(String)
    # type_id is a foreign key into either the streams or users table,
    # as determined by the "type" field
    type_id = Column(Integer) 

    def __init__(self, type, type_id):
        self.type = type
        self.type_id = type_id

    def __repr__(self):
        # In theory this should maybe lookup the names for the IDs
        return "<Recipient('%s','%s')>" % (self.type, self.type_id)

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    recipient_id = Column(Integer, ForeignKey('recipients.id'))

    def __init__(self, user_id, recipient_id):
        self.user_id = user_id
        self.recipient_id = recipient_id

    def __repr__(self):
        # In theory this should maybe lookup the names for the IDs
        return "<Subscription('%s','%s')>" % (self.user_id, self.recipient_id)

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    # message_id is NOT unique -- it can be repeated with multi-recipient personals
    message_id = Column(Integer) 
    sender_id = Column(Integer, ForeignKey('users.id'))
    recipient_id = Column(Integer, ForeignKey('recipients.id'))
    thread = Column(String)
    content = Column(String) # Maybe should change this to an ID
    time = Column(Integer) # Should use a real datetime thingy here

    def __init__(self, message_id, sender_id, recipient_id, thread, time, content):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.thread = thread
        self.time = time
        self.content = content
        self.message_id = message_id

    def __repr__(self):
        return "<Message('%s', '%s', '%s', '%s', '%s', '%s')>" % \
            (self.message_id, self.sender_id, self.recipient_id, self.thread, self.time, self.content)

class UserMessage(Base):
    __tablename__ = 'user_messages'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id'), primary_key=True)
    # Maybe add an "archived" bit later

    def __init__(self, user_id, message_id):
        self.user_id = user_id
        self.message_id = message_id

    def __repr__(self):
        # Ideally this should lookup the name for at least the user ID
        return "<User Received Message('%s','%s')>" % (self.user_id, self.message_id)

class Realm(Base):
    __tablename__ = 'realms'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    domain = Column(String)

    def __init__(self, name, domain):
        self.name = name
        self.domain = domain

    def __repr__(self):
        # Ideally this should lookup the name for at least the user ID
        return "<Realm('%s','%s')>" % (self.name, self.domain)

Base.metadata.create_all(engine) 
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

if __name__ == "__main__":
    jeff = User(username="Jeff", realm_id=1, email="sipbexch@mit.edu", password="blank")
    tim = User(username="Tim", realm_id=1, email="starnine@mit.edu", password="blank")

    m = Message(sender_id=jeff.id, recipient_id=tim.id, 
                thread="personnel", time=1, content="We rock!", message_id=1)
    session.add(jeff)
    session.add(tim)
    session.add(m)
    print session.query(Message).filter_by(sender_id=jeff.id).first()
    session.commit()

#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "humbug.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


# Django settings for humbug project.
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

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
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

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

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

ACCOUNT_ACTIVATION_DAYS=7
EMAIL_HOST='localhost'
EMAIL_PORT=9991
EMAIL_HOST_USER='username'
EMAIL_HOST_PASSWORD='password'

LOGIN_REDIRECT_URL='/'

from django.conf import settings
from django.conf.urls import patterns, include, url
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
    url(r'^subscriptions/$', 'zephyr.views.subscriptions', name='subscriptions'),
    url(r'^subscriptions/manage/$', 'zephyr.views.manage_subscriptions', name='manage_subscriptions'),
    url(r'^subscriptions/add/$', 'zephyr.views.add_subscriptions', name='add_subscriptions'),
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
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.signals import post_save
import hashlib

def get_display_recipient(recipient):
    """
    recipient: an instance of Recipient.

    returns: an appropriate string describing the recipient (the class
    name, for a class, or the username, for a user).
    """
    if recipient.type == "class":
        zephyr_class = ZephyrClass.objects.get(pk=recipient.type_id)
        return zephyr_class.name
    elif recipient.type == "huddle":
        user_list = [UserProfile.objects.get(user=s.userprofile) for s in
                     Subscription.objects.filter(recipient=recipient)]
        return [{'name': user.user.username} for user in user_list]
    else:
        user = User.objects.get(pk=recipient.type_id)
        return user.username

callback_table = {}

class Realm(models.Model):
    domain = models.CharField(max_length=40)

    def __repr__(self):
        return "<Realm: %s %s>" % (self.domain, self.id)
    def __str__(self):
        return self.__repr__()

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    pointer = models.IntegerField()
    realm = models.ForeignKey(Realm)

    # The user receives this message
    def receive(self, message):
        global callback_table

        # Should also store in permanent database the receipt
        for cb in callback_table.get(self.user.id, []):
            cb([message])

        callback_table[self.user.id] = []

    def add_callback(self, cb, last_received):
        global callback_table

        new_zephyrs = filter_by_subscriptions(
                Zephyr.objects.filter(id__gt=last_received), self.user)

        if new_zephyrs:
            return cb(new_zephyrs)
        callback_table.setdefault(self.user.id, []).append(cb)

    def __repr__(self):
        return "<UserProfile: %s %s>" % (self.user.username, self.realm)
    def __str__(self):
        return self.__repr__()

def create_user_profile(user, realm):
    """When creating a new user, make a profile for him or her."""
    if not UserProfile.objects.filter(user=user):
        profile = UserProfile(user=user, pointer=-1, realm_id=realm.id)
        profile.save()
        # Auto-sub to the ability to receive personals.
        recipient = Recipient(type_id=profile.pk, type="personal")
        recipient.save()
        Subscription(userprofile=profile, recipient=recipient).save()

class ZephyrClass(models.Model):
    name = models.CharField(max_length=30)
    realm = models.ForeignKey(Realm)

    def __repr__(self):
        return "<ZephyrClass: %s>" % (self.name,)

class Recipient(models.Model):
    type_id = models.IntegerField()
    type = models.CharField(max_length=30)
    # Valid types are {personal, class, huddle}

    def __repr__(self):
        display_recipient = get_display_recipient(self)
        return "<Recipient: %s (%d, %s)>" % (display_recipient, self.type_id, self.type)

class Zephyr(models.Model):
    sender = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    instance = models.CharField(max_length=30)
    content = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def __repr__(self):
        display_recipient = get_display_recipient(self.recipient)
        return "<Zephyr: %s / %s / %r>" % (display_recipient, self.instance, self.sender)

    def to_dict(self):
        return {'id'               : self.id,
                'sender'           : self.sender.user.username,
                'type'             : self.recipient.type,
                'display_recipient': get_display_recipient(self.recipient),
                'instance'         : self.instance,
                'content'          : self.content }

def send_zephyr(**kwargs):
    zephyr = kwargs["instance"]
    if zephyr.recipient.type == "personal":
        recipients = UserProfile.objects.filter(Q(user=zephyr.recipient.type_id) | Q(user=zephyr.sender))
        # For personals, you send out either 1 or 2 copies of the zephyr, for
        # personals to yourself or to someone else, respectively.
        assert((len(recipients) == 1) or (len(recipients) == 2))
    elif zephyr.recipient.type == "class" or zephyr.recipient.type == "huddle":
        recipients = [UserProfile.objects.get(user=s.userprofile) for
                      s in Subscription.objects.filter(recipient=zephyr.recipient, active=True)]
    else:
        raise
    for recipient in recipients:
        recipient.receive(zephyr)

post_save.connect(send_zephyr, sender=Zephyr)

class Subscription(models.Model):
    userprofile = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    active = models.BooleanField(default=True)

    def __repr__(self):
        return "<Subscription: %r -> %r>" % (self.userprofile, self.recipient)

class Huddle(models.Model):
    huddle_hash = models.CharField(max_length=40)

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
        recipient = Recipient(type_id=huddle.pk, type="huddle")
        recipient.save()

        # Add subscriptions
        for uid in id_list:
            s = Subscription(recipient = recipient,
                             userprofile = UserProfile.objects.get(id=uid))
            s.save()
        return huddle

def filter_by_subscriptions(zephyrs, user):
    userprofile = UserProfile.objects.get(user=user)
    subscribed_zephyrs = []
    subscriptions = [sub.recipient for sub in Subscription.objects.filter(userprofile=userprofile, active=True)]
    for zephyr in zephyrs:
        # If you are subscribed to the personal or class, or if you sent the personal, you can see the zephyr.
        if (zephyr.recipient in subscriptions) or \
                (zephyr.recipient.type == "personal" and zephyr.sender == userprofile):
            subscribed_zephyrs.append(zephyr)

    return subscribed_zephyrs

import tornado.web
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
import re
import urllib

import sys, logging
logger = logging.getLogger("mechanize")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

def browser_login(br):
    br.set_handle_robots(False)
    ## debugging code to consider
    # br.set_debug_http(True)
    # br.set_debug_responses(True)
    # br.set_debug_redirects(True)
    # br.set_handle_refresh(False)
    br.add_password("https://app.humbughq.com/", "tabbott", "xxxxxxxxxxxxxxxxx", "wiki")
    login_info = urllib.urlencode([('username', 'iago'), ('password', 'iago')])
    response = br.open("https://app.humbughq.com/")
    br.follow_link(text_regex="\s*Log in\s*")
    br.select_form(nr=0)
    br["username"] = "iago"
    br["password"] = "iago"
    response2 = br.submit()
    # This is a horrible horrible hack
    data = "".join(response2.readlines())
    val = data.index("csrfmiddlewaretoken")
    csrf = data[val+28:val+60]
    return csrf

# example: send_zephyr("Verona", "Auto2", "test")
def send_zephyr(sender, klass, instance, content):
    br = mechanize.Browser()
    hack_content = "Message from MIT Zephyr sender %s\n" % (sender,) + content
    csrf = browser_login(br)
    br.addheaders.append(('X-CSRFToken', csrf))
    zephyr_data = urllib.urlencode([('type', 'class'), ('class', klass),
                                    ('instance', instance), ('new_zephyr', hack_content)])
    br.open("https://app.humbughq.com/zephyr/", zephyr_data)

import zephyr
subs = zephyr.Subscriptions()
subs.add(('tabbott-test2', '*', '*'))

while True:
    notice = zephyr.receive(block=True)
    [zsig, body] = notice.message.split("\x00")
    send_zephyr(notice.sender, notice.cls, notice.instance, body)

from django import forms

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, max_length=100)

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import render
from django.utils.timezone import utc

from django.contrib.auth.models import User
from zephyr.models import Zephyr, UserProfile, ZephyrClass, Subscription, \
    Recipient, filter_by_subscriptions, get_display_recipient, get_huddle, \
    create_user_profile, Realm
from zephyr.forms import RegistrationForm

import tornado.web
from zephyr.decorator import asynchronous

import datetime
import simplejson
import socket

def require_post(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if request.method != "POST":
            return HttpResponseBadRequest('This form can only be submitted by POST.')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

def json_response(res_type="success", msg="", status=200):
    return HttpResponse(content=simplejson.dumps({"result":res_type, "msg":msg}),
                        mimetype='application/json', status=status)

def json_success():
    return json_response()

def json_error(msg):
    return json_response(res_type="error", msg=msg, status=400)

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            domain = request.POST['domain']
            realm = Realm.objects.filter(domain=domain)
            if not realm:
                realm = Realm(domain=domain)
            else:
                realm = Realm.objects.get(domain=domain)
            user = User.objects.create_user(username=username, password=password)
            user.save()
            create_user_profile(user, realm)
            login(request, authenticate(username=username, password=password))
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

    zephyrs = filter_by_subscriptions(Zephyr.objects.all(), request.user)

    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if user_profile.pointer == -1 and zephyrs:
        user_profile.pointer = min([zephyr.id for zephyr in zephyrs])
        user_profile.save()
    zephyr_json = simplejson.dumps([zephyr.to_dict() for zephyr in zephyrs])

    personals = filter_by_subscriptions(Zephyr.objects.filter(
        recipient__type="personal").all(), request.user)
    people = simplejson.dumps(list(
            set(get_display_recipient(zephyr.recipient) for zephyr in personals)))

    publics = filter_by_subscriptions(Zephyr.objects.filter(
        recipient__type="class").all(), request.user)

    subscriptions = Subscription.objects.filter(userprofile_id=user_profile, active=True)
    classes = simplejson.dumps([get_display_recipient(sub.recipient) for sub in subscriptions
                                     if sub.recipient.type == "class"])

    instances = simplejson.dumps(list(
            set(zephyr.instance for zephyr in publics)))

    return render_to_response('zephyr/index.html',
                              {'zephyr_json' : zephyr_json,
                               'user_profile': user_profile,
                               'people'      : people,
                               'classes'     : classes,
                               'instances'   : instances},
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

@asynchronous
@require_post
def get_updates_longpoll(request, handler):
    last_received = request.POST.get('last_received')
    if not last_received:
        # TODO: return error?
        pass

    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    def on_receive(zephyrs):
        if handler.request.connection.stream.closed():
            return
        try:
            handler.finish({'zephyrs': [zephyr.to_dict() for zephyr in zephyrs]})
        except socket.error, e:
            pass

    # We need to replace this abstraction with the message list
    user_profile.add_callback(handler.async_callback(on_receive), last_received)

@login_required
@require_post
def zephyr(request):
    return zephyr_backend(request, request.user)

@login_required
@require_post
def forge_zephyr(request):
    username = request.POST['sender']
    user_profile = UserProfile.objects.get(user=request.user)
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # forge a user for this person
        user = User.objects.create_user(username=username, password="test")
        user.save()
        create_user_profile(user, user_profile.realm)
    return zephyr_backend(request, user)

@login_required
@require_post
def zephyr_backend(request, sender):
    user_profile = UserProfile.objects.get(user=request.user)
    zephyr_type = request.POST["type"]
    if zephyr_type == 'class':
        class_name = request.POST['class']
        if ZephyrClass.objects.filter(name=class_name, realm=user_profile.realm):
            my_class = ZephyrClass.objects.get(name=class_name, realm=user_profile.realm)
        else:
            my_class = ZephyrClass()
            my_class.name = class_name
            my_class.realm = user_profile.realm
            my_class.save()
            recipient = Recipient(type_id=my_class.id, type="class")
            recipient.save()
        try:
            recipient = Recipient.objects.get(type_id=my_class.id, type="class")
        except Recipient.DoesNotExist:
            return json_error("Invalid class")
    elif zephyr_type == "personal":
        recipient_data = request.POST['recipient']
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
                        UserProfile.objects.get(user=User.objects.get(username=recipient)).id)
                except User.DoesNotExist, e:
                    return json_error("Invalid username '%s'" % (recipient))
            # Make sure the sender is included in the huddle
            recipient_ids.append(UserProfile.objects.get(user=request.user).id)
            huddle = get_huddle(recipient_ids)
            recipient = Recipient.objects.get(type_id=huddle.pk, type="huddle")
        else:
            # This is actually a personal message
            if not User.objects.filter(username=recipient_data):
                return json_error("Invalid username")

            recipient_user = User.objects.get(username=recipient_data)
            recipient_user_profile = UserProfile.objects.get(user=recipient_user)
            recipient = Recipient.objects.get(type_id=recipient_user_profile.id, type="personal")
    else:
        return json_error("Invalid zephyr type")

    new_zephyr = Zephyr()
    new_zephyr.sender = UserProfile.objects.get(user=sender)
    new_zephyr.content = request.POST['new_zephyr']
    new_zephyr.recipient = recipient
    if zephyr_type == "class":
        new_zephyr.instance = request.POST['instance']
    new_zephyr.pub_date = datetime.datetime.utcnow().replace(tzinfo=utc)
    new_zephyr.save()

    return json_success()

@login_required
def subscriptions(request):
    userprofile = UserProfile.objects.get(user=request.user)
    subscriptions = Subscription.objects.filter(userprofile=userprofile, active=True)
    # For now, don't display the subscription for your ability to receive personals.
    sub_names = [get_display_recipient(sub.recipient) for sub in subscriptions
                 if sub.recipient.type == "class"]

    return render_to_response('zephyr/subscriptions.html',
                              {'subscriptions': sub_names, 'user_profile': userprofile},
                              context_instance=RequestContext(request))

@login_required
def manage_subscriptions(request):
    if not request.POST:
        # Do something reasonable.
        return
    user_profile = UserProfile.objects.get(user=request.user)

    unsubs = request.POST.getlist('subscription')
    for sub_name in unsubs:
        zephyr_class = ZephyrClass.objects.get(name=sub_name, realm=user_profile.realm)
        recipient = Recipient.objects.get(type_id=zephyr_class.id, type="class")
        subscription = Subscription.objects.get(
            userprofile=user_profile, recipient=recipient)
        subscription.active = False
        subscription.save()

    return HttpResponseRedirect(reverse('zephyr.views.subscriptions'))

@login_required
def add_subscriptions(request):
    if not request.POST:
        # Do something reasonable.
        return
    user_profile = UserProfile.objects.get(user=request.user)

    new_subs = request.POST.get('new_subscriptions')
    if not new_subs:
        return HttpResponseRedirect(reverse('zephyr.views.subscriptions'))

    for sub_name in new_subs.split(","):
        zephyr_class = ZephyrClass.objects.filter(name=sub_name, realm=user_profile.realm)
        if zephyr_class:
            zephyr_class = zephyr_class[0]
        else:
            zephyr_class = ZephyrClass(name=sub_name, realm=user_profile.realm)
            zephyr_class.save()

        recipient = Recipient.objects.filter(type_id=zephyr_class.pk, type="class")
        if recipient:
            recipient = recipient[0]
        else:
            recipient = Recipient(type_id=zephyr_class.pk, type="class")
        recipient.save()

        subscription = Subscription.objects.filter(userprofile=user_profile,
                                                   recipient=recipient)
        if subscription:
            subscription = subscription[0]
            subscription.active = True
            subscription.save()
        else:
            new_subscription = Subscription(userprofile=user_profile,
                                            recipient=recipient)
            new_subscription.save()

    return HttpResponseRedirect(reverse('zephyr.views.subscriptions'))

@login_required
def class_exists(request, zephyr_class):
    return HttpResponse(bool(ZephyrClass.objects.filter(name=zephyr_class)))


from django.core.management.base import NoArgsCommand

from django.contrib.auth.models import User
from zephyr.models import Zephyr, UserProfile, ZephyrClass, Recipient, Subscription
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
            import logging
            logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(levelname)-8s %(message)s')
            logger = logging.getLogger()

        def inner_run():
            from django.conf import settings
            from django.utils import translation
            translation.activate(settings.LANGUAGE_CODE)

            print "Validating Django models.py..."
            self.validate(display_num_errors=True)
            print "\nDjango version %s" % (django.get_version())
            print "Tornado server is running at http://%s:%s/" % (addr, port)
            print "Quit the server with %s." % quit_command

            from tornado.web import FallbackHandler, StaticFileHandler
            django_app = wsgi.WSGIContainer(WSGIHandler())

            try:
                # Application is an instance of Django's standard wsgi handler.
                application = web.Application([(r"/get_updates_longpoll", AsyncDjangoHandler),
                                               (r".*", FallbackHandler, dict(fallback=django_app)),
                                               ])

                # start tornado web server in single-threaded mode
                http_server = httpserver.HTTPServer(application,
                                                    xheaders=xheaders,
                                                    no_keep_alive=no_keep_alive)
                http_server.listen(int(port), address=addr)

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

    def prepare(func):
        """Patches the Cookie header in the Tornado request to fulfull
        Django's strict string-type cookie policy"""
        def inner_func(self,**kwargs):
            if u'Cookie' in self.request.headers:
                raw_cookie = self.request.headers[u'Cookie']
                if isinstance(raw_cookie, unicode):
                    if hasattr(escape, "native_str"):
                        self.request.headers[u'Cookie'] = escape.native_str(raw_cookie)
                    else:
                        print "Method 'native_str' in module 'escape' not found."
                        self.request.headers[u'Cookie'] = str(raw_cookie)
            return func(self)
        return inner_func

    def get(self):
        from tornado.wsgi import HTTPRequest, WSGIContainer
        from django.core.handlers.wsgi import WSGIRequest, STATUS_CODE_TEXT
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

        status_text = STATUS_CODE_TEXT.get(response.status_code, "UNKNOWN")
        status = '%s (%s)' % (response.status_code, status_text)

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
                            receivers = signals.got_request_exception.send(sender=self.__class__, request=request)
            except exceptions.PermissionDenied:
                logger.warning(
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
                receivers = signals.got_request_exception.send(sender=self.__class__, request=request)
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
    Subscription, Huddle, get_huddle, Realm, create_user_profile

import datetime
import random
from optparse import make_option

class Command(BaseCommand):
    help = "Populate a test database"

    option_list = BaseCommand.option_list + (
        make_option('-n', '--num-zephyrs',
                    dest='num_zephyrs',
                    type='int',
                    default=120,
                    help='The number of zephyrs to create.'),
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
        )

    def handle(self, **options):
        if options["percent_huddles"] + options["percent_personals"] > 100:
            self.stderr.write("Error!  More than 100% of messages allocated.\n")
            return

        for klass in [Zephyr, ZephyrClass, UserProfile, User, Recipient,
                      Realm, Subscription, Huddle]:
            klass.objects.all().delete()

        # Create a test realm
        realm = Realm(domain="humbughq.com")
        realm.save()

        # Create test Users (UserProfiles are automatically created,
        # as are subscriptions to the ability to receive personals).
        usernames = ["othello", "iago", "prospero", "cordelia", "hamlet"]
        for username in usernames:
            user = User.objects.create_user(username=username, password=username)
            user.save()
            create_user_profile(user, realm)
        users = [user.id for user in User.objects.all()]

        # Create public classes.
        for name in ["Verona", "Denmark", "Scotland", "Venice", "Rome"]:
            new_class = ZephyrClass(name=name, realm=realm)
            new_class.save()

            recipient = Recipient(type_id=new_class.pk, type="class")
            recipient.save()

        # Create several initial huddles
        huddle_members = {}
        for i in range(0, options["num_huddles"]):
            user_ids = random.sample(users, random.randint(3, 4))
            huddle_members[get_huddle(user_ids).id] = user_ids

        # Create several initial pairs for personals
        personals_pairs = []
        for i in range(0, options["num_personals"]):
            personals_pairs.append(random.sample(users, 2))

        recipient_classes = [klass.type_id for klass in Recipient.objects.filter(type="class")]
        recipient_huddles = [h.type_id for h in Recipient.objects.filter(type="huddle")]

        # Create subscriptions to classes
        profiles = UserProfile.objects.all()
        for i, profile in enumerate(profiles):
            # Subscribe to some classes.
            for recipient in recipient_classes[:int(len(recipient_classes) * float(i)/len(profiles)) + 1]:
                new_subscription = Subscription(userprofile=profile,
                                                recipient=Recipient.objects.get(type="class",
                                                                                type_id=recipient))
                new_subscription.save()

        # Create some test zephyrs, including:
        # - multiple classes
        # - multiple instances per class
        # - multiple zephyrs per instance
        # - both single and multi-line content

        texts = file("zephyr/management/commands/test_zephyrs.txt", "r").readlines()
        offset = 0
        num_zephyrs = 0
        random_max = 1000000
        recipients = {}
        while num_zephyrs < options["num_zephyrs"]:
            saved_data = ''
            new_zephyr = Zephyr()
            length = random.randint(1, 5)
            new_zephyr.content = "".join(texts[offset: offset + length])
            offset += length
            offset = offset % len(texts)

            randkey = random.randint(1, random_max)
            if (num_zephyrs > 0 and
                random.randint(1, random_max) * 100. / random_max < options["stickyness"]):
                # Use an old recipient
                zephyr_type, recipient, saved_data = recipients[num_zephyrs - 1]
                if zephyr_type == "personal":
                    personals_pair = saved_data
                    random.shuffle(personals_pair)
                elif zephyr_type == "class":
                    new_zephyr.instance = saved_data
                    new_zephyr.recipient = recipient
                elif zephyr_type == "huddle":
                    new_zephyr.recipient = recipient
            elif (randkey <= random_max * options["percent_huddles"] / 100.):
                zephyr_type = "huddle"
                new_zephyr.recipient = Recipient.objects.get(type="huddle", type_id=random.choice(recipient_huddles))
            elif (randkey <= random_max * (options["percent_huddles"] + options["percent_personals"]) / 100.):
                zephyr_type = "personal"
                personals_pair = random.choice(personals_pairs)
                random.shuffle(personals_pair)
            elif (randkey <= random_max * 1.0):
                zephyr_type = "class"
                new_zephyr.recipient = Recipient.objects.get(type="class", type_id=random.choice(recipient_classes))

            if zephyr_type == "huddle":
                new_zephyr.sender = UserProfile.objects.get(id=random.choice(huddle_members[new_zephyr.recipient.type_id]))
            elif zephyr_type == "personal":
                new_zephyr.recipient = Recipient.objects.get(type="personal", type_id=personals_pair[0])
                new_zephyr.sender = UserProfile.objects.get(id=personals_pair[1])
                saved_data = personals_pair
            elif zephyr_type == "class":
                zephyr_class = ZephyrClass.objects.get(pk=new_zephyr.recipient.type_id)
                # Pick a random subscriber to the class
                new_zephyr.sender = random.choice(Subscription.objects.filter(recipient=new_zephyr.recipient)).userprofile
                new_zephyr.instance = zephyr_class.name + str(random.randint(1, 3))
                saved_data = new_zephyr.instance

            new_zephyr.pub_date = datetime.datetime.utcnow().replace(tzinfo=utc)
            new_zephyr.save()

            recipients[num_zephyrs] = [zephyr_type, new_zephyr.recipient, saved_data]
            num_zephyrs += 1

        self.stdout.write("Successfully populated test database.\n")


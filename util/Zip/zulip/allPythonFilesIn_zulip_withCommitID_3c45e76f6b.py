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

from django.conf import settings
from django.conf.urls import patterns, url
import os.path

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'zephyr.views.home', name='home'),
    # We have two entries for accounts/login to allow reverses on the Django
    # view we're wrapping to continue to function.
    url(r'^accounts/login/', 'zephyr.views.login_page', {'template_name': 'zephyr/login.html'}),
    url(r'^accounts/login/', 'django.contrib.auth.views.login', {'template_name': 'zephyr/login.html'}),
    url(r'^accounts/logout/', 'django.contrib.auth.views.logout', {'template_name': 'zephyr/index.html'}),

    # These are json format views used by the web client.  They require a logged in browser.
    url(r'^json/update_pointer$', 'zephyr.views.json_update_pointer', name='json_update_pointer'),
    url(r'^json/get_updates$', 'zephyr.views.json_get_updates', name='json_get_updates'),
    url(r'^json/send_message/', 'zephyr.views.json_send_message', name='json_send_message'),
    url(r'^json/settings/change/$', 'zephyr.views.json_change_settings', name='json_change_settings'),
    url(r'^json/subscriptions/list$', 'zephyr.views.json_list_subscriptions', name='json_list_subscriptions'),
    url(r'^json/subscriptions/remove$', 'zephyr.views.json_remove_subscription', name='json_remove_subscription'),
    url(r'^json/subscriptions/add$', 'zephyr.views.json_add_subscription', name='json_add_subscription'),
    url(r'^json/subscriptions/exists/(?P<stream>.*)$', 'zephyr.views.json_stream_exists', name='json_stream_exists'),

    # These are json format views used by the API.  They require an API key.
    url(r'^api/v1/get_messages$', 'zephyr.views.api_get_messages', name='api_get_messages'),
    url(r'^api/v1/get_public_streams$', 'zephyr.views.api_get_public_streams', name='api_get_public_streams'),
    url(r'^api/v1/get_subscriptions$', 'zephyr.views.api_get_subscriptions', name='api_get_subscriptions'),
    url(r'^api/v1/subscribe$', 'zephyr.views.api_subscribe', name='api_subscribe'),
    url(r'^api/v1/send_message$', 'zephyr.views.api_send_message', name='api_send_message'),

    url(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/static/favicon.ico'}),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(settings.SITE_ROOT, '..', 'zephyr', 'static/')}),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

if settings.ALLOW_REGISTER:
    urlpatterns += patterns('',
        url(r'^accounts/home/', 'zephyr.views.accounts_home', name='accounts_home'),
        url(r'^accounts/register/', 'zephyr.views.accounts_register', name='accounts_register'),
        url(r'^accounts/send_confirm/(?P<email>[\S]+)?', 'django.views.generic.simple.direct_to_template', {'template': 'zephyr/accounts_send_confirm.html'}, name='send_confirm'),
        url(r'^accounts/do_confirm/(?P<confirmation_key>[\w]+)', 'confirmation.views.confirm', name='confirm'),
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

# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: models.py 28 2009-10-22 15:03:02Z jarek.zgoda $'

import os
import re
import datetime
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
        confirmation_key = sha1(str(os.urandom(12)) + str(email_address)).hexdigest()
        current_site = Site.objects.get_current()
        activate_url = u'http://%s%s' % (current_site.domain,
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
        return self.create(content_object=obj, date_sent=datetime.datetime.now(), confirmation_key=confirmation_key)


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

from setuptools import setup, find_packages

# Dynamically calculate the version based on confirmation.VERSION.                                                          
version_tuple = __import__('confirmation').VERSION
if version_tuple[2] is not None:
    version = "%d.%d_%s" % version_tuple
else:
    version = "%d.%d" % version_tuple[:2]


setup(
    name = 'django-confirmation',
    version = version,
    description = 'Generic object confirmation for Django',
    author = 'Jarek Zgoda',
    author_email = 'jarek.zgoda@gmail.com',
    url = 'http://code.google.com/p/django-confirmation/',
    license = 'New BSD License',
    packages = find_packages(),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
    zip_safe = False,
    install_requires = [
        'django>=1.0',
    ],
)


# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: admin.py 3 2008-11-18 07:33:52Z jarek.zgoda $'


from django.contrib import admin

from confirmation.models import Confirmation


admin.site.register(Confirmation)
# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: settings.py 12 2008-11-23 19:38:52Z jarek.zgoda $'

STATUS_ACTIVE = 1

STATUS_FIELDS = {
}

# -*- coding: utf-8 -*-

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: urls.py 3 2008-11-18 07:33:52Z jarek.zgoda $'


from django.conf.urls.defaults import *

from confirmation.views import confirm


urlpatterns = patterns('',
    (r'^(?P<confirmation_key>\w+)/$', confirm),
)
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

# Copyright: (c) 2008, Jarek Zgoda <jarek.zgoda@gmail.com>

__revision__ = '$Id: cleanupconfirmation.py 5 2008-11-18 09:10:12Z jarek.zgoda $'


from django.core.management.base import NoArgsCommand

from confirmation.models import Confirmation


class Command(NoArgsCommand):
    help = 'Delete expired confirmations from database'

    def handle_noargs(self, **options):
        Confirmation.objects.delete_expired_confirmations()

#!/usr/bin/python
import urllib
import sys
import logging
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
from urllib2 import HTTPError

root_path = "/mit/tabbott/for_friends"
sys.path.append(root_path + "/python-zephyr")
sys.path.append(root_path + "/python-zephyr/build/lib.linux-x86_64-2.6/")

parser = optparse.OptionParser()
parser.add_option('--forward-class-messages',
                  dest='forward_class_messages',
                  default=False,
                  action='store_true')
parser.add_option('--resend-log',
                  dest='resend_log',
                  default=False,
                  action='store_true')
parser.add_option('--enable-log',
                  dest='enable_log',
                  default=False,
                  action='store_true')
parser.add_option('--no-forward-personals',
                  dest='forward_personals',
                  default=True,
                  action='store_false')
parser.add_option('--forward-from-humbug',
                  dest='forward_from_humbug',
                  default=False,
                  action='store_true')
parser.add_option('--verbose',
                  dest='verbose',
                  default=False,
                  action='store_true')
parser.add_option('--no-auto-subscribe',
                  dest='auto_subscribe',
                  default=True,
                  action='store_false')
parser.add_option('--site',
                  dest='site',
                  default="https://app.humbughq.com",
                  action='store')
parser.add_option('--api-key',
                  dest='api_key',
                  default="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                  action='store')
(options, args) = parser.parse_args()

sys.path.append(".")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import api.common
humbug_client = api.common.HumbugAPI(email=os.environ["USER"] + "@mit.edu",
                                     api_key=options.api_key,
                                     verbose=True,
                                     site=options.site)

start_time = time.time()

def humbug_username(zephyr_username):
    return zephyr_username.lower().split("@")[0] + "@mit.edu"

def send_humbug(zeph):
    zeph["forged"] = "yes"
    zeph["sender"] = humbug_username(zeph["sender"])
    zeph['fullname']  = username_to_fullname(zeph['sender'])
    zeph['shortname'] = zeph['sender'].split('@')[0]
    if "subject" in zeph:
        zeph["subject"] = zeph["subject"][:60]
    if zeph['type'] == 'stream':
        # Forward messages sent to -c foo -i bar to stream bar subject "instance"
        if zeph["stream"] == "message":
            zeph['stream'] = zeph['subject']
            zeph['subject'] = "instance %s" % (zeph['stream'])
        elif zeph["stream"] == "tabbott-test5":
            zeph['stream'] = zeph['subject']
            zeph['subject'] = "test instance %s" % (zeph['stream'])

    for key in zeph.keys():
        if isinstance(zeph[key], unicode):
            zeph[key] = zeph[key].encode("utf-8")
        elif isinstance(zeph[key], str):
            zeph[key] = zeph[key].decode("utf-8")

    return humbug_client.send_message(zeph)

def fetch_fullname(username):
    try:
        match_user = re.match(r'([a-zA-Z0-9_]+)@mit\.edu', username)
        if match_user:
            proc = subprocess.Popen(['hesinfo', match_user.group(1), 'passwd'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            out, _err_unused = proc.communicate()
            if proc.returncode == 0:
                return out.split(':')[4].split(',')[0]
    except:
        print >>sys.stderr, '%s: zephyr=>humbug: Error getting fullname for %s' % \
            (datetime.datetime.now(), username)
        traceback.print_exc()

    domains = [
        ("@CS.CMU.EDU", " (CMU)"),
        ("@ANDREW.CMU.EDU", " (CMU)"),
        ("@IASTATE.EDU", " (IASTATE)"),
        ("@1TS.ORG", " (1TS)"),
        ("@DEMENTIA.ORG", " (DEMENTIA)"),
        ("@MIT.EDU", ""),
        ]
    for (domain, tag) in domains:
        if username.upper().endswith(domain):
            return username.split("@")[0] + tag
    return username

fullnames = {}
def username_to_fullname(username):
    if username not in fullnames:
        fullnames[username] = fetch_fullname(username)
    return fullnames[username]

current_zephyr_subs = {}
def ensure_subscribed(sub):
    if sub in current_zephyr_subs:
        return
    subs.add((sub, '*', '*'))
    current_zephyr_subs[sub] = True

def update_subscriptions_from_humbug():
    try:
        res = humbug_client.get_public_streams()
        streams = res["streams"]
    except:
        print "%s: Error getting public streams:" % (datetime.datetime.now())
        traceback.print_exc()
        return
    for stream in streams:
        ensure_subscribed(stream)

def maybe_restart_mirroring_script():
    if os.stat(root_path + "/restart_stamp").st_mtime > start_time or \
            (os.environ["USER"] == "tabbott" and
             os.stat(root_path + "/tabbott_stamp").st_mtime > start_time):
        print
        print "%s: zephyr mirroring script has been updated; restarting..." % \
            (datetime.datetime.now())
        os.kill(child_pid, signal.SIGKILL)
        while True:
            try:
                os.execvp(root_path + "/zephyr_mirror.py", sys.argv)
            except:
                print "Error restarting, trying again."
                traceback.print_exc()
                time.sleep(10)

def process_loop(log):
    sleep_count = 0
    sleep_time = 0.1
    while True:
        notice = zephyr.receive(block=False)
        if notice is not None:
            try:
                process_notice(notice, log)
            except:
                print >>sys.stderr, '%s: zephyr=>humbug: Error relaying zephyr' % \
                    (datetime.datetime.now())
                traceback.print_exc()
                time.sleep(2)

        maybe_restart_mirroring_script()

        time.sleep(sleep_time)
        sleep_count += sleep_time
        if sleep_count > 15:
            sleep_count = 0
            if options.forward_class_messages:
                # Ask the Humbug server about any new classes to subscribe to
                update_subscriptions_from_humbug()
        continue

def process_notice(notice, log):
    zsig, body = notice.message.split("\x00", 1)
    is_personal = False
    is_huddle = False

    if notice.opcode == "PING":
        # skip PING messages
        return

    if isinstance(zsig, str):
        # Check for width unicode character u'\u200B'.encode("utf-8")
        if u'\u200B'.encode("utf-8") in zsig:
            print "%s: zephyr=>humbug: Skipping message from Humbug!" % \
                (datetime.datetime.now())
            return

    sender = notice.sender.lower().replace("athena.mit.edu", "mit.edu")
    recipient = notice.recipient.lower().replace("athena.mit.edu", "mit.edu")
    zephyr_class = notice.cls.lower()
    instance = notice.instance.lower()

    if (zephyr_class == "message" and recipient != ""):
        is_personal = True
        if body.startswith("CC:"):
            is_huddle = True
            # Map "CC: sipbtest espuser" => "starnine@mit.edu,espuser@mit.edu"
            huddle_recipients_list = [humbug_username(x.strip()) for x in
                                      body.split("\n")[0][4:].split()]
            if sender not in huddle_recipients_list:
                huddle_recipients_list.append(sender)
            huddle_recipients = ",".join(huddle_recipients_list)
    if (zephyr_class == "mail" and instance == "inbox"):
        is_personal = True

    # Drop messages not to the listed subscriptions
    if (zephyr_class not in current_zephyr_subs) and not \
            (is_personal and options.forward_personals):
        print "%s: zephyr=>humbug: Skipping ... %s/%s/%s" % \
            (datetime.datetime.now(), zephyr_class, instance, is_personal)
        return

    if is_huddle:
        zeph = { 'type'      : 'personal',
                 'time'      : str(notice.time),
                 'sender'    : sender,
                 'recipient' : huddle_recipients,
                 'zsig'      : zsig,  # logged here but not used by app
                 'content'   : body.split("\n", 1)[1] }
    elif is_personal:
        zeph = { 'type'      : 'personal',
                 'time'      : str(notice.time),
                 'sender'    : sender,
                 'recipient' : humbug_username(recipient),
                 'zsig'      : zsig,  # logged here but not used by app
                 'content'   : body }
    else:
        zeph = { 'type'      : 'stream',
                 'time'      : str(notice.time),
                 'sender'    : sender,
                 'stream'    : zephyr_class,
                 'subject'   : instance,
                 'zsig'      : zsig,  # logged here but not used by app
                 'content'   : body }

    # Add instances in for instanced personals
    if zeph['type'] == "personal" and instance != "personal":
        zeph["content"] = "[-i %s]" % (instance,) + "\n" + zeph["content"]

    print "%s: zephyr=>humbug: received a message on %s/%s from %s..." % \
        (datetime.datetime.now(), zephyr_class, instance, notice.sender)
    log.write(simplejson.dumps(zeph) + '\n')
    log.flush()

    res = send_humbug(zeph)
    if res.get("result") != "success":
        print >>sys.stderr, 'Error relaying zephyr'
        print zeph
        print res


def zephyr_to_humbug(options):
    import mit_subs_list
    if options.auto_subscribe:
        add_humbug_subscriptions()
    if options.forward_class_messages:
        for sub in mit_subs_list.all_subs:
            ensure_subscribed(sub)
        update_subscriptions_from_humbug()
    if options.forward_personals:
        subs.add(("message", "*", os.environ["USER"] + "@ATHENA.MIT.EDU"))
        if subscribed_to_mail_messages():
            subs.add(("mail", "inbox", os.environ["USER"] + "@ATHENA.MIT.EDU"))

    if options.resend_log:
        with open('zephyrs', 'r') as log:
            for ln in log:
                try:
                    zeph = simplejson.loads(ln)
                    print "%s: zephyr=>humbug: sending saved message to %s from %s..." % \
                        (datetime.datetime.now(), zeph.get('class', zeph.get('recipient')),
                         zeph['sender'])
                    send_humbug(zeph)
                except:
                    print >>sys.stderr, 'Could not send saved zephyr'
                    traceback.print_exc()
                    time.sleep(2)

    print "%s: zephyr=>humbug: Starting receive loop." % (datetime.datetime.now(),)

    if options.enable_log:
        log_file = "zephyrs"
    else:
        log_file = "/dev/null"

    with open(log_file, 'a') as log:
        process_loop(log)

def forward_to_zephyr(message):
    zsig = u"%s\u200B" % (username_to_fullname(message["sender_email"]))
    if ' dot ' in zsig:
        print "%s: humbug=>zephyr: ERROR!  Couldn't compute zsig for %s!" % \
            (datetime.datetime.now(), message["sender_email"])
        return

    wrapped_content = "\n".join("\n".join(textwrap.wrap(line))
            for line in message["content"].split("\n"))

    sender_email = message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU")
    print "%s: humbug=>zephyr: Forwarding message from %s" % \
        (datetime.datetime.now(), sender_email)
    if message['type'] == "stream":
        zephyr_class = message["display_recipient"]
        instance = message["subject"]
        if (instance == "instance %s" % (zephyr_class,) or
            instance == "test instance %s" % (zephyr_class,)):
            # Forward messages to e.g. -c -i white-magic back from the
            # place we forward them to
            if instance.startswith("test"):
                instance = zephyr_class
                zephyr_class = "tabbott-test5"
            else:
                instance = zephyr_class
                zephyr_class = "message"
        zeph = zephyr.ZNotice(sender=sender_email, auth=True,
                              cls=zephyr_class, instance=instance)
        body = "%s\0%s" % (zsig, wrapped_content)
        zeph.setmessage(body)
        zeph.send()
    elif message['type'] == "personal":
        recipient = message["display_recipient"]["email"]
        recipient = recipient.replace("@mit.edu", "@ATHENA.MIT.EDU")
        zeph = zephyr.ZNotice(sender=sender_email,
                              auth=True, recipient=recipient,
                              cls="message", instance="personal")
        body = "%s\0%s" % (zsig, wrapped_content)
        zeph.setmessage(body)
        zeph.send()
    elif message['type'] == "huddle":
        cc_list = ["CC:"]
        cc_list.extend([user["email"].replace("@mit.edu", "")
                        for user in message["display_recipient"]])
        body = "%s\0%s\n%s" % (zsig, " ".join(cc_list), wrapped_content)
        for r in message["display_recipient"]:
            recipient = r["email"].replace("mit.edu", "ATHENA.MIT.EDU")
            zeph = zephyr.ZNotice(sender=sender_email, auth=True,
                                  recipient=recipient, cls="message",
                                  instance="personal")
            zeph.setmessage(body)
            zeph.send()

def maybe_forward_to_zephyr(message):
    if message["sender_email"] == os.environ["USER"] + "@mit.edu":
        timestamp_now = datetime.datetime.now().strftime("%s")
        if float(message["timestamp"]) < float(timestamp_now) - 15:
            print "%s humbug=>zephyr: Alert!  Out of order message: %s < %s" % \
                (datetime.datetime.now(), message["timestamp"], timestamp_now)
            return
        forward_to_zephyr(message)

def humbug_to_zephyr(options):
    # Sync messages from zephyr to humbug
    print "%s: humbug=>zephyr: Starting syncing messages." % (datetime.datetime.now(),)
    humbug_client.call_on_each_message(maybe_forward_to_zephyr,
                                       options={"mit_sync_bot": 'yes'})

def subscribed_to_mail_messages():
    for (cls, instance, recipient) in parse_zephyr_subs(verbose=False):
        if (cls.lower() == "mail" and instance.lower() == "inbox"):
            return True
    return False

def add_humbug_subscriptions():
    zephyr_subscriptions = set()
    for (cls, instance, recipient) in parse_zephyr_subs(verbose=options.verbose):
        if cls == "message" and recipient == "*":
            if instance == "*":
                continue
            # If you're on -i white-magic on zephyr, get on stream white-magic on humbug
            # instead of subscribing to stream message
            zephyr_subscriptions.add(instance)
            continue
        elif instance != "*" or recipient != "*":
            if options.verbose:
                print "Skipping ~/.zephyr.subs line: [%s,%s,%s]: Non-* values" % \
                    (cls, instance, recipient)
            continue
        zephyr_subscriptions.add(cls)
    if len(zephyr_subscriptions) != 0:
        humbug_client.subscribe(list(zephyr_subscriptions))

def parse_zephyr_subs(verbose=False):
    if verbose:
        print "Adding your ~/.zephyr.subs subscriptions to Humbug!"
    zephyr_subscriptions = set()
    subs_file = os.path.join(os.environ["HOME"], ".zephyr.subs")
    if not os.path.exists(subs_file):
        if verbose:
            print >>sys.stderr, "Couldn't find .zephyr.subs!"
            print >>sys.stderr, "Do you mean to run with --no-auto-subscribe?"
            return

    for line in file(subs_file, "r").readlines():
        line = line.strip()
        if len(line) == 0:
            continue
        try:
            (cls, instance, recipient) = line.split(",")
        except:
            if verbose:
                print >>sys.stderr, "Couldn't parse ~/.zephyr.subs line: [%s]" % (line,)
            continue
        zephyr_subscriptions.add((cls.strip(), instance.strip(), recipient.strip()))
    return zephyr_subscriptions

if options.forward_from_humbug:
    print "This option is obsolete."
    sys.exit(0)

child_pid = os.fork()
if child_pid == 0:
    # Run the humbug => zephyr mirror in the child
    import zephyr
    zephyr.init()
    humbug_to_zephyr(options)
    sys.exit(0)

import zephyr
zephyr.init()
subs = zephyr.Subscriptions()
zephyr_to_humbug(options)


#!/usr/bin/python
import simplejson
import requests
import time
import traceback

# Check that we have a recent enough version
assert(requests.__version__ > '0.12')

class HumbugAPI():
    def __init__(self, email, api_key, verbose=False, site="https://app.humbughq.com"):
        self.api_key = api_key
        self.email = email
        self.verbose = verbose
        self.base_url = site

    def do_api_query(self, request, url):
        request["email"] = self.email
        request["api-key"] = self.api_key
        while True:
            try:
                res = requests.post(self.base_url + url,
                                    data=request,
                                    verify=True,
                                    auth=requests.auth.HTTPDigestAuth('tabbott',
                                                                      'xxxxxxxxxxxxxxxxx'))
                if res.status_code == requests.codes.service_unavailable:
                    # On 503 errors, try again after a short sleep
                    time.sleep(0.5)
                    continue
            except requests.exceptions.ConnectionError:
                return {'msg': "Connection error:\n%s" % traceback.format_exc(),
                        "result": "connection-error"}
            except Exception:
                # we'll split this out into more cases as we encounter new bugs.
                return {'msg': "Unexpected error:\n%s" % traceback.format_exc(),
                        "result": "unexpected-error"}

            if res.json is not None:
                return res.json
            return {'msg': res.text, "result": "http-error",
                    "status_code": res.status_code}

    def send_message(self, request):
        return self.do_api_query(request, "/api/v1/send_message")

    def get_messages(self, request = {}):
        return self.do_api_query(request, "/api/v1/get_messages")

    def get_public_streams(self, request = {}):
        return self.do_api_query(request, "/api/v1/get_public_streams")

    def get_subscriptions(self, request = {}):
        return self.do_api_query(request, "/api/v1/get_subscriptions")

    def subscribe(self, streams):
        request = {}
        request["streams"] = simplejson.dumps(streams)
        return self.do_api_query(request, "/api/v1/subscribe")

    def call_on_each_message(self, callback, options = {}):
        max_message_id = None
        while True:
            if max_message_id is not None:
                options["first"] = "0"
                options["last"] = str(max_message_id)
            res = self.get_messages(options)
            if 'error' in res.get('result'):
                if self.verbose:
                    if res["result"] == "http-error":
                        print "Unexpected error -- probably a server restart"
                    elif res["result"] == "connection-error":
                        print "Connection error -- probably server is temporarily down?"
                    else:
                        print "Server returned error:\n%s" % res["msg"]
                # TODO: Make this back off once it's more reliable
                time.sleep(1)
                continue
            for message in sorted(res['messages'], key=lambda x: int(x["id"])):
                max_message_id = max(max_message_id, int(message["id"]))
                callback(message)

subs_lists = {}
subs_lists['default'] = """\
""".split()

all_subs = set()
for sub_list in subs_lists.values():
    for sub in sub_list:
        all_subs.add(sub)

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import hashlib
import base64
import calendar
from zephyr.lib.cache import cache_with_key
import fcntl
import os
import simplejson
from django.db import transaction
from zephyr.lib import bugdown
from zephyr.lib.avatar import gravatar_hash

@cache_with_key(lambda self: 'display_recipient_dict:%d' % (self.id))
def get_display_recipient(recipient):
    """
    recipient: an subject of Recipient.

    returns: an appropriate string describing the recipient (the stream
    name, for a stream, or the email, for a user).
    """
    if recipient.type == Recipient.STREAM:
        stream = Stream.objects.get(id=recipient.type_id)
        return stream.name
    elif recipient.type == Recipient.HUDDLE:
        user_profile_list = [UserProfile.objects.select_related().get(user=s.userprofile) for s in
                             Subscription.objects.filter(recipient=recipient)]
        return [{'email': user_profile.user.email,
                 'full_name': user_profile.full_name,
                 'short_name': user_profile.short_name} for user_profile in user_profile_list]
    else:
        user_profile = UserProfile.objects.select_related().get(user=recipient.type_id)
        return {'email': user_profile.user.email,
                'full_name': user_profile.full_name,
                'short_name': user_profile.short_name}

def get_log_recipient(recipient):
    """
    recipient: an subject of Recipient.

    returns: an appropriate string describing the recipient (the stream
    name, for a stream, or the email, for a user).
    """
    if recipient.type == Recipient.STREAM:
        stream = Stream.objects.get(id=recipient.type_id)
        return stream.name

    user_profile_list = [UserProfile.objects.select_related().get(user=s.userprofile) for s in
                         Subscription.objects.filter(recipient=recipient)]
    return [{'email': user_profile.user.email,
             'full_name': user_profile.full_name,
             'short_name': user_profile.short_name} for user_profile in user_profile_list]

callback_table = {}
mit_sync_table = {}

class Realm(models.Model):
    domain = models.CharField(max_length=40, db_index=True)

    def __repr__(self):
        return "<Realm: %s %s>" % (self.domain, self.id)
    def __str__(self):
        return self.__repr__()

def gen_api_key():
    return 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
### TODO: For now, everyone has the same (fixed) API key to make
### testing easier.  Uncomment the following to generate them randomly
### in a reasonable way.  Long-term, we should use a real
### cryptographic random number generator.

#    return hex(random.getrandbits(4*32))[2:34]

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    full_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100)
    pointer = models.IntegerField()
    realm = models.ForeignKey(Realm)
    api_key = models.CharField(max_length=32)

    # The user receives this message
    def receive(self, message):
        global callback_table

        for cb in callback_table.get(self.user.id, []):
            cb([message])

        callback_table[self.user.id] = []

    def add_callback(self, cb):
        global callback_table
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
            profile.api_key = gen_api_key()
            profile.save()
            # Auto-sub to the ability to receive personals.
            recipient = Recipient(type_id=profile.id, type=Recipient.PERSONAL)
            recipient.save()
            Subscription(userprofile=profile, recipient=recipient).save()

class PreregistrationUser(models.Model):
    email = models.EmailField(unique=True)
    # 0 is inactive, 1 is active
    status = models.IntegerField(default=0)

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

def create_user_if_needed(realm, email, password, full_name, short_name):
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        # forge a user for this person
        create_user(email, password, realm,
                    full_name, short_name)
        user = User.objects.get(email=email)
        return user

def create_stream_if_needed(realm, stream_name):
    try:
        return Stream.objects.get(name__iexact=stream_name, realm=realm)
    except Stream.DoesNotExist:
        stream = Stream()
        stream.name = stream_name
        stream.realm = realm
        stream.save()
        recipient = Recipient(type_id=stream.id, type=Recipient.STREAM)
        recipient.save()
        return stream


class Stream(models.Model):
    name = models.CharField(max_length=30, db_index=True)
    realm = models.ForeignKey(Realm, db_index=True)

    def __repr__(self):
        return "<Stream: %s>" % (self.name,)
    def __str__(self):
        return self.__repr__()

    @classmethod
    def create(cls, name, realm):
        stream = cls(name=name, realm=realm)
        stream.save()

        recipient = Recipient(type_id=stream.id, type=Recipient.STREAM)
        recipient.save()
        return (stream, recipient)

class Recipient(models.Model):
    type_id = models.IntegerField(db_index=True)
    type = models.PositiveSmallIntegerField(db_index=True)
    # Valid types are {personal, stream, huddle}
    PERSONAL = 1
    STREAM = 2
    HUDDLE = 3

    def type_name(self):
        if self.type == self.PERSONAL:
            return "personal"
        elif self.type == self.STREAM:
            return "stream"
        elif self.type == self.HUDDLE:
            return "huddle"
        else:
            raise

    def __repr__(self):
        display_recipient = get_display_recipient(self)
        return "<Recipient: %s (%d, %s)>" % (display_recipient, self.type_id, self.type)

class Message(models.Model):
    sender = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    subject = models.CharField(max_length=60)
    content = models.TextField()
    pub_date = models.DateTimeField('date published')

    def __repr__(self):
        display_recipient = get_display_recipient(self.recipient)
        return "<Message: %s / %s / %r>" % (display_recipient, self.subject, self.sender)
    def __str__(self):
        return self.__repr__()

    @cache_with_key(lambda self, apply_markdown: 'message_dict:%d:%d' % (self.id, apply_markdown))
    def to_dict(self, apply_markdown):
        if apply_markdown:
            content = bugdown.convert(self.content)
        else:
            content = self.content
        return {'id'               : self.id,
                'sender_email'     : self.sender.user.email,
                'sender_full_name' : self.sender.full_name,
                'sender_short_name': self.sender.short_name,
                'type'             : self.recipient.type_name(),
                'display_recipient': get_display_recipient(self.recipient),
                'recipient_id'     : self.recipient.id,
                'subject'          : self.subject,
                'content'          : content,
                'timestamp'        : calendar.timegm(self.pub_date.timetuple()),
                'gravatar_hash'    : gravatar_hash(self.sender.user.email),
                }

    def to_log_dict(self):
        return {'id'               : self.id,
                'sender_email'     : self.sender.user.email,
                'sender_full_name' : self.sender.full_name,
                'sender_short_name': self.sender.short_name,
                'type'             : self.recipient.type_name(),
                'recipient'        : get_log_recipient(self.recipient),
                'subject'          : self.subject,
                'content'          : self.content,
                'timestamp'        : calendar.timegm(self.pub_date.timetuple()),
                }

class UserMessage(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    message = models.ForeignKey(Message)
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
    return UserProfile.objects.select_related().get(id=uid)

def log_message(message):
    if not os.path.exists(settings.MESSAGE_LOG + '.lock'):
        file(settings.MESSAGE_LOG + '.lock', "w").write("0")
    lock = open(settings.MESSAGE_LOG + '.lock', 'r')
    fcntl.flock(lock, fcntl.LOCK_EX)
    f = open(settings.MESSAGE_LOG, "a")
    f.write(simplejson.dumps(message.to_log_dict()) + "\n")
    f.flush()
    f.close()
    fcntl.flock(lock, fcntl.LOCK_UN)

def do_send_message(message, synced_from_mit=False, no_log=False):
    message.save()
    # The following mit_sync_table code must be after message.save() or
    # otherwise the id returned will be None (not having been assigned
    # by the database yet)
    mit_sync_table[message.id] = synced_from_mit
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
        recipients = [s.userprofile for
                      s in Subscription.objects.select_related().filter(recipient=message.recipient, active=True)]
    else:
        raise

    # Save the message receipts in the database
    with transaction.commit_on_success():
        for user_profile in recipients:
            UserMessage(user_profile=user_profile, message=message).save()

    for recipient in recipients:
        recipient.receive(message)

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
def filter_by_subscriptions(messages, user):
    userprofile = UserProfile.objects.get(user=user)
    user_messages = []
    subscriptions = [sub.recipient for sub in
                     Subscription.objects.filter(userprofile=userprofile, active=True)]
    for message in messages:
        # If you are subscribed to the personal or stream, or if you
        # sent the personal, you can see the message.
        if (message.recipient in subscriptions) or \
                (message.recipient.type == Recipient.PERSONAL and
                 message.sender == userprofile):
            user_messages.append(message)

    return user_messages

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


from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

def is_unique(value):
    try:
        User.objects.get(email=value)
        raise ValidationError(u'%s is already registered' % value)
    except User.DoesNotExist:
        pass

class UniqueEmailField(forms.EmailField):
    default_validators = [validators.validate_email, is_unique]

class RegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, max_length=100)
    domain = forms.CharField(max_length=100)

class HomepageForm(forms.Form):
    email = UniqueEmailField()

from django.conf import settings

def add_settings(context):
    return { 'full_navbar': settings.FULL_NAVBAR }

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import render
from django.utils.timezone import utc
from django.core.exceptions import ValidationError
from django.contrib.auth.views import login as django_login_page
from django.contrib.auth.models import User
from zephyr.models import Message, UserProfile, Stream, Subscription, \
    Recipient, get_display_recipient, get_huddle, Realm, UserMessage, \
    create_user, do_send_message, mit_sync_table, create_user_if_needed, \
    create_stream_if_needed, PreregistrationUser
from zephyr.forms import RegistrationForm, HomepageForm, is_unique
from django.views.decorators.csrf import csrf_exempt

from zephyr.decorator import asynchronous
from zephyr.lib.query import last_n
from zephyr.lib.avatar import gravatar_hash

from confirmation.models import Confirmation

import datetime
import simplejson
import socket
import re
import urllib
import time

SERVER_GENERATION = int(time.time())

def require_post(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if request.method != "POST":
            return HttpResponseBadRequest('This form can only be submitted by POST.')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

# api_key_required will add the authenticated user's user_profile to
# the view function's arguments list, since we have to look it up
# anyway.
def login_required_api_view(view_func):
    @csrf_exempt
    @require_post
    def _wrapped_view_func(request, *args, **kwargs):
        # Arguably @require_post should protect us from having to do
        # this, but I don't want to count on us always getting the
        # decorator ordering right.
        try:
            user_profile = UserProfile.objects.get(user__email=request.POST.get("email"))
        except UserProfile.DoesNotExist:
            return json_error("Invalid user")
        if user_profile is None or request.POST.get("api-key") != user_profile.api_key:
            return json_error('Invalid API user/key pair.')
        return view_func(request, user_profile, *args, **kwargs)
    return _wrapped_view_func

# Checks if the request is a POST request and that the user is logged
# in.  If not, return an error (the @login_required behavior of
# redirecting to a login page doesn't make sense for json views)
def login_required_json_view(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        # Arguably @require_post should protect us from having to do
        # this, but I don't want to count on us always getting the
        # decorator ordering right.
        if request.method != "POST":
            return HttpResponseBadRequest('This form can only be submitted by POST.')
        if not request.user.is_authenticated():
            return json_error("Not logged in")
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

def get_stream(stream_name, realm):
    stream = Stream.objects.filter(name__iexact=stream_name, realm=realm)
    if stream:
        return stream[0]
    else:
        return None

@require_post
def accounts_register(request):
    key = request.POST['key']
    email = Confirmation.objects.get(confirmation_key=key).content_object.email
    company_name = email.split('@')[-1]

    try:
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
            domain     = form.cleaned_data['domain']

            try:
                realm = Realm.objects.get(domain=domain)
            except Realm.DoesNotExist:
                realm = Realm(domain=domain)
                realm.save()

            # FIXME: sanitize email addresses
            create_user(email, password, realm, full_name, short_name)
            login(request, authenticate(username=email, password=password))
            return HttpResponseRedirect(reverse('zephyr.views.home'))

    return render_to_response('zephyr/register.html',
        { 'form': form, 'company_name': company_name, 'email': email, 'key': key },
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
    return render_to_response('zephyr/accounts_home.html',
                              context_instance=RequestContext(request))

def home(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse(settings.NOT_LOGGED_IN_REDIRECT))
    user_profile = UserProfile.objects.get(user=request.user)

    num_messages = UserMessage.objects.filter(user_profile=user_profile).count()

    if user_profile.pointer == -1 and num_messages > 0:
        min_id = UserMessage.objects.filter(user_profile=user_profile).order_by("message")[0].message_id
        user_profile.pointer = min_id
        user_profile.save()

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

    subscriptions = Subscription.objects.select_related().filter(userprofile_id=user_profile, active=True)
    streams = [get_display_recipient(sub.recipient) for sub in subscriptions
               if sub.recipient.type == Recipient.STREAM]

    return render_to_response('zephyr/index.html',
                              {'user_profile': user_profile,
                               'email_hash'  : gravatar_hash(user_profile.user.email),
                               'people'      : people,
                               'streams'     : streams,
                               'have_initial_messages':
                                   'true' if num_messages > 0 else 'false',
                               'show_debug':
                                   settings.DEBUG and ('show_debug' in request.GET),
                               'server_generation': SERVER_GENERATION},
                              context_instance=RequestContext(request))

@login_required_json_view
def json_update_pointer(request):
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

def format_updates_response(messages, mit_sync_bot=False, apply_markdown=False, where='bottom'):
    if mit_sync_bot:
        messages = [m for m in messages if not mit_sync_table.get(m.id)]
    return {'messages': [message.to_dict(apply_markdown) for message in messages],
            "result": "success",
            "msg": "",
            'where':   where,
            'server_generation': SERVER_GENERATION}

def return_messages_immediately(request, handler, user_profile, **kwargs):
    first = request.POST.get("first")
    last = request.POST.get("last")
    failures = request.POST.get("failures")
    client_server_generation = request.POST.get("server_generation")
    if first is None or last is None:
        # When an API user is first querying the server to subscribe,
        # there's no reason to reply immediately.
        return False
    first = int(first)
    last  = int(last)
    if failures is not None:
        failures = int(failures)

    where = 'bottom'
    query = Message.objects.select_related().filter(usermessage__user_profile = user_profile).order_by('id')

    if last == -1:
        # User has no messages yet
        # Get a range around the pointer
        ptr = user_profile.pointer
        messages = (last_n(200, query.filter(id__lt=ptr))
                  + list(query.filter(id__gte=ptr)[:200]))
    else:
        messages = query.filter(id__gt=last)[:400]
        if not messages:
            # No more messages in the future; try filling in from the past.
            messages = last_n(400, query.filter(id__lt=first))
            where = 'top'

    # Filter for mit_sync_bot before checking whether there are any
    # messages to pass on.  If we don't do this, when the only message
    # to forward is one that was sent via mit_sync_bot, the API client
    # will end up in an endless loop requesting more data from us.
    if kwargs.get("mit_sync_bot"):
        messages = [m for m in messages if not mit_sync_table.get(m.id)]

    if messages:
        handler.finish(format_updates_response(messages, where=where, **kwargs))
        return True

    if failures >= 4:
        # No messages, but still return immediately, to clear the
        # user's failures count
        handler.finish(format_updates_response([], where="bottom", **kwargs))
        return True

    if client_server_generation is not None and int(client_server_generation) != SERVER_GENERATION:
        # No messages, but still return immediately to inform the
        # client that they should reload
        handler.finish(format_updates_response([], where="bottom", **kwargs))
        return True

    return False

def get_updates_backend(request, user_profile, handler, **kwargs):
    if return_messages_immediately(request, handler, user_profile, **kwargs):
        return

    def on_receive(messages):
        if handler.request.connection.stream.closed():
            return
        try:
            handler.finish(format_updates_response(messages, **kwargs))
        except socket.error:
            pass

    user_profile.add_callback(handler.async_callback(on_receive))

@asynchronous
@login_required_json_view
def json_get_updates(request, handler):
    if not ('last' in request.POST and 'first' in request.POST):
        return json_error("Missing message range")
    user_profile = UserProfile.objects.get(user=request.user)

    return get_updates_backend(request, user_profile, handler, apply_markdown=True)

# Yes, this has a name similar to the previous function.  I think this
# new name is better and expect the old function to be deleted and
# replaced by the new one soon, so I'm not going to worry about it.
@asynchronous
@login_required_api_view
def api_get_messages(request, user_profile, handler):
    return get_updates_backend(request, user_profile, handler,
                               apply_markdown=(request.POST.get("apply_markdown") is not None),
                               mit_sync_bot=request.POST.get("mit_sync_bot"))

@login_required_api_view
def api_send_message(request, user_profile):
    return send_message_backend(request, user_profile, user_profile.user)

@login_required_json_view
def json_send_message(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if 'time' in request.POST:
        return json_error("Invalid field 'time'")
    return send_message_backend(request, user_profile, request.user)

# TODO: This should have a real superuser security check
def is_super_user_api(request):
    return request.POST.get("api-key") == "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

def already_sent_forged_message(request):
    email = request.POST['sender'].lower()
    if Message.objects.filter(sender__user__email=email,
                              content=request.POST['content'],
                              pub_date__gt=datetime.datetime.utcfromtimestamp(float(request.POST['time']) - 10).replace(tzinfo=utc),
                              pub_date__lt=datetime.datetime.utcfromtimestamp(float(request.POST['time']) + 10).replace(tzinfo=utc)):
        return True
    return False

def create_forged_message_users(request, user_profile):
    # Create a user for the sender, if needed
    email = request.POST['sender'].lower()
    user = create_user_if_needed(user_profile.realm, email, "test",
                                 request.POST['fullname'],
                                 request.POST['shortname'])

    # Create users for huddle recipients, if needed.
    if request.POST['type'] == 'personal':
        if ',' in request.POST['recipient']:
            # Huddle message
            for user_email in [e.strip() for e in request.POST["recipient"].split(",")]:
                create_user_if_needed(user_profile.realm, user_email, "test",
                                      user_email.split('@')[0],
                                      user_email.split('@')[0])
        else:
            user_email = request.POST["recipient"].strip()
            create_user_if_needed(user_profile.realm, user_email, "test",
                                  user_email.split('@')[0],
                                  user_email.split('@')[0])
    return user

# We do not @require_login for send_message_backend, since it is used
# both from the API and the web service.  Code calling
# send_message_backend should either check the API key or check that
# the user is logged in.
def send_message_backend(request, user_profile, sender):
    if "type" not in request.POST:
        return json_error("Missing type")
    if "content" not in request.POST:
        return json_error("Missing message contents")
    if "forged" in request.POST:
        if not is_super_user_api(request):
            return json_error("User not authorized for this query")
        if "time" not in request.POST:
            return json_error("Missing time")
        if already_sent_forged_message(request):
            return json_success()
        sender = create_forged_message_users(request, user_profile)

    message_type_name = request.POST["type"]
    if message_type_name == 'stream':
        if "stream" not in request.POST:
            return json_error("Missing stream")
        if "subject" not in request.POST:
            return json_error("Missing subject")
        stream_name = request.POST['stream'].strip()
        subject_name = request.POST['subject'].strip()

        if not valid_stream_name(stream_name):
            return json_error("Invalid stream name")
        ## FIXME: Commented out temporarily while we figure out what we want
        # if not valid_stream_name(subject_name):
        #     return json_error("Invalid subject name")

        stream = create_stream_if_needed(user_profile.realm, stream_name)
        recipient = Recipient.objects.get(type_id=stream.id, type=Recipient.STREAM)
    elif message_type_name == 'personal':
        if "recipient" not in request.POST:
            return json_error("Missing recipient")

        recipient_data = request.POST['recipient']
        if ',' in recipient_data:
            # This is actually a huddle message, which shares the
            # "personal" message sending form
            recipients = [r.strip() for r in recipient_data.split(',')]
            # Ignore any blank recipients
            recipients = [r for r in recipients if r]
            recipient_ids = []
            for recipient in recipients:
                try:
                    recipient_ids.append(
                        UserProfile.objects.get(user__email=recipient).id)
                except UserProfile.DoesNotExist:
                    return json_error("Invalid email '%s'" % (recipient))
            # Make sure the sender is included in the huddle
            recipient_ids.append(UserProfile.objects.get(user=sender).id)
            huddle = get_huddle(recipient_ids)
            recipient = Recipient.objects.get(type_id=huddle.id, type=Recipient.HUDDLE)
        else:
            # This is actually a personal message
            if not User.objects.filter(email=recipient_data):
                return json_error("Invalid email '%s'" % (recipient_data))

            recipient_user = User.objects.get(email=recipient_data)
            recipient_user_profile = UserProfile.objects.get(user=recipient_user)
            recipient = Recipient.objects.get(type_id=recipient_user_profile.id,
                                              type=Recipient.PERSONAL)
    else:
        return json_error("Invalid message type")

    message = Message()
    message.sender = UserProfile.objects.get(user=sender)
    message.content = request.POST['content']
    message.recipient = recipient
    if message_type_name == 'stream':
        message.subject = subject_name
    if 'time' in request.POST:
        # Forged messages come with a timestamp
        message.pub_date = datetime.datetime.utcfromtimestamp(float(request.POST['time'])).replace(tzinfo=utc)
    else:
        message.pub_date = datetime.datetime.utcnow().replace(tzinfo=utc)

    # To avoid message loops, we must pass whether the message was
    # synced from MIT message here.
    do_send_message(message, synced_from_mit = 'time' in request.POST)

    return json_success()


@login_required_api_view
def api_get_public_streams(request, user_profile):
    streams = sorted([stream.name for stream in
                      Stream.objects.filter(realm=user_profile.realm)])
    return json_success({"streams": streams})

def gather_subscriptions(user_profile):
    subscriptions = Subscription.objects.filter(userprofile=user_profile, active=True)
    # For now, don't display the subscription for your ability to receive personals.
    return sorted([get_display_recipient(sub.recipient) for sub in subscriptions
            if sub.recipient.type == Recipient.STREAM])

@login_required_api_view
def api_get_subscriptions(request, user_profile):
    return json_success({"streams": gather_subscriptions(user_profile)})

@login_required_json_view
def json_list_subscriptions(request):
    subs = gather_subscriptions(UserProfile.objects.get(user=request.user))
    return json_success({"subscriptions": subs})

@login_required_json_view
def json_remove_subscription(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if 'subscription' not in request.POST:
        return json_error("Missing subscriptions")

    sub_name = request.POST.get('subscription')
    stream = get_stream(sub_name, user_profile.realm)
    if not stream:
        return json_error("Not subscribed, so you can't unsubscribe")

    recipient = Recipient.objects.get(type_id=stream.id,
                                      type=Recipient.STREAM)
    subscription = Subscription.objects.get(
        userprofile=user_profile, recipient=recipient)
    subscription.active = False
    subscription.save()

    return json_success({"data": sub_name})

def valid_stream_name(name):
    # Streams must start with a letter or number.
    return re.match("^[.a-zA-Z0-9][.a-z A-Z0-9_-]*$", name)

@login_required_api_view
def api_subscribe(request, user_profile):
    if "streams" not in request.POST:
        return json_error("Missing streams argument.")
    streams = simplejson.loads(request.POST.get("streams"))
    for stream_name in streams:
        if len(stream_name) > 30:
            return json_error("Stream name (%s) too long." % (stream_name,))
        if not valid_stream_name(stream_name):
            return json_error("Invalid characters in stream name (%s)." % (stream_name,))
    res = add_subscriptions_backend(request, user_profile, streams)
    return json_success(res)

@login_required_json_view
def json_add_subscription(request):
    user_profile = UserProfile.objects.get(user=request.user)

    if "new_subscription" not in request.POST:
        return json_error("Missing new_subscription argument")
    stream_name = request.POST.get('new_subscription').strip()
    if not valid_stream_name(stream_name):
        return json_error("Invalid characters in stream names")
    if len(stream_name) > 30:
        return json_error("Stream name %s too long." % (stream_name,))
    res = add_subscriptions_backend(request,user_profile,
                                    [request.POST["new_subscription"]])
    if len(res["already_subscribed"]) != 0:
        return json_error("Subscription already exists")
    return json_success({"data": res["subscribed"][0]})

def add_subscriptions_backend(request, user_profile, streams):
    subscribed = []
    already_subscribed = []
    for stream_name in streams:
        stream = create_stream_if_needed(user_profile.realm, stream_name)
        recipient = Recipient.objects.get(type_id=stream.id,
                                          type=Recipient.STREAM)

        try:
            subscription = Subscription.objects.get(userprofile=user_profile,
                                                    recipient=recipient)
            if subscription.active:
                # Subscription already exists and is active
                already_subscribed.append(stream_name)
                continue
        except Subscription.DoesNotExist:
            subscription = Subscription(userprofile=user_profile,
                                        recipient=recipient)
        subscription.active = True
        subscription.save()
        subscribed.append(stream_name)

    return {"subscribed": subscribed,
            "already_subscribed": already_subscribed}

@login_required_json_view
def json_change_settings(request):
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
    full_name        = request.POST['full_name']
    short_name       = request.POST['short_name']

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

    user_profile.user.save()
    user_profile.save()

    return json_success(result)

@login_required_json_view
def json_stream_exists(request, stream):
    if not valid_stream_name(stream):
        return json_error("Invalid characters in stream name")
    exists = bool(get_stream(stream, UserProfile.objects.get(user=request.user).realm))
    return json_success({"exists": exists})


from django.core.management.base import NoArgsCommand

from django.contrib.auth.models import User
from zephyr.models import Message, UserProfile, Stream, Recipient, \
    Subscription, Huddle, Realm, UserMessage
from django.contrib.sessions.models import Session

class Command(NoArgsCommand):
    help = "Clear only tables we change: messages, accounts + sessions"

    def handle_noargs(self, **options):
        for model in [Message, Stream, UserProfile, User, Recipient,
                      Realm, Subscription, Huddle, UserMessage]:
            model.objects.all().delete()
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
                application = web.Application([(r"/json/get_updates", AsyncDjangoHandler),
                                               (r"/api/v1/get_messages", AsyncDjangoHandler),
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
from zephyr.models import Message, UserProfile, Stream, Recipient, \
    Subscription, Huddle, get_huddle, Realm, UserMessage, get_user_profile_by_id, \
    create_user, do_send_message, create_user_if_needed, create_stream_if_needed
from zephyr.lib.parallel import run_parallel
from django.db import transaction
from django.conf import settings
from api import mit_subs_list

import simplejson
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

def create_streams(stream_list, realm):
    for name in stream_list:
        if Stream.objects.filter(name=name, realm=realm):
            # We're trying to create the same stream twice!
            raise
        Stream.create(name, realm)

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

        stream_list = ["Verona", "Denmark", "Scotland", "Venice", "Rome"]

        if options["delete"]:
            for model in [Message, Stream, UserProfile, User, Recipient,
                          Realm, Subscription, Huddle, UserMessage]:
                model.objects.all().delete()

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

            # Create public streams.
            create_streams(stream_list, humbug_realm)
            recipient_streams = [klass.type_id for klass in
                                 Recipient.objects.filter(type=Recipient.STREAM)]

            # Create subscriptions to streams
            profiles = UserProfile.objects.all()
            for i, profile in enumerate(profiles):
                # Subscribe to some streams.
                for recipient in recipient_streams[:int(len(recipient_streams) *
                                                        float(i)/len(profiles)) + 1]:
                    r = Recipient.objects.get(type=Recipient.STREAM, type_id=recipient)
                    new_subscription = Subscription(userprofile=profile,
                                                    recipient=r)
                    new_subscription.save()
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

        if options["delete"]:
            mit_realm = Realm(domain="mit.edu")
            mit_realm.save()

            # Create internal users
            internal_mit_users = []
            create_users(internal_mit_users)

            create_streams(mit_subs_list.all_subs, mit_realm)

            # Now subscribe everyone to these streams
            profiles = UserProfile.objects.filter(realm=mit_realm)
            for cls in mit_subs_list.all_subs:
                stream = Stream.objects.get(name=cls, realm=mit_realm)
                recipient = Recipient.objects.get(type=Recipient.STREAM, type_id=stream.id)
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
            humbug_stream_list = ["devel", "all", "humbug", "design", "support", "social", "test"]
            create_streams(humbug_stream_list, humbug_realm)

            # Now subscribe everyone to these streams
            profiles = UserProfile.objects.filter(realm=humbug_realm)
            for cls in humbug_stream_list:
                stream = Stream.objects.get(name=cls, realm=humbug_realm)
                recipient = Recipient.objects.get(type=Recipient.STREAM, type_id=stream.id)
                for i, profile in enumerate(profiles):
                    # Subscribe to some streams.
                    new_subscription = Subscription(userprofile=profile, recipient=recipient)
                    new_subscription.save()

            self.stdout.write("Successfully populated test database.\n")
        if options["replay_old_messages"]:
            restore_saved_messages()

            # Set restored pointers to the very latest messages
            for user_profile in UserProfile.objects.all():
                ids = [u.message_id for u in UserMessage.objects.filter(user_profile = user_profile)]
                if ids != []:
                    user_profile.pointer = max(ids)
                    user_profile.save()


recipient_hash = {}
def get_recipient_by_id(rid):
    if rid in recipient_hash:
        return recipient_hash[rid]
    return Recipient.objects.get(id=rid)

def restore_saved_messages():
    old_messages = file("all_messages_log", "r").readlines()
    for old_message_json in old_messages:
        old_message = simplejson.loads(old_message_json.strip())
        message = Message()

        sender_email = old_message["sender_email"]
        realm = None
        try:
            realm = Realm.objects.get(domain=sender_email.split('@')[1])
        except IndexError:
            pass
        except Realm.DoesNotExist:
            pass

        if not realm:
            realm = Realm.objects.get(domain='mit.edu')

        create_user_if_needed(realm, sender_email, sender_email.split('@')[0],
                              old_message["sender_full_name"],
                              old_message["sender_short_name"])
        message.sender = UserProfile.objects.get(user__email=old_message["sender_email"])
        type_hash = {"stream": Recipient.STREAM, "huddle": Recipient.HUDDLE, "personal": Recipient.PERSONAL}
        message.type = type_hash[old_message["type"]]
        message.content = old_message["content"]
        message.subject = old_message["subject"]
        message.pub_date = datetime.datetime.utcfromtimestamp(float(old_message["timestamp"])).replace(tzinfo=utc)

        if message.type == Recipient.PERSONAL:
            u = old_message["recipient"][0]
            create_user_if_needed(realm, u["email"], u["email"].split('@')[0],
                                  u["full_name"], u["short_name"])
            user_profile = UserProfile.objects.get(user__email=u["email"])
            message.recipient = Recipient.objects.get(type=Recipient.PERSONAL,
                                                         type_id=user_profile.id)
        elif message.type == Recipient.STREAM:
            stream = create_stream_if_needed(realm, old_message["recipient"])
            message.recipient = Recipient.objects.get(type=Recipient.STREAM,
                                                         type_id=stream.id)
        elif message.type == Recipient.HUDDLE:
            for u in old_message["recipient"]:
                create_user_if_needed(realm, u["email"], u["email"].split('@')[0],
                                      u["full_name"], u["short_name"])
            target_huddle = get_huddle([UserProfile.objects.get(user__email=u["email"]).id
                                        for u in old_message["recipient"]])
            message.recipient = Recipient.objects.get(type=Recipient.HUDDLE,
                                                         type_id=target_huddle.id)
        else:
            raise
        do_send_message(message, synced_from_mit=True, no_log=True)


# Create some test messages, including:
# - multiple streams
# - multiple subjects per stream
# - multiple huddles
# - multiple personals converastions
# - multiple messages per subject
# - both single and multi-line content
def send_messages(data):
    (tot_messages, personals_pairs, options, output) = data
    from django.db import connection
    connection.close()
    texts = file("zephyr/management/commands/test_messages.txt", "r").readlines()
    offset = random.randint(0, len(texts))

    recipient_streams = [klass.id for klass in
                         Recipient.objects.filter(type=Recipient.STREAM)]
    recipient_huddles = [h.id for h in Recipient.objects.filter(type=Recipient.HUDDLE)]

    huddle_members = {}
    for h in recipient_huddles:
        huddle_members[h] = [s.userprofile.id for s in
                             Subscription.objects.filter(recipient_id=h)]

    num_messages = 0
    random_max = 1000000
    recipients = {}
    while num_messages < tot_messages:
      with transaction.commit_on_success():
        saved_data = ''
        message = Message()
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
                    recipient=message.recipient)).userprofile
            message.subject = stream.name + str(random.randint(1, 3))
            saved_data = message.subject

        message.pub_date = datetime.datetime.utcnow().replace(tzinfo=utc)
        do_send_message(message)

        recipients[num_messages] = [message_type, message.recipient.id, saved_data]
        num_messages += 1
    return tot_messages

import re
import markdown

from zephyr.lib.avatar import gravatar_hash

class Gravatar(markdown.inlinepatterns.Pattern):
    def handleMatch(self, match):
        # NB: the first match of our regex is match.group(2) due to
        # markdown internal matches
        img = markdown.util.etree.Element('img')
        img.set('class', 'message_body_gravatar img-rounded')
        img.set('src', 'https://secure.gravatar.com/avatar/%s?d=identicon&s=30'
            % (gravatar_hash(match.group(2)),))
        return img

class Bugdown(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        del md.inlinePatterns['image_link']
        del md.inlinePatterns['image_reference']
        del md.parser.blockprocessors['hashheader']
        del md.parser.blockprocessors['setextheader']

        md.inlinePatterns.add('gravatar', Gravatar(r'!gravatar\(([^)]*)\)'), '_begin')

# We need to re-initialize the markdown engine every 30 messages
# due to some sort of performance leak in the markdown library.
MAX_MD_ENGINE_USES = 30

_md_engine = None
_use_count = 0

# A link starts after whitespace, and cannot contain spaces,
# end parentheses, or end brackets (which would confuse Markdown).
# FIXME: Use one of the actual linkification extensions.
_link_regex = re.compile(r'(\s|\A)(?P<url>https?://[^\s\])]+)')

def _linkify(match):
    url = match.group('url')
    return ' [%s](%s) ' % (url, url)

def convert(md):
    """Convert Markdown to HTML, with Humbug-specific settings and hacks."""
    global _md_engine, _use_count

    if _md_engine is None:
        _md_engine = markdown.Markdown(
            extensions    = ['fenced_code', 'codehilite', 'nl2br', Bugdown()],
            safe_mode     = 'escape',
            output_format = 'xhtml')

    md = _link_regex.sub(_linkify, md)

    try:
        html = _md_engine.convert(md)
    except:
        # FIXME: Do something more reasonable here!
        html = '<p>[Humbug note: Sorry, we could not understand the formatting of your message]</p>'

    _use_count += 1
    if _use_count >= MAX_MD_ENGINE_USES:
        _md_engine = None
        _use_count = 0

    return html

def last_n(n, query_set):
    """Get the last n results from a Django QuerySet, in a semi-efficient way.
       Returns a list."""

    # We don't use reversed() because we would get a generator,
    # which causes bool(last_n(...)) to be True always.

    xs = list(query_set.reverse()[:n])
    xs.reverse()
    return xs

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


import hashlib

def gravatar_hash(email):
    """Compute the Gravatar hash for an email address."""
    return hashlib.md5(email.lower()).hexdigest()

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



from __future__ import absolute_import

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext, loader
from django.utils.timezone import now
from django.utils.cache import patch_cache_control
from django.core.exceptions import ValidationError
from django.core import validators
from django.contrib.auth.views import login as django_login_page, \
    logout_then_login as django_logout_then_login
from django.db.models import Q, F
from django.core.mail import send_mail, mail_admins, EmailMessage
from django.db import transaction
from zerver.models import Message, UserProfile, Stream, Subscription, \
    Recipient, Realm, UserMessage, bulk_get_recipients, \
    PreregistrationUser, get_client, MitUser, UserActivity, \
    MAX_SUBJECT_LENGTH, get_stream, bulk_get_streams, UserPresence, \
    get_recipient, valid_stream_name, to_dict_cache_key, to_dict_cache_key_id, \
    extract_message_dict, stringify_message_dict, parse_usermessage_flags, \
    email_to_domain, email_to_username, get_realm, completely_open, \
    is_super_user, get_active_user_profiles_by_realm
from zerver.lib.actions import do_remove_subscription, bulk_remove_subscriptions, \
    do_change_password, create_mit_user_if_needed, do_change_full_name, \
    do_change_enable_desktop_notifications, do_change_enter_sends, do_change_enable_sounds, \
    do_send_confirmation_email, do_activate_user, do_create_user, check_send_message, \
    do_change_subscription_property, internal_send_message, \
    create_stream_if_needed, gather_subscriptions, subscribed_to_stream, \
    update_user_presence, bulk_add_subscriptions, do_update_message_flags, \
    recipient_for_emails, extract_recipients, do_events_register, \
    get_status_dict, do_change_enable_offline_email_notifications, \
    do_update_onboarding_steps, do_update_message, internal_prep_message, \
    do_send_messages, do_add_subscription, get_default_subs, do_deactivate, \
    user_email_is_unique, do_invite_users, do_refer_friend, compute_mit_user_fullname, \
    do_add_alert_words, do_remove_alert_words, do_set_alert_words
from zerver.lib.create_user import random_api_key
from zerver.forms import RegistrationForm, HomepageForm, ToSForm, CreateBotForm, \
    is_inactive, isnt_mit, not_mit_mailing_list
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django_openid_auth.views import default_render_failure, login_complete
from openid.consumer.consumer import SUCCESS as openid_SUCCESS
from openid.extensions import ax
from zerver.lib import bugdown
from zerver.lib.alert_words import user_alert_words

from zerver.decorator import require_post, \
    authenticated_api_view, authenticated_json_post_view, \
    has_request_variables, authenticated_json_view, \
    to_non_negative_int, json_to_dict, json_to_list, json_to_bool, \
    JsonableError, get_user_profile_by_email, \
    authenticated_rest_api_view, process_as_post, REQ, rate_limit_user
from zerver.lib.query import last_n
from zerver.lib.avatar import avatar_url
from zerver.lib.upload import upload_message_image, upload_avatar_image
from zerver.lib.response import json_success, json_error, json_response, json_method_not_allowed
from zerver.lib.cache import cache_get_many, cache_set_many, \
    generic_bulk_cached_fetch
from zerver.lib.unminify import SourceMap
from zerver.lib.queue import queue_json_publish
from zerver.lib.utils import statsd, generate_random_token
from zerver import tornado_callbacks
from django.db import connection

from confirmation.models import Confirmation

import subprocess
import calendar
import datetime
import ujson
import simplejson
import re
import urllib
import base64
import time
import logging
from os import path
from collections import defaultdict

def list_to_streams(streams_raw, user_profile, autocreate=False, invite_only=False):
    """Converts plaintext stream names to a list of Streams, validating input in the process

    For each stream name, we validate it to ensure it meets our requirements for a proper
    stream name: that is, that it is shorter than 30 characters and passes valid_stream_name.

    This function in autocreate mode should be atomic: either an exception will be raised
    during a precheck, or all the streams specified will have been created if applicable.

    @param streams_raw The list of stream names to process
    @param user_profile The user for whom we are retreiving the streams
    @param autocreate Whether we should create streams if they don't already exist
    @param invite_only Whether newly created streams should have the invite_only bit set
    """
    existing_streams = []
    created_streams = []
    # Validate all streams, getting extant ones, then get-or-creating the rest.
    stream_set = set(stream_name.strip() for stream_name in streams_raw)
    rejects = []
    for stream_name in stream_set:
        if len(stream_name) > Stream.MAX_NAME_LENGTH:
            raise JsonableError("Stream name (%s) too long." % (stream_name,))
        if not valid_stream_name(stream_name):
            raise JsonableError("Invalid stream name (%s)." % (stream_name,))

    existing_stream_map = bulk_get_streams(user_profile.realm, stream_set)

    for stream_name in stream_set:
        stream = existing_stream_map.get(stream_name.lower())
        if stream is None:
            rejects.append(stream_name)
        else:
            existing_streams.append(stream)
    if autocreate:
        for stream_name in rejects:
            stream, created = create_stream_if_needed(user_profile.realm,
                                                      stream_name,
                                                      invite_only=invite_only)
            if created:
                created_streams.append(stream)
            else:
                existing_streams.append(stream)
    elif rejects:
        raise JsonableError("Stream(s) (%s) do not exist" % ", ".join(rejects))

    return existing_streams, created_streams

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
        or agent.realm != principal_user_profile.realm):
        # We have to make sure we don't leak information about which users
        # are registered for Zulip in a different realm.  We could do
        # something a little more clever and check the domain part of the
        # principal to maybe give a better error message
        raise PrincipalError(principal)

    return principal_user_profile

METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH')

# Import the Tornado REST views that are used by rest_dispatch
from zerver.tornadoviews import get_events_backend, get_updates_backend

@csrf_exempt
def rest_dispatch(request, **kwargs):
    """Dispatch to a REST API endpoint.

    This calls the function named in kwargs[request.method], if that request
    method is supported, and after wrapping that function to:

        * protect against CSRF (if the user is already authenticated through
          a Django session)
        * authenticate via an API key (otherwise)
        * coerce PUT/PATCH/DELETE into having POST-like semantics for
          retrieving variables

    Any keyword args that are *not* HTTP methods are passed through to the
    target function.

    Note that we search views.py globals for the function to call, so never
    make a urls.py pattern put user input into a variable called GET, POST,
    etc.
    """
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
    elif not mit_beta_user and prereg_user.realm:
        # You have a realm set, even though nobody referred you. This
        # happens if you sign up through a special URL for an open
        # realm.
        domain = prereg_user.realm.domain
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
        if domain == "mit.edu":
            hesiod_name = compute_mit_user_fullname(email)
            form = RegistrationForm(
                    initial={'full_name': hesiod_name if "@" not in hesiod_name else ""})
        else:
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
                try:
                    user_profile = get_user_profile_by_email(email)
                except UserProfile.DoesNotExist:
                    user_profile = do_create_user(email, password, realm, full_name, short_name)
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

                # Give you the last 100 messages on your streams, so you have
                # something to look at in your home view once you finish the
                # tutorial.
                recipients = Recipient.objects.filter(type=Recipient.STREAM,
                                                      type_id__in=[stream.id for stream in streams])
                messages = Message.objects.filter(recipient_id__in=recipients).order_by("-id")[0:100]
                if len(messages) > 0:
                    ums_to_create = [UserMessage(user_profile=user_profile, message=message,
                                                 flags=UserMessage.flags.read)
                                     for message in messages]

                    UserMessage.objects.bulk_create(ums_to_create)

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
                return HttpResponseRedirect(reverse('zerver.views.initial_invite_page'))
            else:
                return HttpResponseRedirect(reverse('zerver.views.home'))

    return render_to_response('zerver/register.html',
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
                    loader.render_to_string('zerver/tos_accept_body.txt',
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
    return render_to_response('zerver/accounts_accept_terms.html',
        { 'form': form, 'company_name': domain, 'email': email },
        context_instance=RequestContext(request))

from zerver.lib.ccache import make_ccache

@authenticated_json_view
@has_request_variables
def webathena_kerberos_login(request, user_profile,
                             cred=REQ(default=None)):
    if cred is None:
        return json_error("Could not find Kerberos credential")
    if not user_profile.realm.domain == "mit.edu":
        return json_error("Webathena login only for mit.edu realm")

    try:
        parsed_cred = ujson.loads(cred)
        user = parsed_cred["cname"]["nameString"][0]
        if user == "golem":
            # Hack for an mit.edu user whose Kerberos username doesn't
            # match what he zephyrs as
            user = "ctl"
        assert(user == user_profile.email.split("@")[0])
        ccache = make_ccache(parsed_cred)
    except Exception:
        return json_error("Invalid Kerberos cache")

    # TODO: Send these data via (say) rabbitmq
    try:
        subprocess.check_call(["ssh", "humbug@zmirror2.zulip.net", "--",
                               "/home/humbug/humbug/bots/process_ccache",
                               user,
                               user_profile.api_key,
                               base64.b64encode(ccache)])
    except Exception:
        logging.exception("Error updating the user's ccache")
        return json_error("We were unable to setup mirroring for you")

    return json_success()

def api_endpoint_docs(request):
    raw_calls = open('templates/zerver/api_content.json', 'r').read()
    calls = ujson.loads(raw_calls)
    langs = set()
    for call in calls:
        response = call['example_response']
        if not '\n' in response:
            # For 1-line responses, pretty-print them
            extended_response = response.replace(", ", ",\n ")
        else:
            extended_response = response
        call['rendered_response'] = bugdown.convert("~~~ .py\n" + extended_response + "\n~~~\n", "default")
        for example_type in ('request', 'response'):
            for lang in call.get('example_' + example_type, []):
                langs.add(lang)
    return render_to_response(
            'zerver/api_endpoints.html', {
                'content': calls,
                'langs': langs,
                },
        context_instance=RequestContext(request))

@authenticated_json_post_view
@has_request_variables
def json_invite_users(request, user_profile, invitee_emails=REQ):
    # Validation
    try:
        isnt_mit(user_profile.email)
    except ValidationError, e:
        return json_error(e.message)

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

def create_homepage_form(request, user_info=None):
    if user_info:
        return HomepageForm(user_info, domain=request.session.get("domain"))
    # An empty fields dict is not treated the same way as not
    # providing it.
    return HomepageForm(domain=request.session.get("domain"))

def handle_openid_errors(request, issue, openid_response=None):
    if issue == "Unknown user":
        if openid_response is not None and openid_response.status == openid_SUCCESS:
            ax_response = ax.FetchResponse.fromSuccessResponse(openid_response)
            google_email = openid_response.getSigned('http://openid.net/srv/ax/1.0', 'value.email')
            full_name = " ".join((
                    ax_response.get('http://axschema.org/namePerson/first')[0],
                    ax_response.get('http://axschema.org/namePerson/last')[0]))
            form = create_homepage_form(request, user_info={'email': google_email})
            request.verified_email = None
            if form.is_valid():
                # Construct a PreregistrationUser object and send the user over to
                # the confirmation view.
                prereg_user = create_preregistration_user(google_email, request)
                return redirect("".join((
                    "/",
                    # Split this so we only get the part after the /
                    Confirmation.objects.get_link_for_object(prereg_user).split("/", 3)[3],
                    '?gafyd_name=',
                    # urllib does not handle Unicode, so coerece to encoded byte string
                    # Explanation: http://stackoverflow.com/a/5605354/90777
                    urllib.quote_plus(full_name.encode('utf8')))))
            else:
                return render_to_response('zerver/accounts_home.html', {'form': form})
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
        return redirect('zerver.views.home')

    params = {'company_name': user.realm.domain}

    if (user.realm.restricted_to_domain):
        params['invite_suffix'] = user.realm.domain

    return render_to_response('zerver/initial_invite_page.html', params,
                              context_instance=RequestContext(request))

@require_post
def logout_then_login(request, **kwargs):
    return django_logout_then_login(request, kwargs)

def create_preregistration_user(email, request):
    domain = request.session.get("domain")
    if not completely_open(domain):
        domain = None
    # MIT users who are not explicitly signing up for an open realm
    # require special handling (They may already have an (inactive)
    # account, for example)
    if email_to_domain(email) == "mit.edu" and not domain:
        prereg_user, created = MitUser.objects.get_or_create(email=email)
    else:
        prereg_user = PreregistrationUser(email=email, realm=get_realm(domain))
        prereg_user.save()

    request.session["domain"] = None

    return prereg_user

def accounts_home_with_domain(request, domain):
    if completely_open(domain):
        # You can sign up for a completely open realm through a
        # special registration path that contains the domain in the
        # URL. We store this information in the session rather than
        # elsewhere because we don't have control over URL or form
        # data for folks registering through OpenID.
        request.session["domain"] = domain
        return accounts_home(request)
    else:
        return HttpResponseRedirect(reverse('zerver.views.accounts_home'))

def accounts_home(request):
    if request.method == 'POST':
        form = create_homepage_form(request, user_info=request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            prereg_user = create_preregistration_user(email, request)
            Confirmation.objects.send_confirmation(prereg_user, email)
            return HttpResponseRedirect(reverse('send_confirm', kwargs={'email': email}))
        try:
            email = request.POST['email']
            # Note: We don't check for uniqueness
            is_inactive(email)
        except ValidationError:
            return HttpResponseRedirect(reverse('django.contrib.auth.views.login') + '?email=' + urllib.quote_plus(email))
    else:
        form = create_homepage_form(request)
    return render_to_response('zerver/accounts_home.html',
                              {'form': form, 'current_url': request.get_full_path},
                              context_instance=RequestContext(request))

def approximate_unread_count(user_profile, latest_read_message):
    # latest_read_message is a UserMessage object.
    if not latest_read_message:
        return 0
    return UserMessage.objects.filter(user_profile=user_profile,
                                      id__gt=latest_read_message.id).count()

def sent_time_in_epoch_seconds(user_message):
    # user_message is a UserMessage object.
    if not user_message:
        return None
    # We have USE_TZ = True, so our datetime objects are timezone-aware.
    # Return the epoch seconds in UTC.
    return calendar.timegm(user_message.message.pub_date.utctimetuple())

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

        register_ret['pointer'] = register_ret['max_message_id']
        user_profile.last_pointer_updater = request.session.session_key

    if user_profile.pointer == -1:
        latest_read = None
    else:
        try:
            latest_read = UserMessage.objects.get(user_profile=user_profile,
                                                  message__id=user_profile.pointer)
        except UserMessage.DoesNotExist:
            # Don't completely fail if your saved pointer ID is invalid
            logging.warning("%s has invalid pointer %s" % (user_profile.email, user_profile.pointer))
            latest_read = None


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
        referrals             = register_ret['referrals'],
        realm_emoji           = register_ret['realm_emoji'],
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
        unread_count          = approximate_unread_count(user_profile,
                                                         latest_read),
        furthest_read_time    = sent_time_in_epoch_seconds(latest_read),
        onboarding_steps      = ujson.loads(user_profile.onboarding_steps),
        staging               = settings.STAGING_DEPLOYED or not settings.DEPLOYED,
        alert_words           = register_ret['alert_words']
    ))

    statsd.incr('views.home')

    try:
        isnt_mit(user_profile.email)
        show_invites = True
    except ValidationError:
        show_invites = False

    # For the CUSTOMER4 student realm, only let instructors (who have
    # @customer4.invalid addresses) invite new users.
    if ((user_profile.realm.domain == "users.customer4.invalid") and
        (not user_profile.email.lower().endswith("@customer4.invalid"))):
        show_invites = False

    response = render_to_response('zerver/index.html',
                                  {'user_profile': user_profile,
                                   'page_params' : page_params,
                                   'avatar_url': avatar_url(user_profile),
                                   'nofontface': is_buggy_ua(request.META["HTTP_USER_AGENT"]),
                                   'show_debug':
                                       settings.DEBUG and ('show_debug' in request.GET),
                                   'show_invites': show_invites,
                                   'show_admin': user_profile.show_admin,
                                   'show_webathena': user_profile.realm.domain == "mit.edu",
                                   },
                                  context_instance=RequestContext(request))
    patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True)
    return response

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

    try:
        UserMessage.objects.get(
            user_profile=user_profile,
            message__id=pointer
        )
    except UserMessage.DoesNotExist:
        raise JsonableError("Invalid message ID")

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
        elif operand == 'alerted':
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
            cursor.execute("SELECT zerver_message.id, zerver_usermessage.flags FROM " +
                           "zerver_usermessage INNER JOIN zerver_message ON " +
                           "zerver_message.id = zerver_usermessage.message_id " +
                           "WHERE zerver_usermessage.user_profile_id = %s and zerver_message.id <= %s " +
                           "ORDER BY message_id DESC LIMIT %s", [user_profile.id, before_anchor, num_before])
            before_result = reversed(cursor.fetchall())
        else:
            before_result = last_n(num_before, query.filter(**add_prefix(id__lte=before_anchor)))
    if num_after != 0:
        if use_raw_query:
            cursor = connection.cursor()
            # These queries should always be the same as what we would do
            # in the !include_history case.
            cursor.execute("SELECT zerver_message.id, zerver_usermessage.flags FROM " +
                           "zerver_usermessage INNER JOIN zerver_message ON " +
                           "zerver_message.id = zerver_usermessage.message_id " +
                           "WHERE zerver_usermessage.user_profile_id = %s and zerver_message.id >= %s " +
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
    return generate_random_token(32)

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
def json_update_flags(request, user_profile):
    return update_message_flags(request, user_profile);

@has_request_variables
def update_message_flags(request, user_profile, messages=REQ('messages', converter=json_to_list),
                      operation=REQ('op'), flag=REQ('flag'),
                      all=REQ('all', converter=json_to_bool, default=False)):
    do_update_message_flags(user_profile, operation, flag, messages, all)
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

def is_super_user_api(request):
    return request.user.is_authenticated() and is_super_user(request.user)

def mit_to_mit(user_profile, email):
    # Are the sender and recipient both @mit.edu addresses?
    # We have to handle this specially, inferring the domain from the
    # e-mail address, because the recipient may not existing in Zulip
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
                           propagate_subject=REQ(default=False),
                           content=REQ(default=None)):
    if subject is None and content is None:
        return json_error("Nothing to change")
    do_update_message(user_profile, message_id, subject, propagate_subject, content)
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
                         message_content = REQ('content'),
                         domain = REQ('domain', default=None)):
    client = request.client
    is_super_user = is_super_user_api(request)
    if forged and not is_super_user:
        return json_error("User not authorized for this query")

    realm = None
    if domain:
        if not is_super_user:
            # The email gateway bot needs to be able to send messages in
            # any realm.
            return json_error("User not authorized for this query")
        realm = get_realm(domain)
        if not realm:
            return json_error("Unknown domain " + domain)

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
                             forwarder_user_profile=user_profile, realm=realm)
    return json_success({"id": ret})

@has_request_variables
def render_message_backend(request, user_profile, content=REQ):
    rendered_content = bugdown.convert(content, user_profile.realm.domain)
    return json_success({"rendered": rendered_content})

@authenticated_api_view
def api_get_public_streams(request, user_profile):
    return get_public_streams_backend(request, user_profile)

@authenticated_json_post_view
def json_get_public_streams(request, user_profile):
    return get_public_streams_backend(request, user_profile)

# By default, lists all streams that the user has access to --
# i.e. public streams plus invite-only streams that the user is on
@has_request_variables
def get_streams_backend(request, user_profile,
                        include_public=REQ(converter=json_to_bool, default=True),
                        include_subscribed=REQ(converter=json_to_bool, default=True),
                        include_all_active=REQ(converter=json_to_bool, default=False)):
    if include_all_active and not is_super_user_api(request):
            return json_error("User not authorized for this query")

    # Listing public streams are disabled for some users (e.g. a
    # contractor for CUSTOMER5) and for the mit.edu realm.
    include_public = include_public and not (user_profile.public_streams_disabled or
                                             user_profile.realm.domain == "mit.edu")

    # Only get streams someone is currently subscribed to
    subs_filter = Subscription.objects.filter(active=True).values('recipient_id')
    stream_ids = Recipient.objects.filter(
        type=Recipient.STREAM, id__in=subs_filter).values('type_id')

    # Start out with all active streams in the realm
    query = Stream.objects.filter(id__in = stream_ids, realm=user_profile.realm)

    if not include_all_active:
        user_subs = Subscription.objects.select_related("recipient").filter(
            active=True, user_profile=user_profile,
            recipient__type=Recipient.STREAM)

        if include_subscribed:
            recipient_check = Q(id__in=[sub.recipient.type_id for sub in user_subs])
        if include_public:
            invite_only_check = Q(invite_only=False)

        if include_subscribed and include_public:
            query = query.filter(recipient_check | invite_only_check)
        elif include_public:
            query = query.filter(invite_only_check)
        elif include_subscribed:
            query = query.filter(recipient_check)
        else:
            # We're including nothing, so don't bother hitting the DB.
            query = []

    streams = sorted({"name": stream.name} for stream in query)
    return json_success({"streams": streams})

def get_public_streams_backend(request, user_profile):
    return get_streams_backend(request, user_profile, include_public=True,
                               include_subscribed=False, include_all_active=False)

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

    streams, _ = list_to_streams(streams_raw, user_profile)

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

def filter_stream_authorization(user_profile, streams):
    streams_subscribed = set()
    recipients_map = bulk_get_recipients(Recipient.STREAM, [stream.id for stream in streams])
    subs = Subscription.objects.filter(user_profile=user_profile,
                                       recipient__in=recipients_map.values(),
                                       active=True)

    for sub in subs:
        streams_subscribed.add(sub.recipient.type_id)

    unauthorized_streams = []
    for stream in streams:
        # The user is authorized for his own streams
        if stream.id in streams_subscribed:
            continue

        # The user is not authorized for invite_only streams, and if
        # the user has public streams disabled, nothing is authorized
        if stream.invite_only or user_profile.public_streams_disabled:
            unauthorized_streams.append(stream)

    streams = [stream for stream in streams if
               stream.id not in set(stream.id for stream in unauthorized_streams)]
    return streams, unauthorized_streams

@has_request_variables
def add_subscriptions_backend(request, user_profile,
                              streams_raw = REQ("subscriptions", json_to_list),
                              invite_only = REQ(converter=json_to_bool, default=False),
                              announce = REQ(converter=json_to_bool, default=False),
                              principals = REQ(converter=json_to_list, default=None),
                              authorization_errors_fatal = REQ(converter=json_to_bool, default=True)):

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

    existing_streams, created_streams = \
        list_to_streams(stream_names, user_profile, autocreate=True, invite_only=invite_only)
    authorized_streams, unauthorized_streams = \
        filter_stream_authorization(user_profile, existing_streams)
    if len(unauthorized_streams) > 0 and authorization_errors_fatal:
        return json_error("Unable to access stream (%s)." % unauthorized_streams[0].name)
    # Newly created streams are also authorized for the creator
    streams = authorized_streams + created_streams

    if principals is not None:
        if user_profile.realm.domain == 'mit.edu' and not all(stream.invite_only for stream in streams):
            return json_error("You can only invite other mit.edu users to invite-only streams.")
        subscribers = set(principal_to_user_profile(user_profile, principal) for principal in principals)
    else:
        subscribers = [user_profile]

    (subscribed, already_subscribed) = bulk_add_subscriptions(streams, subscribers)

    result = dict(subscribed=defaultdict(list), already_subscribed=defaultdict(list))
    for (subscriber, stream) in subscribed:
        result["subscribed"][subscriber.email].append(stream.name)
    for (subscriber, stream) in already_subscribed:
        result["already_subscribed"][subscriber.email].append(stream.name)

    private_streams = dict((stream.name, stream.invite_only) for stream in streams)

    # Inform the user if someone else subscribed them to stuff,
    # or if a new stream was created with the "announce" option.
    notifications = []
    if principals and result["subscribed"]:
        for email, subscriptions in result["subscribed"].iteritems():
            if email == user_profile.email:
                # Don't send a Zulip if you invited yourself.
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

            if len([s for s in subscriptions if not private_streams[s]]) > 0:
                msg += "\nYou can see historical content on a non-invite-only stream by narrowing to it."
            notifications.append(internal_prep_message("notification-bot@zulip.com",
                                                       "private", email, "", msg))

    if announce and len(created_streams) > 0:
        for realm_user in get_active_user_profiles_by_realm(user_profile.realm):
            # Don't announce to yourself or to people you explicitly added
            # (who will get the notification above instead).
            if realm_user.email in principals or realm_user.email == user_profile.email:
                continue
            msg = ("Hi there!  %s just created a new stream '%s'. "
                   "To join, click the gear in the left-side streams list."
                   % (user_profile.full_name, created_streams[0].name))
            notifications.append(internal_prep_message("notification-bot@zulip.com",
                                                       "private",
                                                       realm_user.email, "", msg))

    if len(notifications) > 0:
        do_send_messages(notifications)

    result["subscribed"] = dict(result["subscribed"])
    result["already_subscribed"] = dict(result["already_subscribed"])
    if not authorization_errors_fatal:
        result["unauthorized"] = [stream.name for stream in unauthorized_streams]
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
    stream = get_stream(stream_name, user_profile.realm)
    if stream is None:
        return json_error("Stream does not exist: %s" % stream_name)

    if user_profile.realm.domain == "mit.edu" and not stream.invite_only:
        return json_error("You cannot get subscribers for public streams in this realm")

    if stream.invite_only and not subscribed_to_stream(user_profile, stream):
        return json_error("Unable to retrieve subscribers for invite-only stream")

    # Note that non-active users may still have "active" subscriptions, because we
    # want to be able to easily reactivate them with their old subscriptions.  This
    # is why the query here has to look at the UserProfile.is_active flag.
    subscriptions = Subscription.objects.filter(recipient__type=Recipient.STREAM,
                                                recipient__type_id=stream.id,
                                                user_profile__is_active=True,
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
        if user_profile.realm.domain == "users.customer4.invalid":
            # At the request of the facilitators, CUSTOMER4
            # students can't change their names. Failingly silently is
            # fine -- they can't do it through the UI, so they'd have
            # to be trying to break the rules.
            pass
        else:
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
        return HttpResponseRedirect(reverse('zerver.views.login_page'))

    web_queries = (
        ("get_updates",    ["/json/get_updates", "/json/get_events"]),
        ("send_message",   ["/json/send_message"]),
        ("update_pointer", ["/json/update_pointer"]),
    )

    api_queries = (
        ("get_updates",  ["/api/v1/get_messages", "/api/v1/messages/latest", "/api/v1/events"]),
        ("send_message", ["/api/v1/send_message"]),
    )

    return render_to_response('zerver/activity.html',
        { 'data': {
            'Website': ActivityTable('website',       web_queries, default_tab=True),
            'Mirror':  ActivityTable('zephyr_mirror', api_queries),
            'API':     ActivityTable('API',           api_queries),
            'Android': ActivityTable('Android',       api_queries),
            'iPhone':  ActivityTable('iPhone',        api_queries)
        }}, context_instance=RequestContext(request))

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
                            event_types=REQ(converter=json_to_list, default=None),
                            queue_lifespan_secs=REQ(converter=int, default=0)):
    ret = do_events_register(user_profile, request.client, apply_markdown,
                             event_types, queue_lifespan_secs)
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
def patch_bot_backend(request, user_profile, email, full_name=REQ):
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
        bot.save(update_fields=["avatar_source"])
        bot_avatar_url = avatar_url(bot)
    else:
        return json_error("You may only upload one file at a time")

    json_result = dict(
        full_name = full_name,
        avatar_url = bot_avatar_url
    )
    return json_success(json_result)

@has_request_variables
def regenerate_api_key(request, user_profile):
    user_profile.api_key = random_api_key()
    user_profile.save(update_fields=["api_key"])
    json_result = dict(
        api_key = user_profile.api_key
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
    bot.save(update_fields=["api_key"])
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

@authenticated_json_post_view
@has_request_variables
def json_refer_friend(request, user_profile, email=REQ):
    if not email:
        return json_error("No email address specified")
    if user_profile.invites_granted - user_profile.invites_used <= 0:
        return json_error("Insufficient invites")

    do_refer_friend(user_profile, email);

    return json_success()

def list_alert_words(request, user_profile):
    return json_success({'alert_words': user_alert_words(user_profile)})

@authenticated_json_post_view
@has_request_variables
def json_set_alert_words(request, user_profile,
                         alert_words=REQ(converter=json_to_list, default=[])):
    do_set_alert_words(user_profile, alert_words)
    return json_success()

@has_request_variables
def set_alert_words(request, user_profile,
                    alert_words=REQ(converter=json_to_list, default=[])):
    do_set_alert_words(user_profile, alert_words)
    return json_success()

@has_request_variables
def add_alert_words(request, user_profile,
                    alert_words=REQ(converter=json_to_list, default=[])):
    do_add_alert_words(user_profile, alert_words)
    return json_success()

@has_request_variables
def remove_alert_words(request, user_profile,
                       alert_words=REQ(converter=json_to_list, default=[])):
    do_remove_alert_words(user_profile, alert_words)
    return json_success()
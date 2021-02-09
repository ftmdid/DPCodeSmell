from __future__ import absolute_import

from django.conf import settings
from django.core import validators
from django.contrib.sessions.models import Session
from zerver.lib.cache import update_user_profile_cache
from zerver.lib.context_managers import lockfile
from zerver.models import Realm, RealmEmoji, Stream, UserProfile, UserActivity, \
    Subscription, Recipient, Message, UserMessage, valid_stream_name, \
    DefaultStream, UserPresence, Referral, PushDeviceToken, MAX_SUBJECT_LENGTH, \
    MAX_MESSAGE_LENGTH, get_client, get_stream, get_recipient, get_huddle, \
    get_user_profile_by_id, PreregistrationUser, get_display_recipient, \
    to_dict_cache_key, get_realm, stringify_message_dict, bulk_get_recipients, \
    resolve_email_to_domain, email_to_username, display_recipient_cache_key, \
    get_stream_cache_key, to_dict_cache_key_id, is_super_user, \
    UserActivityInterval, get_active_user_dicts_in_realm, RealmAlias, \
    ScheduledJob, realm_filters_for_domain, RealmFilter
from zerver.lib.avatar import get_avatar_url
from guardian.shortcuts import assign_perm, remove_perm

from django.db import transaction, IntegrityError
from django.db.models import F, Q
from django.core.exceptions import ValidationError
from django.utils.importlib import import_module
from django.template import loader
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.timezone import now

from confirmation.models import Confirmation

session_engine = import_module(settings.SESSION_ENGINE)

from zerver.lib.initial_password import initial_password
from zerver.lib.timestamp import timestamp_to_datetime, datetime_to_timestamp
from zerver.lib.cache_helpers import cache_save_message
from zerver.lib.queue import queue_json_publish
from django.utils import timezone
from zerver.lib.create_user import create_user
from zerver.lib import bugdown
from zerver.lib.cache import cache_with_key, cache_set, \
    user_profile_by_email_cache_key, cache_set_many, \
    cache_delete, cache_delete_many, message_cache_key
from zerver.decorator import get_user_profile_by_email, json_to_list, JsonableError, \
     statsd_increment, uses_mandrill
from zerver.lib.event_queue import request_event_queue, get_user_events
from zerver.lib.utils import log_statsd_event, statsd
from zerver.lib.html_diff import highlight_html_differences
from zerver.lib.alert_words import user_alert_words, add_user_alert_words, \
    remove_user_alert_words, set_user_alert_words
from zerver.lib.push_notifications import num_push_devices_for_user, \
     send_apple_push_notification, send_android_push_notification
from zerver.lib.narrow import check_supported_events_narrow_filter

from zerver import tornado_callbacks

import DNS
import ujson
import time
import traceback
import re
import datetime
import os
import platform
import logging
import itertools
from collections import defaultdict
import urllib
import subprocess

# Store an event in the log for re-importing messages
def log_event(event):
    if settings.EVENT_LOG_DIR is None:
        return

    if "timestamp" not in event:
        event["timestamp"] = time.time()

    if not os.path.exists(settings.EVENT_LOG_DIR):
        os.mkdir(settings.EVENT_LOG_DIR)

    template = os.path.join(settings.EVENT_LOG_DIR,
        '%s.' + platform.node()
        + datetime.datetime.now().strftime('.%Y-%m-%d'))

    with lockfile(template % ('lock',)):
        with open(template % ('events',), 'a') as log:
            log.write(ujson.dumps(event) + '\n')

def active_user_ids(realm):
    return [userdict['id'] for userdict in get_active_user_dicts_in_realm(realm)]

def notify_created_user(user_profile):
    notice = dict(event=dict(type="realm_user", op="add",
                             person=dict(email=user_profile.email,
                                         full_name=user_profile.full_name,
                                         is_bot=user_profile.is_bot,
                  )),
                  users=active_user_ids(user_profile.realm))
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
    for session in Session.objects.filter(expire_date__gte=datetime.datetime.now()):
        if session.get_decoded().get('_auth_user_id') in realm_user_ids:
            delete_session(session)

def delete_all_user_sessions():
    for session in Session.objects.all():
        delete_session(session)

def active_humans_in_realm(realm):
    return UserProfile.objects.filter(realm=realm, is_active=True, is_bot=False)

def do_deactivate_realm(realm):
    """
    Deactivate this realm. Do NOT deactivate the users -- we need to be able to
    tell the difference between users that were intentionally deactivated,
    e.g. by a realm admin, and users who can't currently use Zulip because their
    realm has been deactivated.
    """
    if realm.deactivated:
        return

    realm.deactivated = True
    realm.save(update_fields=["deactivated"])

    for user in active_humans_in_realm(realm):
        # Don't deactivate the users, but do delete their sessions so they get
        # bumped to the login screen, where they'll get a realm deactivation
        # notice when they try to log in.
        delete_user_sessions(user)
        update_user_profile_cache(None, instance=user, update_fields=None)

def do_deactivate_user(user_profile, log=True, _cascade=True):
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
                  users=active_user_ids(user_profile.realm))
    tornado_callbacks.send_notification(notice)

    if _cascade:
        bot_profiles = UserProfile.objects.filter(is_bot=True, is_active=True,
                                                  bot_owner=user_profile)
        for profile in bot_profiles:
            do_deactivate_user(profile, _cascade=False)

def do_deactivate_stream(stream, log=True):
    user_profiles = UserProfile.objects.filter(realm=stream.realm)
    for user_profile in user_profiles:
            do_remove_subscription(user_profile, stream)
    return

def do_change_user_email(user_profile, new_email):
    old_email = user_profile.email
    user_profile.email = new_email
    user_profile.save(update_fields=["email"])

    log_event({'type': 'user_email_changed',
               'old_email': old_email,
               'new_email': new_email})

def compute_irc_user_fullname(email):
    return email.split("@")[0] + " (IRC)"

def compute_jabber_user_fullname(email):
    return email.split("@")[0] + " (XMPP)"

def compute_mit_user_fullname(email):
    try:
        # Input is either e.g. starnine@mit.edu or user|CROSSREALM.INVALID@mit.edu
        match_user = re.match(r'^([a-zA-Z0-9_.-]+)(\|.+)?@mit\.edu$', email.lower())
        if match_user and match_user.group(2) is None:
            answer = DNS.dnslookup(
                "%s.passwd.ns.athena.mit.edu" % (match_user.group(1),),
                DNS.Type.TXT)
            hesiod_name = answer[0][0].split(':')[4].split(',')[0].strip()
            if hesiod_name != "":
                return hesiod_name
        elif match_user:
            return match_user.group(1).lower() + "@" + match_user.group(2).upper()[1:]
    except DNS.Base.ServerError:
        pass
    except:
        print ("Error getting fullname for %s:" % (email,))
        traceback.print_exc()
    return email.lower()

@cache_with_key(lambda realm, email, f: user_profile_by_email_cache_key(email),
                timeout=3600*24*7)
def create_mirror_user_if_needed(realm, email, email_to_fullname):
    try:
        return get_user_profile_by_email(email)
    except UserProfile.DoesNotExist:
        try:
            # Forge a user for this person
            return create_user(email, initial_password(email), realm,
                               email_to_fullname(email), email_to_username(email),
                               active=False, is_mirror_dummy=True)
        except IntegrityError:
            return get_user_profile_by_email(email)

def log_message(message):
    if not message.sending_client.name.startswith("test:"):
        log_event(message.to_log_dict())

def always_push_notify(user):
    # robinhood.io asked to get push notifications for **all** notifyable
    # messages, regardless of idle status
    return user.realm.domain in ['zulip.com', 'robinhood.io']

# Helper function. Defaults here are overriden by those set in do_send_messages
def do_send_message(message, rendered_content = None, no_log = False, stream = None, local_id = None):
    return do_send_messages([{'message': message,
                              'rendered_content': rendered_content,
                              'no_log': no_log,
                              'stream': stream,
                              'local_id': local_id}])[0]

def do_send_messages(messages):
    # Filter out messages which didn't pass internal_prep_message properly
    messages = [message for message in messages if message is not None]

    # Filter out zephyr mirror anomalies where the message was already sent
    already_sent_ids = []
    new_messages = []
    for message in messages:
        if isinstance(message['message'], int):
            already_sent_ids.append(message['message'])
        else:
            new_messages.append(message)
    messages = new_messages

    # For consistency, changes to the default values for these gets should also be applied
    # to the default args in do_send_message
    for message in messages:
        message['rendered_content'] = message.get('rendered_content', None)
        message['no_log'] = message.get('no_log', False)
        message['stream'] = message.get('stream', None)
        message['local_id'] = message.get('local_id', None)
        message['sender_queue_id'] = message.get('sender_queue_id', None)

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
            # We use select_related()/only() here, while the PERSONAL case above uses
            # get_user_profile_by_id() to get UserProfile objects from cache.  Streams will
            # typically have more recipients than PMs, so get_user_profile_by_id() would be
            # a bit more expensive here, given that we need to hit the DB anyway and only
            # care about the email from the user profile.
            fields = [
                'user_profile__id',
                'user_profile__email',
                'user_profile__is_active',
                'user_profile__realm__domain'
            ]
            query = Subscription.objects.select_related("user_profile", "user_profile__realm").only(*fields).filter(
                recipient=message['message'].recipient, active=True)
            message['recipients'] = [s.user_profile for s in query]
        else:
            raise ValueError('Bad recipient type')

        # Only deliver the message to active user recipients
        message['active_recipients'] = filter(lambda user_profile: user_profile.is_active,
                                              message['recipients'])
        message['message'].maybe_render_content(None)

    # Save the message receipts in the database
    user_message_flags = defaultdict(dict)
    with transaction.commit_on_success():
        Message.objects.bulk_create([message['message'] for message in messages])
        ums = []
        for message in messages:
            ums_to_create = [UserMessage(user_profile=user_profile, message=message['message'])
                             for user_profile in message['active_recipients']]

            # These properties on the Message are set via
            # Message.render_markdown by code in the bugdown inline patterns
            wildcard = message['message'].mentions_wildcard
            mentioned_ids = message['message'].mentions_user_ids
            ids_with_alert_words = message['message'].user_ids_with_alert_words

            for um in ums_to_create:
                if um.user_profile.id == message['message'].sender.id and \
                        message['message'].sent_by_human():
                    um.flags |= UserMessage.flags.read
                if wildcard:
                    um.flags |= UserMessage.flags.wildcard_mentioned
                if um.user_profile_id in mentioned_ids:
                    um.flags |= UserMessage.flags.mentioned
                if um.user_profile_id in ids_with_alert_words:
                    um.flags |= UserMessage.flags.has_alert_word
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
        sender = message['message'].sender
        user_presences = get_status_dict(sender)
        presences = {}
        for user_profile in message['active_recipients']:
            if user_profile.email in user_presences:
                presences[user_profile.id] = user_presences[user_profile.email]

        data = dict(
            type         = 'new_message',
            message      = message['message'].id,
            presences    = presences,
            users        = [{'id': user.id,
                             'flags': user_flags.get(user.id, []),
                             'always_push_notify': always_push_notify(user)}
                            for user in message['active_recipients']])
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
            if message['stream'].invite_only:
                data['invite_only'] = True
        if message['local_id'] is not None:
            data['local_id'] = message['local_id']
        if message['sender_queue_id'] is not None:
            data['sender_queue_id'] = message['sender_queue_id']
        tornado_callbacks.send_notification(data)
        if (settings.ENABLE_FEEDBACK and
            message['message'].recipient.type == Recipient.PERSONAL and
            settings.FEEDBACK_BOT in [up.email for up in message['recipients']]):
            queue_json_publish(
                    'feedback_messages',
                    message['message'].to_dict(apply_markdown=False),
                    lambda x: None
            )

    # Note that this does not preserve the order of message ids
    # returned.  In practice, this shouldn't matter, as we only
    # mirror single zephyr messages at a time and don't otherwise
    # intermingle sending zephyr messages with other messages.
    return already_sent_ids + [message['message'].id for message in messages]

def do_create_stream(realm, stream_name):
    # This is used by a management command now, mostly to facilitate testing.  It
    # doesn't simulate every single aspect of creating a subscription; for example,
    # we don't send Zulips to users to tell them they have been subscribed.
    stream = Stream()
    stream.realm = realm
    stream.name = stream_name
    stream.save()
    Recipient.objects.create(type_id=stream.id, type=Recipient.STREAM)
    subscribers = UserProfile.objects.filter(realm=realm, is_active=True, is_bot=False)
    bulk_add_subscriptions([stream], subscribers)

def create_stream_if_needed(realm, stream_name, invite_only=False):
    (stream, created) = Stream.objects.get_or_create(
        realm=realm, name__iexact=stream_name,
        defaults={'name': stream_name, 'invite_only': invite_only})
    if created:
        Recipient.objects.create(type_id=stream.id, type=Recipient.STREAM)
    return stream, created

def recipient_for_emails(emails, not_forged_mirror_message,
                         user_profile, sender):
    recipient_profile_ids = set()
    realm_domains = set()
    realm_domains.add(sender.realm.domain)
    for email in emails:
        try:
            user_profile = get_user_profile_by_email(email)
        except UserProfile.DoesNotExist:
            raise ValidationError("Invalid email '%s'" % (email,))
        recipient_profile_ids.add(user_profile.id)
        realm_domains.add(user_profile.realm.domain)

    if not_forged_mirror_message and user_profile.id not in recipient_profile_ids:
        raise ValidationError("User not authorized for this query")

    # Prevent cross realm private messages unless it is between only two realms
    # and one of the realms is zulip.com.
    if len(realm_domains) == 2 and 'zulip.com' not in realm_domains:
        raise ValidationError("You can't send private messages outside of your organization.")
    if len(realm_domains) > 2:
        raise ValidationError("You can't send private messages outside of your organization.")

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

def already_sent_mirrored_message_id(message):
    if message.recipient.type == Recipient.HUDDLE:
        # For huddle messages, we use a 10-second window because the
        # timestamps aren't guaranteed to actually match between two
        # copies of the same message.
        time_window = datetime.timedelta(seconds=10)
    else:
        time_window = datetime.timedelta(seconds=0)

    messages =  Message.objects.filter(
        sender=message.sender,
        recipient=message.recipient,
        content=message.content,
        subject=message.subject,
        sending_client=message.sending_client,
        pub_date__gte=message.pub_date - time_window,
        pub_date__lte=message.pub_date + time_window)

    if messages.exists():
        return messages[0].id
    return None

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
# Returns the id of the sent message.  Has same argspec as check_message.
def check_send_message(*args, **kwargs):
    message = check_message(*args, **kwargs)
    return do_send_messages([message])[0]

def check_stream_name(stream_name):
    if stream_name == "":
        raise JsonableError("Stream can't be empty")
    if len(stream_name) > Stream.MAX_NAME_LENGTH:
        raise JsonableError("Stream name too long")
    if not valid_stream_name(stream_name):
        raise JsonableError("Invalid stream name")

def send_pm_if_empty_stream(sender, stream, stream_name):
    if sender.realm.domain == 'mit.edu':
        return

    if sender.is_bot and sender.bot_owner is not None:
        if stream:
            num_subscribers = stream.num_subscribers()

        if stream is None or num_subscribers == 0:
            # Warn a bot's owner if they are sending a message to a stream
            # that does not exist, or has no subscribers
            # We warn the user once every 5 minutes to avoid a flood of
            # PMs on a misconfigured integration, re-using the
            # UserProfile.last_reminder field, which is not used for bots.
            last_reminder = sender.last_reminder_tzaware()
            waitperiod = datetime.timedelta(minutes=UserProfile.BOT_OWNER_STREAM_ALERT_WAITPERIOD)
            if not last_reminder or timezone.now() - last_reminder > waitperiod:
                if stream is None:
                    error_msg = "that stream does not yet exist. To create it, "
                elif num_subscribers == 0:
                    error_msg = "there are no subscribers to that stream. To join it, "

                content = ("Hi there! We thought you'd like to know that your bot **%s** just "
                           "tried to send a message to stream `%s`, but %s"
                           "click the gear in the left-side stream list." %
                           (sender.full_name, stream_name, error_msg))
                message = internal_prep_message(settings.NOTIFICATION_BOT, "private",
                                                sender.bot_owner.email, "", content)
                do_send_messages([message])

                sender.last_reminder = timezone.now()
                sender.save(update_fields=['last_reminder'])

# check_message:
# Returns message ready for sending with do_send_message on success or the error message (string) on error.
def check_message(sender, client, message_type_name, message_to,
                  subject_name, message_content, realm=None, forged=False,
                  forged_timestamp=None, forwarder_user_profile=None, local_id=None,
                  sender_queue_id=None):
    stream = None
    if len(message_to) == 0:
        raise JsonableError("Message must have recipients")
    if len(message_content.strip()) == 0:
        raise JsonableError("Message must not be empty")
    message_content = truncate_body(message_content)

    if realm is None:
        realm = sender.realm

    if message_type_name == 'stream':
        if len(message_to) > 1:
            raise JsonableError("Cannot send to multiple streams")

        stream_name = message_to[0].strip()
        check_stream_name(stream_name)

        if subject_name is None:
            raise JsonableError("Missing topic")
        subject = subject_name.strip()
        if subject == "":
            raise JsonableError("Topic can't be empty")
        subject = truncate_topic(subject)
        ## FIXME: Commented out temporarily while we figure out what we want
        # if not valid_stream_name(subject):
        #     return json_error("Invalid subject name")

        stream = get_stream(stream_name, realm)

        send_pm_if_empty_stream(sender, stream, stream_name)

        if stream is None:
            raise JsonableError("Stream does not exist")
        recipient = get_recipient(Recipient.STREAM, stream.id)

        if not stream.invite_only:
            # This is a public stream
            pass
        elif subscribed_to_stream(sender, stream):
            # Or it is private, but your are subscribed
            pass
        elif is_super_user(sender) or is_super_user(forwarder_user_profile):
            # Or this request is being done on behalf of a super user
            pass
        elif sender.is_bot and subscribed_to_stream(sender.bot_owner, stream):
            # Or you're a bot and your owner is subscribed.
            pass
        else:
            # All other cases are an error.
            raise JsonableError("Not authorized to send to stream '%s'" % (stream.name,))

    elif message_type_name == 'private':
        mirror_message = client and client.name in ["zephyr_mirror", "irc_mirror", "jabber_mirror"]
        not_forged_mirror_message = mirror_message and not forged
        try:
            recipient = recipient_for_emails(message_to, not_forged_mirror_message,
                                             forwarder_user_profile, sender)
        except ValidationError, e:
            assert isinstance(e.messages[0], basestring)
            raise JsonableError(e.messages[0])
    else:
        raise JsonableError("Invalid message type")

    message = Message()
    message.sender = sender
    message.content = message_content
    message.recipient = recipient
    if message_type_name == 'stream':
        message.subject = subject
    if forged and forged_timestamp is not None:
        # Forged messages come with a timestamp
        message.pub_date = timestamp_to_datetime(forged_timestamp)
    else:
        message.pub_date = timezone.now()
    message.sending_client = client

    if not message.maybe_render_content(realm.domain):
        raise JsonableError("Unable to render message")

    if client.name == "zephyr_mirror":
        id = already_sent_mirrored_message_id(message)
        if id is not None:
            return {'message': id}

    return {'message': message, 'stream': stream, 'local_id': local_id, 'sender_queue_id': sender_queue_id}

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

    try:
        return check_message(sender, get_client("Internal"), recipient_type_name,
                             parsed_recipients, subject, content, realm)
    except JsonableError, e:
        logging.error("Error queueing internal message by %s: %s" % (sender_email, str(e)))

    return None

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

def validate_user_access_to_subscribers(user_profile, stream):
    """ Validates whether the user can view the subscribers of a stream.  Raises a JsonableError if:
        * The user and the stream are in different realms
        * The realm is MIT and the stream is not invite only.
        * The stream is invite only, requesting_user is passed, and that user
          does not subscribe to the stream.
    """
    return validate_user_access_to_subscribers_helper(
        user_profile,
        {"realm__domain": stream.realm.domain,
         "realm_id": stream.realm_id,
         "invite_only": stream.invite_only},
        # We use a lambda here so that we only compute whether the
        # user is subscribed if we have to
        lambda: subscribed_to_stream(user_profile, stream))

def validate_user_access_to_subscribers_helper(user_profile, stream_dict, check_user_subscribed):
    """ Helper for validate_user_access_to_subscribers that doesn't require a full stream object
    * check_user_subscribed is a function that when called with no
      arguments, will report whether the user is subscribed to the stream
    """
    if user_profile is not None and user_profile.realm_id != stream_dict["realm_id"]:
        raise ValidationError("Requesting user not on given realm")

    if stream_dict["realm__domain"] == "mit.edu" and not stream_dict["invite_only"]:
        raise JsonableError("You cannot get subscribers for public streams in this realm")

    if (user_profile is not None and stream_dict["invite_only"] and
        not check_user_subscribed()):
        raise JsonableError("Unable to retrieve subscribers for invite-only stream")

# sub_dict is a dictionary mapping stream_id => whether the user is subscribed to that stream
def bulk_get_subscriber_user_ids(stream_dicts, user_profile, sub_dict):
    target_stream_dicts = []
    for stream_dict in stream_dicts:
        try:
            validate_user_access_to_subscribers_helper(user_profile, stream_dict,
                                                       lambda: sub_dict[stream_dict["id"]])
        except JsonableError:
            continue
        target_stream_dicts.append(stream_dict)

    subscriptions = Subscription.objects.select_related("recipient").filter(
        recipient__type=Recipient.STREAM,
        recipient__type_id__in=[stream["id"] for stream in target_stream_dicts],
        user_profile__is_active=True,
        active=True).values("user_profile_id", "recipient__type_id")

    result = dict((stream["id"], []) for stream in stream_dicts)
    for sub in subscriptions:
        result[sub["recipient__type_id"]].append(sub["user_profile_id"])

    return result

def get_subscribers_query(stream, requesting_user):
    """ Build a query to get the subscribers list for a stream, raising a JsonableError if:

    'stream' can either be a string representing a stream name, or a Stream
    object. If it's a Stream object, 'realm' is optional.

    The caller can refine this query with select_related(), values(), etc. depending
    on whether it wants objects or just certain fields
    """
    validate_user_access_to_subscribers(requesting_user, stream)

    # Note that non-active users may still have "active" subscriptions, because we
    # want to be able to easily reactivate them with their old subscriptions.  This
    # is why the query here has to look at the UserProfile.is_active flag.
    subscriptions = Subscription.objects.filter(recipient__type=Recipient.STREAM,
                                                recipient__type_id=stream.id,
                                                user_profile__is_active=True,
                                                active=True)
    return subscriptions

def get_subscribers(stream, requesting_user=None):
    subscriptions = get_subscribers_query(stream, requesting_user).select_related()
    return [subscription.user_profile for subscription in subscriptions]

def get_subscriber_emails(stream, requesting_user=None):
    subscriptions = get_subscribers_query(stream, requesting_user)
    subscriptions = subscriptions.values('user_profile__email')
    return [subscription['user_profile__email'] for subscription in subscriptions]

def get_subscriber_ids(stream):
    try:
        subscriptions = get_subscribers_query(stream, None)
    except JsonableError:
        return []

    rows = subscriptions.values('user_profile_id')
    ids = [row['user_profile_id'] for row in rows]
    return ids

def get_other_subscriber_ids(stream, user_profile_id):
    ids = get_subscriber_ids(stream)
    return filter(lambda id: id != user_profile_id, ids)

def maybe_get_subscriber_emails(stream):
    """ Alternate version of get_subscriber_emails that takes a Stream object only
    (not a name), and simply returns an empty list if unable to get a real
    subscriber list (because we're on the MIT realm). """
    try:
        subscribers = get_subscriber_emails(stream)
    except JsonableError:
        subscribers = []
    return subscribers

def set_stream_color(user_profile, stream_name, color=None):
    subscription = get_subscription(stream_name, user_profile)
    if not color:
        color = pick_color(user_profile)
    subscription.color = color
    subscription.save(update_fields=["color"])
    return color

def get_subscribers_to_streams(streams):
    """ Return a dict where the keys are user profiles, and the values are
    arrays of all the streams within 'streams' to which that user is
    subscribed.
    """
    subscribes_to = {}
    for stream in streams:
        try:
            subscribers = get_subscribers(stream)
        except JsonableError:
            # We can't get a subscriber list for this stream. Probably MIT.
            continue

        for subscriber in subscribers:
            if subscriber not in subscribes_to:
                subscribes_to[subscriber] = []
            subscribes_to[subscriber].append(stream)

    return subscribes_to

def notify_subscriptions_added(user_profile, sub_pairs, stream_emails, no_log=False):
    if not no_log:
        log_event({'type': 'subscription_added',
                   'user': user_profile.email,
                   'names': [stream.name for sub, stream in sub_pairs],
                   'domain': stream.realm.domain})

    # Send a notification to the user who subscribed.
    payload = [dict(name=stream.name,
                    in_home_view=subscription.in_home_view,
                    invite_only=stream.invite_only,
                    color=subscription.color,
                    email_address=encode_email_address(stream),
                    notifications=subscription.notifications,
                    subscribers=stream_emails(stream))
            for (subscription, stream) in sub_pairs]
    notice = dict(event=dict(type="subscriptions", op="add",
                             subscriptions=payload),
                  users=[user_profile.id])
    tornado_callbacks.send_notification(notice)

def notify_for_streams_by_default(user_profile):
    # For users in older realms and CUSTOMER19, do not generate notifications
    # for stream messages by default. Everyone else uses the setting on the
    # user_profile.

    if (user_profile.realm.domain in ["customer19.invalid", "customer25.invalid"] or
        user_profile.realm.date_created <= datetime.datetime(2013, 9, 24,
                                                             tzinfo=timezone.utc)):
        return False

    return user_profile.default_desktop_notifications



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
                                  color=color, recipient_id=recipient_id,
                                  notifications=notify_for_streams_by_default(user_profile))
        subs_by_user[user_profile.id].append(sub_to_add)
        subs_to_add.append((sub_to_add, stream))
    Subscription.objects.bulk_create([sub for (sub, stream) in subs_to_add])
    Subscription.objects.filter(id__in=[sub.id for (sub, stream_name) in subs_to_activate]).update(active=True)

    # Notify all existing users on streams that users have joined

    # First, get all users subscribed to the streams that we care about
    # We fetch all subscription information upfront, as it's used throughout
    # the following code and we want to minize DB queries
    all_subs = Subscription.objects.filter(recipient__type=Recipient.STREAM,
                                           recipient__type_id__in=[stream.id for stream in streams],
                                           user_profile__is_active=True,
                                           active=True).select_related('recipient', 'user_profile')

    all_subs_by_stream = defaultdict(list)
    emails_by_stream = defaultdict(list)
    for sub in all_subs:
        all_subs_by_stream[sub.recipient.type_id].append(sub.user_profile)
        emails_by_stream[sub.recipient.type_id].append(sub.user_profile.email)

    def fetch_stream_subscriber_emails(stream):
        if stream.realm.domain == "mit.edu" and not stream.invite_only:
            return []
        return emails_by_stream[stream.id]

    sub_tuples_by_user = defaultdict(list)
    new_streams = set()
    for (sub, stream) in subs_to_add + subs_to_activate:
        sub_tuples_by_user[sub.user_profile.id].append((sub, stream))
        new_streams.add((sub.user_profile.id, stream.id))

    for user_profile in users:
        if len(sub_tuples_by_user[user_profile.id]) == 0:
            continue
        sub_pairs = sub_tuples_by_user[user_profile.id]
        notify_subscriptions_added(user_profile, sub_pairs, fetch_stream_subscriber_emails)

    for stream in streams:
        if stream.realm.domain == "mit.edu" and not stream.invite_only:
            continue

        new_users = [user for user in users if (user.id, stream.id) in new_streams]
        new_user_ids = [user.id for user in new_users]
        all_subscribed_ids = [user.id for user in all_subs_by_stream[stream.id]]
        other_user_ids = set(all_subscribed_ids) - set(new_user_ids)
        if other_user_ids:
            for user_profile in new_users:
                notice = dict(event=dict(type="subscriptions", op="peer_add",
                                         subscriptions=[stream.name],
                                         user_email=user_profile.email),
                              users=other_user_ids)
                tornado_callbacks.send_notification(notice)

    return ([(user_profile, stream_name) for (user_profile, recipient_id, stream_name) in new_subs] +
            [(sub.user_profile, stream_name) for (sub, stream_name) in subs_to_activate],
            already_subscribed)

# When changing this, also change bulk_add_subscriptions
def do_add_subscription(user_profile, stream, no_log=False):
    recipient = get_recipient(Recipient.STREAM, stream.id)
    color = pick_color(user_profile)
    (subscription, created) = Subscription.objects.get_or_create(
        user_profile=user_profile, recipient=recipient,
        defaults={'active': True, 'color': color,
                  'notifications': notify_for_streams_by_default(user_profile)})
    did_subscribe = created
    if not subscription.active:
        did_subscribe = True
        subscription.active = True
        subscription.save(update_fields=["active"])

    if did_subscribe:

        emails_by_stream = {stream.id: maybe_get_subscriber_emails(stream)}
        notify_subscriptions_added(user_profile, [(subscription, stream)], lambda stream: emails_by_stream[stream.id], no_log)

        user_ids = get_other_subscriber_ids(stream, user_profile.id)
        notice = dict(event=dict(type="subscriptions", op="peer_add",
                                 subscriptions=[stream.name],
                                 user_email=user_profile.email),
                      users=user_ids)
        tornado_callbacks.send_notification(notice)

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

    # As with a subscription add, send a 'peer subscription' notice to other
    # subscribers so they know the user unsubscribed.
    # FIXME: This code was mostly a copy-paste from notify_subscriptions_added.
    #        We have since streamlined how we do notifications for adds, and
    #        we should do the same for removes.
    notifications_for = get_subscribers_to_streams(streams)

    for event_recipient, notifications in notifications_for.iteritems():
        # Don't send a peer subscription notice to yourself.
        if event_recipient == user_profile:
            continue

        stream_names = [stream.name for stream in notifications]
        notice = dict(event=dict(type="subscriptions", op="peer_remove",
                                 subscriptions=stream_names,
                                 user_email=user_profile.email),
                      users=[event_recipient.id])
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
    user_profile.is_mirror_dummy = False
    user_profile.set_password(initial_password(user_profile.email))
    user_profile.date_joined = join_date
    user_profile.save(update_fields=["is_active", "date_joined", "password",
                                     "is_mirror_dummy"])

    if log:
        domain = user_profile.realm.domain
        log_event({'type': 'user_activated',
                   'user': user_profile.email,
                   'domain': domain})

    notify_created_user(user_profile)

def do_reactivate_user(user_profile):
    # Unlike do_activate_user, this is meant for re-activating existing users,
    # so it doesn't reset their password, etc.
    user_profile.is_active = True
    user_profile.save(update_fields=["is_active"])

    domain = user_profile.realm.domain
    log_event({'type': 'user_reactivated',
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
                  users=active_user_ids(user_profile.realm))
    tornado_callbacks.send_notification(notice)

def do_change_is_admin(user_profile, is_admin):
    if is_admin:
        assign_perm('administer', user_profile, user_profile.realm)
    else:
        remove_perm('administer', user_profile, user_profile.realm)

    notice = dict(event=dict(type="realm_user", op="update",
                             person=dict(email=user_profile.email,
                                         is_admin=is_admin)),
                  users=active_user_ids(user_profile.realm))
    tornado_callbacks.send_notification(notice)


def do_make_stream_public(user_profile, realm, stream_name):
    stream_name = stream_name.strip()
    stream = get_stream(stream_name, realm)

    if not stream:
        raise JsonableError('Unknown stream "%s"' % (stream_name,))

    if not subscribed_to_stream(user_profile, stream):
        raise JsonableError('You are not invited to this stream.')

    stream.invite_only = False
    stream.save(update_fields=['invite_only'])
    return {}

def do_make_stream_private(realm, stream_name):
    stream_name = stream_name.strip()
    stream = get_stream(stream_name, realm)

    if not stream:
        raise JsonableError('Unknown stream "%s"' % (stream_name,))

    stream.invite_only = True
    stream.save(update_fields=['invite_only'])
    return {}

def do_rename_stream(realm, old_name, new_name, log=True):
    old_name = old_name.strip()
    new_name = new_name.strip()

    stream = get_stream(old_name, realm)

    if not stream:
        raise JsonableError('Unknown stream "%s"' % (old_name,))

    # Will raise if there's an issue.
    check_stream_name(new_name)

    if get_stream(new_name, realm) and old_name.lower() != new_name.lower():
        raise JsonableError('Stream name "%s" is already taken' % (new_name,))

    old_name = stream.name
    stream.name = new_name
    stream.save(update_fields=["name"])

    if log:
        log_event({'type': 'stream_name_change',
                   'domain': realm.domain,
                   'new_name': new_name})

    recipient = get_recipient(Recipient.STREAM, stream.id)
    messages = Message.objects.filter(recipient=recipient).only("id")

    # Update the display recipient and stream, which are easy single
    # items to set.
    old_cache_key = get_stream_cache_key(old_name, realm)
    new_cache_key = get_stream_cache_key(stream.name, realm)
    if old_cache_key != new_cache_key:
        cache_delete(old_cache_key)
        cache_set(new_cache_key, stream)
    cache_set(display_recipient_cache_key(recipient.id), stream.name)

    # Delete cache entries for everything else, which is cheaper and
    # clearer than trying to set them. display_recipient is the out of
    # date field in all cases.
    cache_delete_many(message_cache_key(message.id) for message in messages)
    cache_delete_many(
        to_dict_cache_key_id(message.id, True) for message in messages)
    cache_delete_many(
        to_dict_cache_key_id(message.id, False) for message in messages)

    # We will tell our users to essentially
    # update stream.name = new_name where name = old_name
    event = dict(
        op="update",
        type="stream",
        property="name",
        value=new_name,
        name=old_name
    )
    notice = dict(event=event, users=active_user_ids(realm))

    tornado_callbacks.send_notification(notice)

    # Even though the token doesn't change, the web client needs to update the
    # email forwarding address to display the correctly-escaped new name.
    return {"email_address": encode_email_address(stream)}

def do_create_realm(domain, name, restricted_to_domain=True):
    realm = get_realm(domain)
    created = not realm
    if created:
        realm = Realm(domain=domain, name=name,
                      restricted_to_domain=restricted_to_domain)
        realm.save()

        # Create stream once Realm object has been saved
        notifications_stream, _ = create_stream_if_needed(realm, Realm.NOTIFICATION_STREAM_NAME)
        realm.notifications_stream = notifications_stream
        realm.save(update_fields=['notifications_stream'])

        # Include a welcome message in this notifications stream
        content = """Welcome to Zulip!

This is a message sent to the `zulip` stream, used for system-generated notifications.
Feel free to reply to say hello, though I am a bot so I won't be able to respond!"""
        msg = internal_prep_message(settings.NOTIFICATION_BOT, 'stream',
                                     notifications_stream.name, "Welcome",
                                     content, realm=realm)
        do_send_messages([msg])

        # Log the event
        log_event({"type": "realm_created",
                   "domain": domain,
                   "restricted_to_domain": restricted_to_domain})

        if settings.NEW_USER_BOT is not None:
            signup_message = "Signups enabled"
            if not restricted_to_domain:
                signup_message += " (open realm)"
            internal_send_message(settings.NEW_USER_BOT, "stream",
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

def do_change_enable_offline_push_notifications(user_profile, offline_push_notifications, log=True):
    user_profile.enable_offline_push_notifications = offline_push_notifications
    user_profile.save(update_fields=["enable_offline_push_notifications"])
    if log:
        log_event({'type': 'enable_offline_push_notifications_changed',
                   'user': user_profile.email,
                   'enable_offline_push_notifications': offline_push_notifications})

def do_change_enable_digest_emails(user_profile, enable_digest_emails, log=True):
    user_profile.enable_digest_emails = enable_digest_emails
    user_profile.save(update_fields=["enable_digest_emails"])

    if not enable_digest_emails:
        # Remove any digest emails that have been enqueued.
        clear_followup_emails_queue(user_profile.email)

    if log:
        log_event({'type': 'enable_digest_emails',
                   'user': user_profile.email,
                   'enable_digest_emails': enable_digest_emails})

def do_change_autoscroll_forever(user_profile, autoscroll_forever, log=True):
    user_profile.autoscroll_forever = autoscroll_forever
    user_profile.save(update_fields=["autoscroll_forever"])

    if log:
        log_event({'type': 'autoscroll_forever',
                   'user': user_profile.email,
                   'autoscroll_forever': autoscroll_forever})

def do_change_enter_sends(user_profile, enter_sends):
    user_profile.enter_sends = enter_sends
    user_profile.save(update_fields=["enter_sends"])

def do_change_default_desktop_notifications(user_profile, default_desktop_notifications):
    user_profile.default_desktop_notifications = default_desktop_notifications
    user_profile.save(update_fields=["default_desktop_notifications"])

def set_default_streams(realm, stream_names):
    DefaultStream.objects.filter(realm=realm).delete()
    for stream_name in stream_names:
        stream, _ = create_stream_if_needed(realm, stream_name)
        DefaultStream.objects.create(stream=stream, realm=realm)

    # All realms get a notifications stream by default
    notifications_stream, _ = create_stream_if_needed(realm, Realm.NOTIFICATION_STREAM_NAME)
    DefaultStream.objects.create(stream=notifications_stream, realm=realm)

    log_event({'type': 'default_streams',
               'domain': realm.domain,
               'streams': stream_names})

def get_default_subs(user_profile):
    return [default.stream for default in
            DefaultStream.objects.select_related("stream", "stream__realm").filter(realm=user_profile.realm)]

def do_update_user_activity_interval(user_profile, log_time):
    effective_end = log_time + datetime.timedelta(minutes=15)

    # This code isn't perfect, because with various races we might end
    # up creating two overlapping intervals, but that shouldn't happen
    # often, and can be corrected for in post-processing
    try:
        last = UserActivityInterval.objects.filter(user_profile=user_profile).order_by("-end")[0]
        # There are two ways our intervals could overlap:
        # (1) The start of the new interval could be inside the old interval
        # (2) The end of the new interval could be inside the old interval
        # In either case, we just extend the old interval to include the new interval.
        if ((log_time <= last.end and log_time >= last.start) or
            (effective_end <= last.end and effective_end >= last.start)):
            last.end = max(last.end, effective_end)
            last.start = min(last.start, log_time)
            last.save(update_fields=["start", "end"])
            return
    except IndexError:
        pass

    # Otherwise, the intervals don't overlap, so we should make a new one
    UserActivityInterval.objects.create(user_profile=user_profile, start=log_time,
                                        end=effective_end)

@statsd_increment('user_activity')
def do_update_user_activity(user_profile, client, query, log_time):
    (activity, created) = UserActivity.objects.get_or_create(
        user_profile = user_profile,
        client = client,
        query = query,
        defaults={'last_visit': log_time, 'count': 0})

    activity.count += 1
    activity.last_visit = log_time
    activity.save(update_fields=["last_visit", "count"])

def send_presence_changed(user_profile, presence):
    presence_dict = presence.to_dict()
    notice = dict(event=dict(type="presence", email=user_profile.email,
                             server_timestamp=time.time(),
                             presence={presence_dict['client']: presence.to_dict()}),
                  users=active_user_ids(user_profile.realm))
    tornado_callbacks.send_notification(notice)

@statsd_increment('user_presence')
def do_update_user_presence(user_profile, client, log_time, status):
    (presence, created) = UserPresence.objects.get_or_create(
        user_profile = user_profile,
        client = client,
        defaults = {'timestamp': log_time,
                    'status': status})

    stale_status = (log_time - presence.timestamp) > datetime.timedelta(minutes=1, seconds=10)
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
        # user without delay.  Note that we won't send an update here for a
        # timestamp update, because we rely on the browser to ping us every 50
        # seconds for realm-wide status updates, and those updates should have
        # recent timestamps, which means the browser won't think active users
        # have gone idle.  If we were more aggressive in this function about
        # sending timestamp updates, we could eliminate the ping responses, but
        # that's not a high priority for now, considering that most of our non-MIT
        # realms are pretty small.
        send_presence_changed(user_profile, presence)

def update_user_activity_interval(user_profile, log_time):
    event={'user_profile_id': user_profile.id,
           'time': datetime_to_timestamp(log_time)}
    queue_json_publish("user_activity_interval", event,
                       lambda e: do_update_user_activity_interval(user_profile, log_time))

def update_user_presence(user_profile, client, log_time, status,
                         new_user_input):
    event={'user_profile_id': user_profile.id,
           'status': status,
           'time': datetime_to_timestamp(log_time),
           'client': client.name}

    queue_json_publish("user_presence", event,
                       lambda e: do_update_user_presence(user_profile, client,
                                                         log_time, status))

    if new_user_input:
        update_user_activity_interval(user_profile, log_time)

def do_update_message_flags(user_profile, operation, flag, messages, all):
    flagattr = getattr(UserMessage.flags, flag)

    if all:
        log_statsd_event('bankruptcy')
        msgs = UserMessage.objects.filter(user_profile=user_profile)
    else:
        msgs = UserMessage.objects.filter(user_profile=user_profile,
                                          message__id__in=messages)
        # Hack to let you star any message
        if msgs.count() == 0:
            if not len(messages) == 1:
                raise JsonableError("Invalid message(s)")
            if flag != "starred":
                raise JsonableError("Invalid message(s)")
            # Check that the user could have read the relevant message
            try:
                message = Message.objects.get(id=messages[0])
            except Message.DoesNotExist:
                raise JsonableError("Invalid message(s)")
            recipient = Recipient.objects.get(id=message.recipient_id)
            if recipient.type != Recipient.STREAM:
                raise JsonableError("Invalid message(s)")
            stream = Stream.objects.select_related("realm").get(id=recipient.type_id)
            if not stream.is_public():
                raise JsonableError("Invalid message(s)")

            # OK, this is a message that you legitimately have access
            # to via narrowing to the stream it is on, even though you
            # didn't actually receive it.  So we create a historical,
            # read UserMessage message row for you to star.
            UserMessage.objects.create(user_profile=user_profile,
                                       message=message,
                                       flags=UserMessage.flags.historical | UserMessage.flags.read)

    # The filter() statements below prevent postgres from doing a lot of
    # unnecessary work, which is a big deal for users updating lots of
    # flags (e.g. bankruptcy).  This patch arose from seeing slow calls
    # to /json/update_message_flags in the logs.  The filter() statements
    # are kind of magical; they are actually just testing the one bit.
    if operation == 'add':
        msgs = msgs.filter(flags=~flagattr)
        count = msgs.update(flags=F('flags').bitor(flagattr))
    elif operation == 'remove':
        msgs = msgs.filter(flags=flagattr)
        count = msgs.update(flags=F('flags').bitand(~flagattr))

    event = {'type': 'update_message_flags',
             'operation': operation,
             'flag': flag,
             'messages': messages,
             'all': all}
    log_event(event)
    notice = dict(event=event, users=[user_profile.id])
    tornado_callbacks.send_notification(notice)

    statsd.incr("flags.%s.%s" % (flag, operation), count)

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

def truncate_content(content, max_length, truncation_message):
    if len(content) > max_length:
        content = content[:max_length - len(truncation_message)] + truncation_message
    return content

def truncate_body(body):
    return truncate_content(body, MAX_MESSAGE_LENGTH, "...")

def truncate_topic(topic):
    return truncate_content(topic, MAX_SUBJECT_LENGTH, "...")


def update_user_message_flags(message, ums):
    wildcard = message.mentions_wildcard
    mentioned_ids = message.mentions_user_ids
    ids_with_alert_words = message.user_ids_with_alert_words
    changed_ums = set()

    def update_flag(um, should_set, flag):
        if should_set:
            if not (um.flags & flag):
                um.flags |= flag
                changed_ums.add(um)
        else:
            if (um.flags & flag):
                um.flags &= ~flag
                changed_ums.add(um)

    for um in ums:
        has_alert_word = um.user_profile_id in ids_with_alert_words
        update_flag(um, has_alert_word, UserMessage.flags.has_alert_word)

        mentioned = um.user_profile_id in mentioned_ids
        update_flag(um, mentioned, UserMessage.flags.mentioned)

        update_flag(um, wildcard, UserMessage.flags.wildcard_mentioned)

    for um in changed_ums:
        um.save(update_fields=['flags'])


def do_update_message(user_profile, message_id, subject, propagate_mode, content):
    try:
        message = Message.objects.select_related().get(id=message_id)
    except Message.DoesNotExist:
        raise JsonableError("Unknown message id")

    event = {'type': 'update_message',
             'sender': user_profile.email,
             'message_id': message_id}
    edit_history_event = {}
    changed_messages = [message]

    # You can only edit a message if:
    # 1. You sent it, OR:
    # 2. This is a topic-only edit for a (no topic) message, OR:
    # 3. This is a topic-only edit and you are an admin.
    if message.sender == user_profile:
        pass
    elif (content is None) and ((message.subject == "(no topic)") or
                                user_profile.is_admin()):
        pass
    else:
        raise JsonableError("You don't have permission to edit this message")

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

    ums = UserMessage.objects.filter(message=message_id)

    if content is not None:
        if len(content.strip()) == 0:
            content = "(deleted)"
        content = truncate_body(content)
        rendered_content = message.render_markdown(content)

        if not rendered_content:
            raise JsonableError("We were unable to render your updated message")

        update_user_message_flags(message, ums)

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
        orig_subject = message.subject
        subject = subject.strip()
        if subject == "":
            raise JsonableError("Topic can't be empty")
        subject = truncate_topic(subject)
        event["orig_subject"] = orig_subject
        message.subject = subject
        event["subject"] = subject
        event['subject_links'] = bugdown.subject_links(message.sender.realm.domain.lower(), subject)
        edit_history_event["prev_subject"] = orig_subject


        if propagate_mode in ["change_later", "change_all"]:
            propagate_query = Q(recipient = message.recipient, subject = orig_subject)
            # We only change messages up to 2 days in the past, to avoid hammering our
            # DB by changing an unbounded amount of messages
            if propagate_mode == 'change_all':
                before_bound = now() - datetime.timedelta(days=2)

                propagate_query = propagate_query & ~Q(id = message.id) & \
                                                     Q(pub_date__range=(before_bound, now()))
            if propagate_mode == 'change_later':
                propagate_query = propagate_query & Q(id__gt = message.id)

            messages = Message.objects.filter(propagate_query).select_related();

            # Evaluate the query before running the update
            messages_list = list(messages)
            messages.update(subject=subject)

            for m in messages_list:
                # The cached ORM object is not changed by messages.update()
                # and the memcached update requires the new value
                m.subject = subject

            changed_messages += messages_list

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

    # Update the message as stored in the (deprecated) message
    # cache (for shunting the message over to Tornado in the old
    # get_messages API) and also the to_dict caches.
    items_for_memcached = {}
    event['message_ids'] = []
    for changed_message in changed_messages:
        event['message_ids'].append(changed_message.id)
        items_for_memcached[message_cache_key(changed_message.id)] = (changed_message,)
        items_for_memcached[to_dict_cache_key(changed_message, True)] = \
            (stringify_message_dict(changed_message.to_dict_uncached(apply_markdown=True)),)
        items_for_memcached[to_dict_cache_key(changed_message, False)] = \
            (stringify_message_dict(changed_message.to_dict_uncached(apply_markdown=False)),)
    cache_set_many(items_for_memcached)

    def user_info(um):
        return {
            'id': um.user_profile_id,
            'flags': um.flags_list()
        }
    notice = dict(event=event, users=map(user_info, ums), type='update_message')
    tornado_callbacks.send_notification(notice)

def encode_email_address(stream):
    return encode_email_address_helper(stream.name, stream.email_token)

def encode_email_address_helper(name, email_token):
    # Some deployments may not use the email gateway
    if settings.EMAIL_GATEWAY_PATTERN == '':
        return ''

    # Given the fact that we have almost no restrictions on stream names and
    # that what characters are allowed in e-mail addresses is complicated and
    # dependent on context in the address, we opt for a very simple scheme:
    #
    # Only encode the stream name (leave the + and token alone). Encode
    # everything that isn't alphanumeric plus _ as the percent-prefixed integer
    # ordinal of that character, padded with zeroes to the maximum number of
    # bytes of a UTF-8 encoded Unicode character.
    encoded_name = re.sub("\W", lambda x: "%" + str(ord(x.group(0))).zfill(4), name)
    encoded_token = "%s+%s" % (encoded_name, email_token)
    return settings.EMAIL_GATEWAY_PATTERN % (encoded_token,)

def decode_email_address(email):
    # Perform the reverse of encode_email_address. Returns a tuple of (streamname, email_token)
    pattern_parts = [re.escape(part) for part in settings.EMAIL_GATEWAY_PATTERN.split('%s')]
    match_email_re = re.compile("(.*?)".join(pattern_parts))
    match = match_email_re.match(email)

    if not match:
        return None

    full_address = match.group(1)
    if '.' in full_address:
        # Workaround for Google Groups and other programs that don't accept emails
        # that have + signs in them (see Trac #2102)
        encoded_stream_name, token = full_address.split('.')
    else:
        encoded_stream_name, token = full_address.split('+')
    stream_name = re.sub("%\d{4}", lambda x: unichr(int(x.group(0)[1:])), encoded_stream_name)
    return stream_name, token

# In general, it's better to avoid using .values() because it makes
# the code pretty ugly, but in this case, it has significant
# performance impact for loading / for users with large numbers of
# subscriptions, so it's worth optimizing.
def gather_subscriptions_helper(user_profile):
    sub_dicts = Subscription.objects.select_related("recipient").filter(
        user_profile    = user_profile,
        recipient__type = Recipient.STREAM).values(
        "recipient__type_id", "in_home_view", "color", "notifications", "active")

    stream_ids = [sub["recipient__type_id"] for sub in sub_dicts]

    stream_dicts = Stream.objects.select_related("realm").filter(id__in=stream_ids).values(
        "id", "name", "invite_only", "realm_id", "realm__domain", "email_token")
    stream_hash = {}
    for stream in stream_dicts:
        stream_hash[stream["id"]] = stream

    subscribed = []
    unsubscribed = []

    streams = [stream_hash[sub["recipient__type_id"]] for sub in sub_dicts]
    streams_subscribed_map = dict((sub["recipient__type_id"], sub["active"]) for sub in sub_dicts)
    subscriber_map = bulk_get_subscriber_user_ids(streams, user_profile, streams_subscribed_map)

    for sub in sub_dicts:
        stream = stream_hash[sub["recipient__type_id"]]
        subscribers = subscriber_map[stream["id"]]

        # Important: don't show the subscribers if the stream is invite only
        # and this user isn't on it anymore.
        if stream["invite_only"] and not sub["active"]:
            subscribers = None

        stream_dict = {'name': stream["name"],
                       'in_home_view': sub["in_home_view"],
                       'invite_only': stream["invite_only"],
                       'color': sub["color"],
                       'notifications': sub["notifications"],
                       'email_address': encode_email_address_helper(stream["name"], stream["email_token"])}
        if subscribers is not None:
            stream_dict['subscribers'] = subscribers
        if sub["active"]:
            subscribed.append(stream_dict)
        else:
            unsubscribed.append(stream_dict)

    user_ids = set()
    for subs in [subscribed, unsubscribed]:
        for sub in subs:
            if 'subscribers' in sub:
                for subscriber in sub['subscribers']:
                    user_ids.add(subscriber)
    email_dict = get_emails_from_user_ids(list(user_ids))
    return (sorted(subscribed), sorted(unsubscribed), email_dict)

def gather_subscriptions(user_profile):
    subscribed, unsubscribed, email_dict = gather_subscriptions_helper(user_profile)
    for subs in [subscribed, unsubscribed]:
        for sub in subs:
            if 'subscribers' in sub:
                sub['subscribers'] = [email_dict[user_id] for user_id in sub['subscribers']]

    return (subscribed, unsubscribed)

def get_status_dict(requesting_user_profile):
    # Return no status info for MIT
    if requesting_user_profile.realm.domain == 'mit.edu':
        return defaultdict(dict)

    return UserPresence.get_status_dict_by_realm(requesting_user_profile.realm_id)

# Fetch initial data.  When event_types is not specified, clients want
# all event types.  Whenever you add new code to this function, you
# should also add corresponding events for changes in the data
# structures and new code to apply_events (and add a test in EventsRegisterTest).
def fetch_initial_state_data(user_profile, event_types, queue_id):
    state = {'queue_id': queue_id}
    if event_types is None or "message" in event_types:
        # The client should use get_old_messages() to fetch messages
        # starting with the max_message_id.  They will get messages
        # newer than that ID via get_events()
        messages = Message.objects.filter(usermessage__user_profile=user_profile).order_by('-id')[:1]
        if messages:
            state['max_message_id'] = messages[0].id
        else:
            state['max_message_id'] = -1
    if event_types is None or "pointer" in event_types:
        state['pointer'] = user_profile.pointer
    if event_types is None or "realm_user" in event_types:
        state['realm_users'] = [{'email'     : userdict['email'],
                                 'is_bot'    : userdict['is_bot'],
                                 'full_name' : userdict['full_name']}
                                for userdict in get_active_user_dicts_in_realm(user_profile.realm)]
    if event_types is None or "subscription" in event_types:
        subscriptions, unsubscribed, email_dict = gather_subscriptions_helper(user_profile)
        state['subscriptions'] = subscriptions
        state['unsubscribed'] = unsubscribed
        state['email_dict'] = email_dict
    if event_types is None or "presence" in event_types:
        state['presences'] = get_status_dict(user_profile)
    if event_types is None or "referral" in event_types:
        state['referrals'] = {'granted': user_profile.invites_granted,
                              'used': user_profile.invites_used}
    if event_types is None or "update_message_flags" in event_types:
        # There's no initial data for message flag updates, client will
        # get any updates during a session from get_events()
        pass
    if event_types is None or "realm_emoji" in event_types:
        state['realm_emoji'] = user_profile.realm.get_emoji()
    if event_types is None or "alert_words" in event_types:
        state['alert_words'] = user_alert_words(user_profile)
    if event_types is None or "muted_topics" in event_types:
        state['muted_topics'] = ujson.loads(user_profile.muted_topics)
    if event_types is None or "realm_filters" in event_types:
        state['realm_filters'] = realm_filters_for_domain(user_profile.realm.domain)
    return state

def apply_events(state, events):
    for event in events:
        if event['type'] == "message":
            state['max_message_id'] = max(state['max_message_id'], event['message']['id'])
        elif event['type'] == "pointer":
            state['pointer'] = max(state['pointer'], event['pointer'])
        elif event['type'] == "realm_user":
            person = event['person']

            def our_person(p):
                return p['email'] == person['email']

            if event['op'] == "add":
                state['realm_users'].append(person)
            elif event['op'] == "remove":
                state['realm_users'] = itertools.ifilterfalse(our_person, state['realm_users'])
            elif event['op'] == 'update':
                for p in state['realm_users']:
                    if our_person(p):
                        p.update(person)
        elif event['type'] == 'stream':
            if event['op'] == 'update':
                # For legacy reasons, we call stream data 'subscriptions' in
                # the state var here, for the benefit of the JS code.
                for obj in state['subscriptions']:
                    if obj['name'].lower() == event['name'].lower():
                        obj[event['property']] = event['value']
        elif event['type'] == "subscriptions":
            if event['op'] in ["add"]:
                # Convert the user_profile IDs to emails since that's what register() returns
                # TODO: Clean up this situation
                for item in event["subscriptions"]:
                    item["subscribers"] = [get_user_profile_by_email(email).id for email in item["subscribers"]]
            if event['op'] in ["add", "remove"]:
                subscriptions_to_filter = set(sub['name'].lower() for sub in event["subscriptions"])
            # We add the new subscriptions to the list of streams the
            # user is subscribed to, and also remove/add them from the
            # list of streams the user is not subscribed to (which we
            # are still sending on data about so that e.g. colors and
            # the in_home_view bit are properly available for those streams)
            #
            # And we do the opposite filtering process for unsubscribe events.
            if event['op'] == "add":
                state['subscriptions'] += event['subscriptions']
                state['unsubscribed'] = filter(lambda s: s['name'].lower() not in subscriptions_to_filter,
                                               state['unsubscribed'])
            elif event['op'] == "remove":
                state['unsubscribed'] += event['subscriptions']
                state['subscriptions'] = filter(lambda s: s['name'].lower() not in subscriptions_to_filter,
                                                state['subscriptions'])
            elif event['op'] == 'update':
                for sub in state['subscriptions']:
                    if sub['name'].lower() == event['name'].lower():
                        sub[event['property']] = event['value']
            elif event['op'] == 'peer_add':
                user_id = get_user_profile_by_email(event['user_email']).id
                for sub in state['subscriptions']:
                    if (sub['name'] in event['subscriptions'] and
                        user_id not in sub['subscribers']):
                        sub['subscribers'].append(user_id)
            elif event['op'] == 'peer_remove':
                user_id = get_user_profile_by_email(event['user_email']).id
                for sub in state['subscriptions']:
                    if (sub['name'] in event['subscriptions'] and
                        user_id in sub['subscribers']):
                        sub['subscribers'].remove(user_id)
        elif event['type'] == "presence":
            state['presences'][event['email']] = event['presence']
        elif event['type'] == "update_message":
            # The client will get the updated message directly
            pass
        elif event['type'] == "referral":
            state['referrals'] = event['referrals']
        elif event['type'] == "update_message_flags":
            # The client will get the message with the updated flags directly
            pass
        elif event['type'] == "realm_emoji":
            state['realm_emoji'] = event['realm_emoji']
        elif event['type'] == "alert_words":
            state['alert_words'] = event['alert_words']
        elif event['type'] == "muted_topics":
            state['muted_topics'] = event["muted_topics"]
        elif event['type'] == "realm_filters":
            state['realm_filters'] = event["realm_filters"]
        else:
            raise ValueError("Unexpected event type %s" % (event['type'],))

def do_events_register(user_profile, user_client, apply_markdown=True,
                       event_types=None, queue_lifespan_secs=0, all_public_streams=False,
                       narrow=[]):
    # Technically we don't need to check this here because
    # build_narrow_filter will check it, but it's nicer from an error
    # handling perspective to do it before contacting Tornado
    check_supported_events_narrow_filter(narrow)
    queue_id = request_event_queue(user_profile, user_client, apply_markdown,
                                   queue_lifespan_secs, event_types, all_public_streams,
                                   narrow=narrow)
    if queue_id is None:
        raise JsonableError("Could not allocate event queue")
    if event_types is not None:
        event_types = set(event_types)

    ret = fetch_initial_state_data(user_profile, event_types, queue_id)

    # Apply events that came in while we were fetching initial data
    events = get_user_events(user_profile, queue_id, -1)
    apply_events(ret, events)
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
    subject_template_path = 'confirmation/invite_email_subject.txt'
    body_template_path = 'confirmation/invite_email_body.txt'
    context = {'referrer': referrer,
               'support_email': settings.ZULIP_ADMINISTRATOR,
               'enterprise': settings.ENTERPRISE}

    if referrer.realm.domain == 'mit.edu':
        subject_template_path = 'confirmation/mituser_invite_email_subject.txt'
        body_template_path = 'confirmation/mituser_invite_email_body.txt'

    Confirmation.objects.send_confirmation(
        invitee, invitee.email, additional_context=context,
        subject_template_path=subject_template_path,
        body_template_path=body_template_path)

def hashchange_encode(string):
    # Do the same encoding operation as hashchange.encodeHashComponent on the
    # frontend.
    return urllib.quote(
        string.encode("utf-8")).replace(".", "%2E").replace("%", ".")

def pm_narrow_url(participants):
    participants.sort()
    base_url = "https://%s/#narrow/pm-with/" % (settings.EXTERNAL_HOST,)
    return base_url + hashchange_encode(",".join(participants))

def stream_narrow_url(stream):
    base_url = "https://%s/#narrow/stream/" % (settings.EXTERNAL_HOST,)
    return base_url + hashchange_encode(stream)

def topic_narrow_url(stream, topic):
    base_url = "https://%s/#narrow/stream/" % (settings.EXTERNAL_HOST,)
    return "%s%s/topic/%s" % (base_url, hashchange_encode(stream),
                              hashchange_encode(topic))

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

    def relative_to_full_url(content):
        # URLs for uploaded content are of the form
        # "/user_uploads/abc.png". Make them full paths.
        #
        # There's a small chance of colliding with non-Zulip URLs containing
        # "/user_uploads/", but we don't have much information about the
        # structure of the URL to leverage.
        content = re.sub(
            r"/user_uploads/(\S*)",
            settings.EXTERNAL_HOST + r"/user_uploads/\1", content)

        # Our proxying user-uploaded images seems to break inline images in HTML
        # emails, so scrub the image but leave the link.
        content = re.sub(
            r"<img src=(\S+)/user_uploads/(\S+)>", "", content)

        # URLs for emoji are of the form
        # "static/third/gemoji/images/emoji/snowflake.png".
        content = re.sub(
            r"static/third/gemoji/images/emoji/",
            settings.EXTERNAL_HOST + r"/static/third/gemoji/images/emoji/",
            content)

        return content

    def fix_plaintext_image_urls(content):
        # Replace image URLs in plaintext content of the form
        #     [image name](image url)
        # with a simple hyperlink.
        return re.sub(r"\[(\S*)\]\((\S*)\)", r"\2", content)

    def fix_emoji_sizes(html):
        return html.replace(' class="emoji"', ' height="20px"')

    def build_message_payload(message):
        plain = message.content
        plain = fix_plaintext_image_urls(plain)
        plain = relative_to_full_url(plain)

        html = message.rendered_content
        html = relative_to_full_url(html)
        html = fix_emoji_sizes(html)

        return {'plain': plain, 'html': html}

    def build_sender_payload(message):
        sender = sender_string(message)
        return {'sender': sender,
                'content': [build_message_payload(message)]}

    def message_header(user_profile, message):
        disp_recipient = get_display_recipient(message.recipient)
        if message.recipient.type == Recipient.PERSONAL:
            header = "You and %s" % (message.sender.full_name)
            html_link = pm_narrow_url([message.sender.email])
            header_html = "<a style='color: #ffffff;' href='%s'>%s</a>" % (html_link, header)
        elif message.recipient.type == Recipient.HUDDLE:
            other_recipients = [r['full_name'] for r in disp_recipient
                                    if r['email'] != user_profile.email]
            header = "You and %s" % (", ".join(other_recipients),)
            html_link = pm_narrow_url([r["email"] for r in disp_recipient
                                       if r["email"] != user_profile.email])
            header_html = "<a style='color: #ffffff;' href='%s'>%s</a>" % (html_link, header)
        else:
            header = "%s > %s" % (disp_recipient, message.subject)
            stream_link = stream_narrow_url(disp_recipient)
            topic_link = topic_narrow_url(disp_recipient, message.subject)
            header_html = "<a href='%s'>%s</a> > <a href='%s'>%s</a>" % (
                stream_link, disp_recipient, topic_link, message.subject)
        return {"plain": header,
                "html": header_html,
                "stream_message": message.recipient.type_name() == "stream"}

    # # Collapse message list to
    # [
    #    {
    #       "header": {
    #                   "plain":"header",
    #                   "html":"htmlheader"
    #                 }
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

    messages.sort(key=lambda message: message.pub_date)

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

def unsubscribe_token(user_profile):
    # Leverage the Django confirmations framework to generate and track unique
    # unsubscription tokens.
    return Confirmation.objects.get_link_for_object(user_profile).split("/")[-1]

def one_click_unsubscribe_link(user_profile, endpoint):
    """
    Generate a unique link that a logged-out user can visit to unsubscribe from
    Zulip e-mails without having to first log in.
    """
    token = unsubscribe_token(user_profile)
    base_url = "https://" + settings.EXTERNAL_HOST
    resource_path = "accounts/unsubscribe/%s/%s" % (endpoint, token)
    return "%s/%s" % (base_url.rstrip("/"), resource_path)

@statsd_increment("missed_message_reminders")
def do_send_missedmessage_events(user_profile, missed_messages):
    """
    Send a reminder email and/or push notifications to a user if she's missed some PMs by being offline

    `user_profile` is the user to send the reminder to
    `missed_messages` is a list of Message objects to remind about
    """
    senders = set(m.sender.full_name for m in missed_messages)
    sender_str = ", ".join(senders)
    plural_messages = 's' if len(missed_messages) > 1 else ''
    if user_profile.enable_offline_email_notifications:
        template_payload = {'name': user_profile.full_name,
                            'messages': build_message_list(user_profile, missed_messages),
                            'message_count': len(missed_messages),
                            'url': 'https://%s' % (settings.EXTERNAL_HOST,),
                            'reply_warning': False,
                            'external_host': settings.EXTERNAL_HOST}
        headers = {}
        if all(msg.recipient.type in (Recipient.HUDDLE, Recipient.PERSONAL)
                for msg in missed_messages):
            # If we have one huddle, set a reply-to to all of the members
            # of the huddle except the user herself
            disp_recipients = [", ".join(recipient['email']
                                    for recipient in get_display_recipient(mesg.recipient)
                                        if recipient['email'] != user_profile.email)
                                     for mesg in missed_messages]
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
            headers['Reply-To'] = "Nobody <%s>" % (settings.NOREPLY_EMAIL_ADDRESS,)

        # Give users a one-click unsubscribe link they can use to stop getting
        # missed message emails without having to log in first.
        unsubscribe_link = one_click_unsubscribe_link(user_profile, "missed_messages")
        template_payload["unsubscribe_link"] = unsubscribe_link

        subject = "Missed Zulip%s from %s" % (plural_messages, sender_str)
        from_email = "%s (via Zulip) <%s>" % (sender_str, settings.NOREPLY_EMAIL_ADDRESS)

        text_content = loader.render_to_string('zerver/missed_message_email.txt', template_payload)
        html_content = loader.render_to_string('zerver/missed_message_email_html.txt', template_payload)

        msg = EmailMultiAlternatives(subject, text_content, from_email, [user_profile.email],
                                     headers = headers)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        user_profile.last_reminder = datetime.datetime.now()
        user_profile.save(update_fields=['last_reminder'])

    return

def receives_offline_notifications(user_profile):
    return ((user_profile.enable_offline_email_notifications or
             user_profile.enable_offline_push_notifications) and
            not user_profile.is_bot)

@statsd_increment("push_notifications")
def handle_push_notification(user_profile_id, missed_message):
    try:
        user_profile = get_user_profile_by_id(user_profile_id)
        if not receives_offline_notifications(user_profile):
            return

        umessage = UserMessage.objects.get(user_profile=user_profile,
                                           message__id=missed_message['message_id'])
        message = umessage.message
        if umessage.flags.read:
            return
        sender_str = message.sender.full_name

        apple = num_push_devices_for_user(user_profile, kind=PushDeviceToken.APNS)
        android = num_push_devices_for_user(user_profile, kind=PushDeviceToken.GCM)

        if apple or android:
            #TODO: set badge count in a better way
            # Determine what alert string to display based on the missed messages
            if message.recipient.type == Recipient.HUDDLE:
                alert = "New private group message from %s" % (sender_str,)
            elif message.recipient.type == Recipient.PERSONAL:
                alert = "New private message from %s" % (sender_str,)
            elif message.recipient.type == Recipient.STREAM:
                alert = "New mention from %s" % (sender_str,)
            else:
                alert = "New Zulip mentions and private messages from %s" % (sender_str,)

            if apple:
                apple_extra_data = {'message_ids': [message.id]}
                send_apple_push_notification(user_profile, alert, badge=1, zulip=apple_extra_data)

            if android:
                content = message.content
                content_truncated = (len(content) > 200)
                if content_truncated:
                    content = content[:200] + "..."

                android_data = {
                    'user': user_profile.email,
                    'event': 'message',
                    'alert': alert,
                    'zulip_message_id': message.id, # message_id is reserved for CCS
                    'time': datetime_to_timestamp(message.pub_date),
                    'content': content,
                    'content_truncated': content_truncated,
                    'sender_email': message.sender.email,
                    'sender_full_name': message.sender.full_name,
                    'sender_avatar_url': get_avatar_url(message.sender.avatar_source, message.sender.email),
                }

                if message.recipient.type == Recipient.STREAM:
                    android_data['recipient_type'] = "stream"
                    android_data['stream'] = get_display_recipient(message.recipient)
                    android_data['topic'] = message.subject
                elif message.recipient.type in (Recipient.HUDDLE, Recipient.PERSONAL):
                    android_data['recipient_type'] = "private"

                send_android_push_notification(user_profile, android_data)

    except UserMessage.DoesNotExist:
        logging.error("Could not find UserMessage with message_id %s" %(missed_message['message_id'],))

def handle_missedmessage_emails(user_profile_id, missed_email_events):
    message_ids = [event.get('message_id') for event in missed_email_events]

    user_profile = get_user_profile_by_id(user_profile_id)
    if not receives_offline_notifications(user_profile):
        return

    messages = [um.message for um in UserMessage.objects.filter(user_profile=user_profile,
                                                                message__id__in=message_ids,
                                                                flags=~UserMessage.flags.read)]

    if messages:
        do_send_missedmessage_events(user_profile, messages)

def is_inactive(value):
    try:
        if get_user_profile_by_email(value).is_active:
            raise ValidationError(u'%s is already active' % value)
    except UserProfile.DoesNotExist:
        pass

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

        if user_profile.realm.restricted_to_domain and resolve_email_to_domain(email) != user_profile.realm.domain.lower():
            errors.append((email, "Outside your domain."))
            continue

        try:
            existing_user_profile = get_user_profile_by_email(email)
        except UserProfile.DoesNotExist:
            existing_user_profile = None
        try:
            if existing_user_profile is not None and existing_user_profile.is_mirror_dummy:
                # Mirror dummy users to be activated must be inactive
                is_inactive(email)
            else:
                # Other users should not already exist at all.
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

def send_referral_event(user_profile):
    notice = dict(event=dict(type="referral",
                             referrals=dict(granted=user_profile.invites_granted,
                                            used=user_profile.invites_used)),
                  users=[user_profile.id])
    tornado_callbacks.send_notification(notice)

def do_refer_friend(user_profile, email):
    content = """Referrer: "%s" <%s>
Realm: %s
Referred: %s""" % (user_profile.full_name, user_profile.email, user_profile.realm.domain, email)
    subject = "Zulip referral: %s" % (email,)
    from_email = '"%s" <%s>' % (user_profile.full_name, 'referrals@zulip.com')
    to_email = '"Zulip Referrals" <zulip+referrals@zulip.com>'
    headers = {'Reply-To' : '"%s" <%s>' % (user_profile.full_name, user_profile.email,)}
    msg = EmailMessage(subject, content, from_email, [to_email], headers=headers)
    msg.send()

    referral = Referral(user_profile=user_profile, email=email)
    referral.save()
    user_profile.invites_used += 1
    user_profile.save(update_fields=['invites_used'])

    send_referral_event(user_profile)

def notify_realm_emoji(realm):
    notice = dict(event=dict(type="realm_emoji", op="update",
                             realm_emoji=realm.get_emoji()),
                  users=[userdict['id'] for userdict in get_active_user_dicts_in_realm(realm)])
    tornado_callbacks.send_notification(notice)

def do_add_realm_emoji(realm, name, img_url):
    RealmEmoji(realm=realm, name=name, img_url=img_url).save()
    notify_realm_emoji(realm)

def do_remove_realm_emoji(realm, name):
    RealmEmoji.objects.get(realm=realm, name=name).delete()
    notify_realm_emoji(realm)

def notify_alert_words(user_profile, words):
    notice = dict(event=dict(type="alert_words", alert_words=words),
                  users=[user_profile.id])
    tornado_callbacks.send_notification(notice)

def do_add_alert_words(user_profile, alert_words):
    words = add_user_alert_words(user_profile, alert_words)
    notify_alert_words(user_profile, words)

def do_remove_alert_words(user_profile, alert_words):
    words = remove_user_alert_words(user_profile, alert_words)
    notify_alert_words(user_profile, words)

def do_set_alert_words(user_profile, alert_words):
    set_user_alert_words(user_profile, alert_words)
    notify_alert_words(user_profile, alert_words)

def do_set_muted_topics(user_profile, muted_topics):
    user_profile.muted_topics = ujson.dumps(muted_topics)
    user_profile.save(update_fields=['muted_topics'])
    notice = dict(event=dict(type="muted_topics", muted_topics=muted_topics),
                  users=[user_profile.id])
    tornado_callbacks.send_notification(notice)

def notify_realm_filters(realm):
    realm_filters = realm_filters_for_domain(realm.domain)
    user_ids = [userdict['id'] for userdict in get_active_user_dicts_in_realm(realm)]

    notice = dict(event=dict(type="realm_filters", realm_filters=realm_filters), users=user_ids)
    tornado_callbacks.send_notification(notice)

def do_add_realm_filter(realm, pattern, url_format_string):
    RealmFilter(realm=realm, pattern=pattern,
                url_format_string=url_format_string).save()
    notify_realm_filters(realm)

def do_remove_realm_filter(realm, pattern):
    RealmFilter.objects.get(realm=realm, pattern=pattern).delete()
    notify_realm_filters(realm)

def get_emails_from_user_ids(user_ids):
    # We may eventually use memcached to speed this up, but the DB is fast.
    return UserProfile.emails_from_ids(user_ids)

@uses_mandrill
def clear_followup_emails_queue(email, mail_client=None):
    """
    Clear out queued emails (from Mandrill's queue) that would otherwise
    be sent to a specific email address. Optionally specify which sender
    to filter by (useful when there are more Zulip subsystems using our
    mandrill account).

    `email` is a string representing the recipient email
    `from_email` is a string representing the zulip email account used
    to send the email (for example `support@zulip.com` or `signups@zulip.com`)
    """
    # Zulip Enterprise implementation
    if not mail_client:
        items = ScheduledJob.objects.filter(type=ScheduledJob.EMAIL, filter_string__iexact = email)
        items.delete()
        return

    # Mandrill implementation
    for email in mail_client.messages.list_scheduled(to=email):
        result = mail_client.messages.cancel_scheduled(id=email["_id"])
        if result.get("status") == "error":
            print result.get("name"), result.get("error")
    return

@uses_mandrill
def send_future_email(recipients, email_html, email_text, subject,
                      delay=datetime.timedelta(0), sender=None,
                      tags=[], mail_client=None):
    """
    Sends email via Mandrill, with optional delay

    'mail_client' is filled in by the decorator
    """
    # When sending real emails while testing locally, don't accidentally send
    # emails to non-zulip.com users.
    if not settings.DEPLOYED and \
            settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
        for recipient in recipients:
            email = recipient.get("email")
            if get_user_profile_by_email(email).realm.domain != "zulip.com":
                raise ValueError("digest: refusing to send emails to non-zulip.com users.")

    # message = {"from_email": "othello@zulip.com",
    #            "from_name": "Othello",
    #            "html": "<p>hello</p> there",
    #            "tags": ["signup-reminders"],
    #            "to": [{'email':"acrefoot@zulip.com", 'name': "thingamajig"}]
    #            }

    # Zulip Enterprise implementation
    if not mail_client:
        if sender is None:
            # This may likely overridden by settings.DEFAULT_FROM_EMAIL
            sender = {'email': settings.NOREPLY_EMAIL_ADDRESS, 'name': 'Zulip'}
        for recipient in recipients:
            email_fields = {'email_html': email_html,
                            'email_subject': subject,
                            'email_text': email_text,
                            'recipient_email': recipient.get('email'),
                            'recipient_name': recipient.get('name'),
                            'sender_email': sender['email'],
                            'sender_name': sender['name']}
            ScheduledJob.objects.create(type=ScheduledJob.EMAIL, filter_string=recipient.get('email'),
                                        data=ujson.dumps(email_fields),
                                        scheduled_timestamp=datetime.datetime.utcnow() + delay)
        return

    # Mandrill implementation
    if sender is None:
        sender = {'email': settings.NOREPLY_EMAIL_ADDRESS, 'name': 'Zulip'}

    message = {'from_email': sender['email'],
               'from_name': sender['name'],
               'to': recipients,
               'subject': subject,
               'html': email_html,
               'text': email_text,
               'tags': tags,
               }
    # ignore any delays smaller than 1-minute because it's cheaper just to sent them immediately
    if type(delay) is not datetime.timedelta:
        raise TypeError("specified delay is of the wrong type: %s" % (type(delay),))
    if delay < datetime.timedelta(minutes=1):
        results = mail_client.messages.send(message=message, async=False, ip_pool="Main Pool")
    else:
        send_time = (datetime.datetime.utcnow() + delay).__format__("%Y-%m-%d %H:%M:%S")
        results = mail_client.messages.send(message=message, async=False, ip_pool="Main Pool", send_at=send_time)
    problems = [result for result in results if (result['status'] in ('rejected', 'invalid'))]
    if problems:
        raise Exception("While sending email (%s), encountered problems with these recipients: %r"
                        % (subject, problems))
    return

def send_local_email_template_with_delay(recipients, template_prefix,
                                         template_payload, delay,
                                         tags=[], sender={'email': settings.NOREPLY_EMAIL_ADDRESS, 'name': 'Zulip'}):
    html_content = loader.render_to_string(template_prefix + ".html", template_payload)
    text_content = loader.render_to_string(template_prefix + ".text", template_payload)
    subject = loader.render_to_string(template_prefix + ".subject", template_payload).strip()

    return send_future_email(recipients,
                             html_content,
                             text_content,
                             subject,
                             delay=delay,
                             sender=sender,
                             tags=tags)

def enqueue_welcome_emails(email, name):
    sender = {'email': 'wdaher@zulip.com', 'name': 'Waseem Daher'}
    if settings.ENTERPRISE:
        sender = {'email': settings.ZULIP_ADMINISTRATOR, 'name': 'Zulip'}

    user_profile = get_user_profile_by_email(email)
    unsubscribe_link = one_click_unsubscribe_link(user_profile, "welcome")

    template_payload = {'name': name,
                        'not_enterprise': not settings.ENTERPRISE,
                        'external_host': settings.EXTERNAL_HOST,
                        'unsubscribe_link': unsubscribe_link}

    #Send day 1 email
    send_local_email_template_with_delay([{'email': email, 'name': name}],
                                         "zerver/emails/followup/day1",
                                         template_payload,
                                         datetime.timedelta(hours=1),
                                         tags=["followup-emails"],
                                         sender=sender)
    #Send day 2 email
    tomorrow = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    # 11 AM EDT
    tomorrow_morning = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 15, 0)
    assert(datetime.datetime.utcnow() < tomorrow_morning)
    send_local_email_template_with_delay([{'email': email, 'name': name}],
                                         "zerver/emails/followup/day2",
                                         template_payload,
                                         tomorrow_morning - datetime.datetime.utcnow(),
                                         tags=["followup-emails"],
                                         sender=sender)

def realm_aliases(realm):
    return [alias.domain for alias in realm.realmalias_set.all()]

def convert_html_to_markdown(html):
    # On Linux, the tool installs as html2markdown, and there's a command called
    # html2text that does something totally different. On OSX, the tool installs
    # as html2text.
    commands = ["html2markdown", "html2text"]

    for command in commands:
        try:
            # A body width of 0 means do not try to wrap the text for us.
            p = subprocess.Popen(
                [command, "--body-width=0"], stdout=subprocess.PIPE,
                stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
            break
        except OSError:
            continue

    markdown = p.communicate(input=html.encode("utf-8"))[0].strip()
    # We want images to get linked and inline previewed, but html2text will turn
    # them into links of the form `![](http://foo.com/image.png)`, which is
    # ugly. Run a regex over the resulting description, turning links of the
    # form `![](http://foo.com/image.png?12345)` into
    # `[image.png](http://foo.com/image.png)`.
    return re.sub(r"!\[\]\((\S*)/(\S*)\?(\S*)\)",
                  r"[\2](\1/\2)", markdown).decode("utf-8")
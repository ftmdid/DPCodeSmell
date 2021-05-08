from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from zephyr.lib.cache import cache_with_key, update_user_profile_cache, \
    update_user_cache
from zephyr.lib.initial_password import initial_api_key
from zephyr.lib.utils import make_safe_digest
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
        return ("<Realm: %s %s>" % (self.domain, self.id)).encode("utf-8")
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
        return ("<UserProfile: %s %s>" % (self.user.email, self.realm)).encode("utf-8")
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
    MAX_NAME_LENGTH = 30
    name = models.CharField(max_length=MAX_NAME_LENGTH, db_index=True)
    realm = models.ForeignKey(Realm, db_index=True)
    invite_only = models.NullBooleanField(default=False)

    def __repr__(self):
        return ("<Stream: %s>" % (self.name,)).encode("utf-8")
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
        return ("<Recipient: %s (%d, %s)>" % (display_recipient, self.type_id, self.type)).encode("utf-8")

class Client(models.Model):
    name = models.CharField(max_length=30, db_index=True, unique=True)

def get_client_cache_key(name):
    return 'get_client:%s' % (make_safe_digest(name),)

@cache_with_key(get_client_cache_key)
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

def get_recipient_cache_key(type, type_id):
    return "get_recipient:%s:%s" % (type, type_id,)

@cache_with_key(get_recipient_cache_key)
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
        return ("<Message: %s / %s / %r>" % (display_recipient, self.subject, self.sender)).encode("utf-8")
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
        return ("<UserMessage: %s / %s (%s)>" % (display_recipient, self.user_profile.user.email, self.flags_dict())).encode("utf-8")

    def flags_dict(self):
        return dict(flags = [flag for flag in list(self.flags.keys()) if getattr(self.flags, flag).is_set])


class Subscription(models.Model):
    user_profile = models.ForeignKey(UserProfile)
    recipient = models.ForeignKey(Recipient)
    active = models.BooleanField(default=True)
    in_home_view = models.NullBooleanField(default=True)

    class Meta:
        unique_together = ("user_profile", "recipient")

    def __repr__(self):
        return ("<Subscription: %r -> %s>" % (self.user_profile, self.recipient)).encode("utf-8")
    def __str__(self):
        return self.__repr__()

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

@cache_with_key(lambda huddle_hash, id_list: huddle_hash_cache_key(huddle_hash))
def get_huddle_backend(huddle_hash, id_list):
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
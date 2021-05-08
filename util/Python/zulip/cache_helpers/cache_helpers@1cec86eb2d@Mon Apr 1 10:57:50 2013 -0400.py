# This file needs to be different from cache.py because cache.py
# cannot import anything from zephyr.models or we'd have an import
# loop
from zephyr.models import Message, UserProfile, Stream, get_stream_cache_key, \
    Recipient, get_recipient_cache_key, Client, get_client_cache_key, \
    Huddle, huddle_hash_cache_key
from zephyr.lib.cache import cache_with_key, djcache, message_cache_key, \
    user_profile_by_email_cache_key, user_profile_by_id_cache_key
import logging
from django.db import connection

MESSAGE_CACHE_SIZE = 25000

def cache_save_message(message):
    djcache.set(message_cache_key(message.id), (message,), timeout=3600*24)

@cache_with_key(message_cache_key, timeout=3600*24)
def cache_get_message(message_id):
    return Message.objects.select_related().get(id=message_id)

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
    'message': (lambda: Message.objects.select_related().all().order_by("-id")[0:MESSAGE_CACHE_SIZE],
                message_cache_items, 3600 * 24, 1000),
    'huddle': (lambda: Huddle.objects.select_related().all(), huddle_cache_items, 3600*24*7, 10000),
    }

def fill_memcached_cache(cache):
    items_for_memcached = {}
    (objects, items_filler, timeout, batch_size) = cache_fillers[cache]
    count = 0
    for obj in objects():
        items_filler(items_for_memcached, obj)
        count += 1
        if (count % batch_size == 0):
            djcache.set_many(items_for_memcached, timeout=3600*24)
            items_for_memcached = {}
    djcache.set_many(items_for_memcached, timeout=3600*24*7)
    logging.info("Succesfully populated %s cache!" % (cache,))
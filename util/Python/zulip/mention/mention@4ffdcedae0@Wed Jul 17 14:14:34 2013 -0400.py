import re

from django.db.models import F, Q
import zephyr.models

# Match multi-word string between @** ** or match any one-word
# sequences after @
find_mentions = r'(?<![^\s\'\"\(,:<])@(?:\*\*([^\*]+)\*\*|(\w+))'

wildcards = ['all', 'everyone']

def find_user_for_mention(mention, realm):
    if mention in wildcards:
        return (True, None)

    try:
        user = zephyr.models.UserProfile.objects.filter(
                Q(full_name__iexact=mention) | Q(short_name__iexact=mention),
                is_active=True,
                realm=realm).order_by("id")[0]
    except IndexError:
        user = None

    return (False, user)
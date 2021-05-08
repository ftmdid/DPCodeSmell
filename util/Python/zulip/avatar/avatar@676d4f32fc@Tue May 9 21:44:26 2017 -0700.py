
from django.conf import settings

if False:
    from zerver.models import UserProfile

from typing import Any, Dict, Optional, Text

from zerver.lib.avatar_hash import gravatar_hash, user_avatar_path, \
    user_avatar_path_from_ids
from zerver.lib.upload import upload_backend, MEDIUM_AVATAR_SIZE
from zerver.models import get_user_profile_by_email

def avatar_url(user_profile, medium=False):
    # type: (UserProfile, bool) -> Text
    url = _get_unversioned_avatar_url(
        user_profile.avatar_source,
        email=user_profile.email,
        realm_id=user_profile.realm_id,
        user_profile_id=user_profile.id,
        medium=medium)
    url += '&version=%d' % (user_profile.avatar_version,)
    return url

def get_avatar_url(avatar_source, email, avatar_version, medium=False):
    # type: (Text, Text, int, bool) -> Text
    url = _get_unversioned_avatar_url(
        avatar_source,
        email=email,
        medium=medium)
    url += '&version=%d' % (avatar_version,)
    return url

def _get_unversioned_avatar_url(avatar_source, email=None, realm_id=None,
                                user_profile_id=None, medium=False):
    # type: (Text, Text, Optional[int], Optional[int], bool) -> Text
    if avatar_source == 'U':
        if user_profile_id is not None and realm_id is not None:
            # If we can, avoid doing a database query to fetch user_profile
            hash_key = user_avatar_path_from_ids(user_profile_id, realm_id)
        else:
            user_profile = get_user_profile_by_email(email)
            hash_key = user_avatar_path(user_profile)
        return upload_backend.get_avatar_url(hash_key, medium=medium)
    elif settings.ENABLE_GRAVATAR:
        gravitar_query_suffix = "&s=%s" % (MEDIUM_AVATAR_SIZE,) if medium else ""
        hash_key = gravatar_hash(email)
        return "https://secure.gravatar.com/avatar/%s?d=identicon%s" % (hash_key, gravitar_query_suffix)
    else:
        return settings.DEFAULT_AVATAR_URI+'?x=x'
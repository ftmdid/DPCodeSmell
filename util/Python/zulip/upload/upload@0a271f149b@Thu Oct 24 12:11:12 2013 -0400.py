

from django.conf import settings
from django.template.defaultfilters import slugify

from zerver.lib.avatar import user_avatar_hash

from boto.s3.key import Key
from boto.s3.connection import S3Connection
from mimetypes import guess_type, guess_extension

import base64
import os

# Performance Note:
#
# For writing files to S3, the file could either be stored in RAM
# (if it is less than 2.5MiB or so) or an actual temporary file on disk.
#
# Because we set FILE_UPLOAD_MAX_MEMORY_SIZE to 0, only the latter case
# should occur in practice.
#
# This is great, because passing the pseudofile object that Django gives
# you to boto would be a pain.

# To come up with a s3 key we randomly generate a "directory". The "file
# name" is the original filename provided by the user run through Django's
# slugify.

def sanitize_name(name):
    split_name = name.split('.')
    base = ".".join(split_name[:-1])
    extension = split_name[-1]
    return slugify(base) + "." + slugify(extension)

def random_name(bytes=60):
    return base64.urlsafe_b64encode(os.urandom(bytes))

def upload_image_to_s3(
        bucket_name,
        file_name,
        content_type,
        user_profile,
        contents,
    ):

    conn = S3Connection(settings.S3_KEY, settings.S3_SECRET_KEY)
    key = Key(conn.get_bucket(bucket_name))
    key.key = file_name
    key.set_metadata("user_profile_id", str(user_profile.id))
    key.set_metadata("realm_id", str(user_profile.realm.id))

    if content_type:
        headers = {'Content-Type': content_type}
    else:
        headers = None

    key.set_contents_from_string(contents, headers=headers)

def get_file_info(request, user_file):
    uploaded_file_name = user_file.name
    content_type = request.GET.get('mimetype')
    if content_type is None:
        content_type = guess_type(uploaded_file_name)[0]
    else:
        uploaded_file_name = uploaded_file_name + guess_extension(content_type)
    return uploaded_file_name, content_type

def authed_upload_enabled(user_profile):
    return user_profile.realm.domain in ('zulip.com', 'squarespace.com')

def upload_message_image(uploaded_file_name, content_type, file_data, user_profile, private=None):
    if private is None:
        private = authed_upload_enabled(user_profile)
    if private:
        bucket_name = settings.S3_AUTH_UPLOADS_BUCKET
        s3_file_name = "/".join([
            str(user_profile.realm.id),
            random_name(18),
            sanitize_name(uploaded_file_name)
        ])
        url = "/user_uploads/%s" % (s3_file_name)
    else:
        bucket_name = settings.S3_BUCKET
        s3_file_name = "/".join([random_name(60), sanitize_name(uploaded_file_name)])
        url = "https://%s.s3.amazonaws.com/%s" % (bucket_name, s3_file_name)

    upload_image_to_s3(
            bucket_name,
            s3_file_name,
            content_type,
            user_profile,
            file_data
    )
    return url

def upload_message_image_through_web_client(request, user_file, user_profile, private=None):
    uploaded_file_name, content_type = get_file_info(request, user_file)
    return upload_message_image(uploaded_file_name, content_type, user_file.read(), user_profile, private)

def get_signed_upload_url(path):
    conn = S3Connection(settings.S3_KEY, settings.S3_SECRET_KEY)
    return conn.generate_url(15, 'GET', bucket=settings.S3_AUTH_UPLOADS_BUCKET, key=path)

def upload_avatar_image(user_file, user_profile, email):
    content_type = guess_type(user_file.name)[0]
    bucket_name = settings.S3_AVATAR_BUCKET
    s3_file_name = user_avatar_hash(email)
    upload_image_to_s3(
        bucket_name,
        s3_file_name,
        content_type,
        user_profile,
        user_file.read(),
    )
    # See avatar_url in avatar.py for URL.  (That code also handles the case
    # that users use gravatar.)
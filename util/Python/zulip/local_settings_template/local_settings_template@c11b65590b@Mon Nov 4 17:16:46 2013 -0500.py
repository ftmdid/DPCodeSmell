# Template for Django settings for the Zulip local servers

# This is the user-accessible Zulip hostname for this installation
EXTERNAL_HOST = ''

# This is the Zulip Administrator email address
ZULIP_ADMINISTRATOR = ''

# These credentials are for communication with the central Zulip deployment manager
DEPLOYMENT_ROLE_NAME = ''
DEPLOYMENT_ROLE_KEY = ''

# Configure the outgoing SMTP server below. For outgoing email
# via a GMail SMTP server, EMAIL_USE_TLS must be True and the
# outgoing port must be 587. The EMAIL_HOST is prepopulated
# for GMail servers, change it for other hosts
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587

# By default uploaded files and avatars are stored directly on the Zulip server
# If file storage to Amazon S3 is desired, please contact Zulip Support
# (support@zulip.com) for further instructions on setting up S3 integration
LOCAL_UPLOADS_DIR = "/home/zulip/uploads"

# In order to show Tweet previews inline in messages, Zulip must have access
# to the Twitter API via OAuth. To fetch the various access tokens needed below,
# you must register a new application under your Twitter account by doing the following:
#
# 1. Log in to http://dev.twitter.com.
# 2. In the menu under your username, click My Applications. From this page, create a new application.
# 3. Click on the application you created and click "create my access token". Fill in the requested values.
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
TWITTER_ACCESS_TOKEN_KEY = ''
TWITTER_ACCESS_TOKEN_SECRET = ''

# When using SSO: If REMOTE_USER only provides a username, append this domain
# to the returned value.
SSO_APPEND_DOMAIN = None

# Enable at least one of the following authentication backends.
AUTHENTICATION_BACKENDS = (
#                           'zproject.backends.EmailAuthBackend', # Email and password
#                           'zerver.views.remote_user_sso', # Local SSO
#                           'zproject.backends.GoogleBackend', # Google Apps
    )

# The following keys are automatically generated during the install process
# PLEASE DO NOT EDIT THEM
CAMO_KEY = ''
SECRET_KEY = ''
HASH_SALT = ''
RABBITMQ_PASSWORD = ''
AVATAR_SALT = ''
SHARED_SECRET = ''
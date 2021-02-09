# Settings for Zulip Enterprise

### MANDATORY SETTINGS

# The user-accessible Zulip hostname for this installation, e.g.
# zulip.example.com
EXTERNAL_HOST = ''

# The email address for the person or team who maintain the Zulip
# Enterprise installation. Will also get support emails. (e.g. zulip-admin@example.com)
ZULIP_ADMINISTRATOR = ''

# The domain for your organization, e.g. example.com
ADMIN_DOMAIN = ''

# The deployment key is used by your server to authenticate any
# communication with Zulip.  You can obtain your key from
# https://zulip.com/enterprise/download/deployment-key
DEPLOYMENT_ROLE_KEY = ''

# Enable at least one of the following authentication backends.
AUTHENTICATION_BACKENDS = (
#                           'zproject.backends.EmailAuthBackend', # Email and password
#                           'zproject.backends.ZulipRemoteUserBackend', # Local SSO
#                           'zproject.backends.GoogleBackend', # Google Apps
    )

# If you are using the ZulipRemoteUserBackend authentication backend,
# set this to your domain (e.g. if REMOTE_USER is "username" and the
# corresponding email address is "username@example.com", set
# SSO_APPEND_DOMAIN = "example.com")
SSO_APPEND_DOMAIN = None

# Configure the outgoing SMTP server below. For outgoing email
# via a GMail SMTP server, EMAIL_USE_TLS must be True and the
# outgoing port must be 587. The EMAIL_HOST is prepopulated
# for GMail servers, change it for other hosts, or leave it unset
# or empty to skip sending email.
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# The email From address to be used for automatically generated emails
DEFAULT_FROM_EMAIL = "Zulip <zulip@example.com>"
# The noreply address to be used as Reply-To for certain generated emails.
# Messages sent to this address should not be delivered anywhere.
NOREPLY_EMAIL_ADDRESS = "noreply@example.com"

### OPTIONAL SETTINGS

# Controls whether session cookies expire when the browser closes
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Session cookie expiry in seconds after the last page load
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7 * 2 # 2 weeks

# Controls whether or not there is a feedback button in the UI, which
# can be used to send feedback directly to the Zulip developers.
ENABLE_FEEDBACK = True

# Controls whether or not error reports are sent to Zulip.  Error
# reports are used to improve the quality of the product and do not
# include message contents; please contact Zulip support with any
# questions.
ERROR_REPORTING = True

# Controls whether or not Zulip will provide inline image preview when
# a link to an image is referenced in a message.
INLINE_IMAGE_PREVIEW = True

# By default, files uploaded by users and user avatars are stored
# directly on the Zulip server.  If file storage in Amazon S3 (or
# elsewhere, e.g. your corporate fileshare) is desired, please contact
# Zulip Support (support@zulip.com) for further instructions on
# setting up the appropriate integration.
LOCAL_UPLOADS_DIR = "/home/zulip/uploads"

# Controls whether name changes are completely disabled for this installation
# This is useful in settings where you're syncing names from an integrated LDAP/Active Directory
NAME_CHANGES_DISABLED = False

# Controls whether users who have not uploaded an avatar will receive an avatar
# from gravatar.com.
ENABLE_GRAVATAR = True

### TWITTER INTEGRATION

# Zulip supports showing inline Tweet previews when a tweet is linked
# to in a message.  To support this, Zulip must have access to the
# Twitter API via OAuth.  To obtain the various access tokens needed
# below, you must register a new application under your Twitter
# account by doing the following:
#
# 1. Log in to http://dev.twitter.com.
# 2. In the menu under your username, click My Applications. From this page, create a new application.
# 3. Click on the application you created and click "create my access token". Fill in the requested values.
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
TWITTER_ACCESS_TOKEN_KEY = ''
TWITTER_ACCESS_TOKEN_SECRET = ''

### EMAIL GATEWAY INTEGRATION

# The email gateway provides, for each stream, an email address that
# you can send email to in order to have the email's content be posted
# to that stream.  Emails received at the per-stream email address
# will be converted into a Zulip message

# The email address pattern to use for auto-generated stream emails
# The %s will be replaced with a unique token, and the resulting email
# must be delivered to the EMAIL_GATEWAY_IMAP_FOLDER of the
# EMAIL_GATEWAY_LOGIN account below.
#
# Example: zulip+%s@example.com
EMAIL_GATEWAY_PATTERN = ""

# The Zulip username of the bot that the email pattern should post as.
# Example: emailgateway@example.com
EMAIL_GATEWAY_BOT = ""

# Configuration of the email mirror mailbox
# The IMAP login and password
EMAIL_GATEWAY_LOGIN = ""
EMAIL_GATEWAY_PASSWORD = ""
# The IMAP server & port to connect to
EMAIL_GATEWAY_IMAP_SERVER = ""
EMAIL_GATEWAY_IMAP_PORT = 993
# The IMAP folder name to check for emails. All emails sent to EMAIL_GATEWAY_PATTERN above
# must be delivered to this folder
EMAIL_GATEWAY_IMAP_FOLDER = "INBOX"

# The following secrets are randomly generated during the install
# process, are used for security purposes, and should not be shared
# with anyone.
#
# PLEASE DO NOT CHANGE THEM WITHOUT INSTRUCTIONS FROM ZULIP SUPPORT
CAMO_KEY = ''
SECRET_KEY = ''
HASH_SALT = ''
RABBITMQ_PASSWORD = ''
AVATAR_SALT = ''
SHARED_SECRET = ''
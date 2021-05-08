# Non-secret secret Django settings for the Zulip project
import platform
import configparser
from base64 import b64decode

config_file = configparser.RawConfigParser()
config_file.read("/etc/zulip/zulip.conf")

# Whether we're running in a production environment. Note that DEPLOYED does
# **not** mean hosted by us; customer sites are DEPLOYED and ENTERPRISE
# and as such should not for example assume they are the main Zulip site.
DEPLOYED = config_file.has_option('machine', 'deploy_type')

# The following flags are leftover from the various configurations of
# Zulip run by Zulip, Inc.  We will eventually be able to get rid of
# them and just have the DEPLOYED flag, but we need them for now.
ZULIP_COM_STAGING = DEPLOYED and config_file.get('machine', 'deploy_type') == 'staging'

ENTERPRISE = DEPLOYED and config_file.get('machine', 'deploy_type') == 'enterprise'

ZULIP_FRIENDS_LIST_ID = '84b2f3da6b'

# This can be filled in automatically from the database, maybe
DEPLOYMENT_ROLE_NAME = 'zulip.com'

# XXX: replace me
CAMO_URI = 'https://external-content.zulipcdn.net/'

# Leave EMAIL_HOST unset or empty if you do not wish for emails to be sent
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'zulip@zulip.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# We use mandrill, so this doesn't actually get used on our hosted deployment
DEFAULT_FROM_EMAIL = "Zulip <zulip@zulip.com>"
# The noreply address to be used as Reply-To for certain generated emails.
NOREPLY_EMAIL_ADDRESS = "noreply@zulip.com"

SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

if ZULIP_COM_STAGING:
    EXTERNAL_HOST = 'staging.zulip.com'
elif DEPLOYED:
    EXTERNAL_HOST = 'zulip.com'
    EXTERNAL_API_PATH = 'api.zulip.com'


# For now, ENTERPRISE is only testing, so write to our test buckets
if DEPLOYED and not ENTERPRISE:
    S3_BUCKET="humbug-user-uploads"
    S3_AUTH_UPLOADS_BUCKET = "zulip-user-uploads"
    S3_AVATAR_BUCKET="humbug-user-avatars"
else:
    S3_BUCKET="humbug-user-uploads-test"
    S3_AUTH_UPLOADS_BUCKET = "zulip-user-uploads-test"
    S3_AVATAR_BUCKET="humbug-user-avatars-test"

if DEPLOYED or ZULIP_COM_STAGING:
    APNS_SANDBOX = "push_production"
    APNS_FEEDBACK = "feedback_production"
    APNS_CERT_FILE = "/etc/ssl/django-private/apns-dist.pem"
    DBX_APNS_CERT_FILE = "/etc/ssl/django-private/dbx-apns-dist.pem"
else:
    APNS_SANDBOX = "push_sandbox"
    APNS_FEEDBACK = "feedback_sandbox"
    APNS_CERT_FILE = "/etc/ssl/django-private/apns-dev.pem"
    DBX_APNS_CERT_FILE = "/etc/ssl/django-private/dbx-apns-dev.pem"

GOOGLE_CLIENT_ID = "835904834568-77mtr5mtmpgspj9b051del9i9r5t4g4n.apps.googleusercontent.com"

if DEPLOYED:
    GOOGLE_OAUTH2_CLIENT_ID = '835904834568-ag4p18v0sd9a0tero14r3gekn6shoen3.apps.googleusercontent.com'
else:
    # Google OAUTH2 for dev with the redirect uri set to http://localhost:9991/accounts/login/google/done/
    GOOGLE_OAUTH2_CLIENT_ID = '607830223128-4qgthc7ofdqce232dk690t5jgkm1ce33.apps.googleusercontent.com'

# Administrator domain for this install
ADMIN_DOMAIN = "zulip.com"

# The email address pattern to use for auto-generated stream emails
# The %s will be replaced with a unique token.
if ZULIP_COM_STAGING:
    EMAIL_GATEWAY_PATTERN = "%s@streams.staging.zulip.com"
elif DEPLOYED:
    EMAIL_GATEWAY_PATTERN = "%s@streams.zulip.com"

# Email mirror configuration
# The email of the Zulip bot that the email gateway should post as.
EMAIL_GATEWAY_BOT = "emailgateway@zulip.com"


SSO_APPEND_DOMAIN = None

AUTHENTICATION_BACKENDS = ('zproject.backends.EmailAuthBackend',
                           'zproject.backends.GoogleMobileOauth2Backend')

# ALLOWED_HOSTS is used by django to determine which addresses
# Zulip can serve. This is a security measure.
# The following are the zulip.com hosts
ALLOWED_HOSTS = ['localhost', '.humbughq.com', '54.214.48.144', '54.213.44.54',
                 '54.213.41.54', '54.213.44.58', '54.213.44.73',
                 '54.200.19.65', '54.201.95.104', '54.201.95.206',
                 '54.201.186.29', '54.200.111.22',
                 '54.245.120.64', '54.213.44.83', '.zulip.com', '.zulip.net',
                 'chat.dropboxer.net']


JWT_AUTH_KEYS = {}

NOTIFICATION_BOT = "notification-bot@zulip.com"
ERROR_BOT = "error-bot@zulip.com"
NEW_USER_BOT = "new-user-bot@zulip.com"

NAGIOS_SEND_BOT = 'iago@zulip.com'
NAGIOS_RECEIVE_BOT = 'othello@zulip.com'

# Our internal deployment has nagios checks for both staging and prod
NAGIOS_STAGING_SEND_BOT = 'iago@zulip.com'
NAGIOS_STAGING_RECEIVE_BOT = 'cordelia@zulip.com'

# Also used for support email in emails templates
ZULIP_ADMINISTRATOR = 'support@zulip.com'

# TODO: Store this info in the database
# Also note -- the email gateway bot is automatically added.
API_SUPER_USERS = set(["tabbott/extra@mit.edu",
                       "irc-bot@zulip.com",
                       "bot1@customer35.invalid",
                       "bot1@customer36.invalid",
                       "hipchat-bot@zulip.com",])

ADMINS = (
    ('Zulip Error Reports', 'errors@zulip.com'),
)
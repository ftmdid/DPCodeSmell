

from django.conf import settings
import ujson
from zproject.backends import password_auth_enabled

def add_settings(request):
    return {
        'full_navbar':   settings.FULL_NAVBAR,
        'enterprise':    settings.ENTERPRISE,
        'zulip_admin':   settings.ZULIP_ADMINISTRATOR,
        'password_auth_enabled': password_auth_enabled(),
    }

def add_metrics(request):
    return {
        'mixpanel_token': settings.MIXPANEL_TOKEN,
        'enable_metrics': ujson.dumps(settings.DEPLOYED),
        'dropboxAppKey': settings.DROPBOX_APP_KEY
    }
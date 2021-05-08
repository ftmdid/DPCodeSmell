

from django.conf import settings
import ujson

def add_settings(request):
    return {
        'full_navbar':   settings.FULL_NAVBAR,
        'local_server':  settings.LOCAL_SERVER,
    }

def add_metrics(request):
    return {
        'mixpanel_token': settings.MIXPANEL_TOKEN,
        'enable_metrics': ujson.dumps(settings.DEPLOYED),
        'dropboxAppKey': settings.DROPBOX_APP_KEY
    }
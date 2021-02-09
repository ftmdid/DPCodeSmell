from __future__ import absolute_import

from postmonkey import PostMonkey
from django.core.management.base import BaseCommand
from django.conf import settings

from zerver.lib.queue import SimpleQueueClient

class Command(BaseCommand):
    pm = PostMonkey(settings.MAILCHIMP_API_KEY, timeout=10)

    def subscribe(self, ch, method, properties, data):
        self.pm.listSubscribe(
                id=settings.ZULIP_FRIENDS_LIST_ID,
                email_address=data['EMAIL'],
                merge_vars=data['merge_vars'],
                double_optin=False,
                send_welcome=False)

    def handle(self, *args, **options):
        q = SimpleQueueClient()
        q.register_json_consumer("signups", self.subscribe)
        q.start_consuming()
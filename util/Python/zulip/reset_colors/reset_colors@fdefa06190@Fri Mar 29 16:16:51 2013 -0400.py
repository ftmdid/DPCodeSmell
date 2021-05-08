from django.core.management.base import BaseCommand
from zephyr.models import Subscription, Recipient, get_user_profile_by_email

class Command(BaseCommand):
    help = """Reset all colors for a person to the default grey"""

    def handle(self, *args, **options):
        if not args:
            self.print_help("python manage.py", "reset_colors")
            exit(1)

        for email in args:
            user_profile = get_user_profile_by_email(email)
            subs = Subscription.objects.filter(user_profile=user_profile,
                                               active=True,
                                               recipient__type=Recipient.STREAM)

            for sub in subs:
                sub.color = Subscription.DEFAULT_STREAM_COLOR
                sub.save(update_fields=["color"])
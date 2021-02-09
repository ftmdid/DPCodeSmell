from __future__ import absolute_import

from django.core.management.base import BaseCommand
from confirmation.models import Confirmation
from zephyr.models import UserProfile, PreregistrationUser, \
    get_user_profile_by_email

class Command(BaseCommand):
    help = "Generate activation links for users and print them to stdout."

    def handle(self, *args, **options):
        duplicates = False
        for email in args:
            try:
                get_user_profile_by_email(email)
                print email + ": There is already a user registered with that address."
                duplicates = True
                continue
            except UserProfile.DoesNotExist:
                pass

        if duplicates:
            return

        for email in args:
            prereg_user = PreregistrationUser(email=email)
            prereg_user.save()
            print email + ": " + Confirmation.objects.get_link_for_object(prereg_user)

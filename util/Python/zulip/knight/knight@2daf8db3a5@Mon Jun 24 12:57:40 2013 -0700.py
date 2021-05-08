

import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.core import validators

from guardian.shortcuts import assign_perm, remove_perm

from zephyr.models import Realm, UserProfile

class Command(BaseCommand):
    help = """Give an existing user administrative permissions over their (own) Realm.

ONLY perform this on customer request from an authorized person.
"""

    option_list = BaseCommand.option_list + (
        make_option('--revoke',
                    dest='grant',
                    action="store_false",
                    default=True,
                    help='Remove an administrator\'s rights.'),
        )

    def handle(self, *args, **options):
        try:
            email = args[0]
        except ValueError:
            raise CommandError("""Please specify a user.""")
        try:
            profile = UserProfile.objects.get(email=email)
        except ValidationError:
            raise CommandError("No such user.")

        if options['grant']:
            if profile.has_perm('administer', profile.realm):
                raise CommandError("User already has permission for this realm.")
            else:
                assign_perm('administer', profile, profile.realm)
                print("Done!")
        else:
            if profile.has_perm('administer', profile.realm):
                remove_perm('administer', profile, profile.realm)
                print("Done!")
            else:
                raise CommandError("User did not have permission for this realm!")

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from zerver.lib.actions import do_create_realm
from zilencer.models import Deployment

import re
import sys

class Command(BaseCommand):
    help = """Create a realm for the specified domain.

Usage: python manage.py create_realm --domain=foo.com --name='Foo, Inc.'"""

    option_list = BaseCommand.option_list + (
        make_option('-o', '--open-realm',
                    dest='open_realm',
                    action="store_true",
                    default=False,
                    help='Make this an open realm.'),
        make_option('-d', '--domain',
                    dest='domain',
                    type='str',
                    help='The domain for the realm.'),
        make_option('-n', '--name',
                    dest='name',
                    type='str',
                    help='The user-visible name for the realm.'),
        make_option('--deployment',
                    dest='deployment_id',
                    type='int',
                    default=None,
                    help='Optionally, the ID of the deployment you want to associate the realm with.'),
        )

    def validate_domain(self, domain):
        # Domains can't contain whitespace if they are to be used in memcached
        # keys.
        if re.search("\s", domain):
            raise ValueError("Domains can't contain whitespace")

        # Domains must look like domains, ie have the structure of
        # <subdomain(s)>.<tld>. One reason for this is that bots need
        # to have valid looking emails.
        if len(domain.split(".")) < 2:
            raise ValueError("Domains must contain a '.'")

    def handle(self, *args, **options):
        if options["domain"] is None or options["name"] is None:
            print("\033[1;31mPlease provide both a domain and name.\033[0m\n", file=sys.stderr)
            self.print_help("python manage.py", "create_realm")
            exit(1)

        if options["open_realm"] and options["deployment_id"] is not None:
            print("\033[1;31mExternal deployments cannot be open realms.\033[0m\n", file=sys.stderr)
            self.print_help("python manage.py", "create_realm")
            exit(1)
        if options["deployment_id"] is not None and settings.LOCALSERVER:
            print("\033[1;31mExternal deployments are not supported on local server deployments.\033[0m\n", file=sys.stderr)
            exit(1)

        domain = options["domain"]
        name = options["name"]

        self.validate_domain(domain)

        realm, created = do_create_realm(
            domain, name, restricted_to_domain=not options["open_realm"])
        if created:
            print(domain, "created.")
            if options["deployment_id"] is not None:
                deployment = Deployment.objects.get(id=options["deployment_id"])
                deployment.realms.add(realm)
                deployment.save()
                print("Added to deployment", str(deployment.id))
            elif not settings.LOCALSERVER:
                deployment = Deployment.objects.get(base_site_url="https://zulip.com/")
                deployment.realms.add(realm)
                deployment.save()
            print("\033[1;36mDon't forget to run set_default_streams!\033[0m")
        else:
            print(domain, "already exists.")
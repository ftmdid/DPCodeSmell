from __future__ import absolute_import
from optparse import make_option

from django.core.management.base import BaseCommand
from zerver.lib.actions import do_create_realm

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
            print >>sys.stderr, "\033[1;31mPlease provide both a domain and name.\033[0m\n"
            self.print_help("python manage.py", "create_realm")
            exit(1)

        domain = options["domain"]
        name = options["name"]

        self.validate_domain(domain)

        realm, created = do_create_realm(
            domain, name, restricted_to_domain=not options["open_realm"])
        if created:
            print domain, "created."
        else:
            print domain, "already exists."
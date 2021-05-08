from django.core.management.base import BaseCommand
from django.utils.timezone import utc

from django.contrib.auth.models import User
from zephyr.models import Zephyr, UserProfile, ZephyrClass, Recipient, \
    Subscription, Huddle, get_huddle, Realm, create_user_profile, UserMessage
from zephyr.zephyr_mirror import subs_list

import datetime
import random
from optparse import make_option

def create_users(username_list, realm):
    for username in username_list:
        if User.objects.filter(username=username):
            # We're trying to create the same user twice!
            raise
        user = User.objects.create_user(username=username, password=username)
        user.save()
        create_user_profile(user, realm)

def create_classes(class_list, realm):
    for name in class_list:
        if ZephyrClass.objects.filter(name=name, realm=realm):
            # We're trying to create the same zephyr class twice!
            raise
        new_class = ZephyrClass(name=name, realm=realm)
        new_class.save()

        recipient = Recipient(type_id=new_class.pk, type="class")
        recipient.save()

class Command(BaseCommand):
    help = "Populate a test database"

    option_list = BaseCommand.option_list + (
        make_option('-n', '--num-zephyrs',
                    dest='num_zephyrs',
                    type='int',
                    default=120,
                    help='The number of zephyrs to create.'),
        make_option('--huddles',
                    dest='num_huddles',
                    type='int',
                    default=3,
                    help='The number of huddles to create.'),
        make_option('--personals',
                    dest='num_personals',
                    type='int',
                    default=6,
                    help='The number of personal pairs to create.'),
        make_option('--percent-huddles',
                    dest='percent_huddles',
                    type='float',
                    default=15,
                    help='The percent of messages to be huddles.'),
        make_option('--percent-personals',
                    dest='percent_personals',
                    type='float',
                    default=15,
                    help='The percent of messages to be personals.'),
        make_option('--stickyness',
                    dest='stickyness',
                    type='float',
                    default=20,
                    help='The percent of messages to repeat recent folks.'),
        )

    def handle(self, **options):
        if options["percent_huddles"] + options["percent_personals"] > 100:
            self.stderr.write("Error!  More than 100% of messages allocated.\n")
            return

        for klass in [Zephyr, ZephyrClass, UserProfile, User, Recipient,
                      Realm, Subscription, Huddle, UserMessage]:
            klass.objects.all().delete()

        # Create a test realm
        realm = Realm(domain="humbughq.com")
        realm.save()

        # Create test Users (UserProfiles are automatically created,
        # as are subscriptions to the ability to receive personals).
        usernames = ["othello", "iago", "prospero", "cordelia", "hamlet"]
        create_users(usernames, realm)
        users = [user.id for user in User.objects.all()]

        # Create public classes.
        class_list = ["Verona", "Denmark", "Scotland", "Venice", "Rome"]
        create_classes(class_list, realm)

        # Create several initial huddles
        huddle_members = {}
        for i in range(0, options["num_huddles"]):
            user_ids = random.sample(users, random.randint(3, 4))
            huddle_members[get_huddle(user_ids).id] = user_ids

        # Create several initial pairs for personals
        personals_pairs = []
        for i in range(0, options["num_personals"]):
            personals_pairs.append(random.sample(users, 2))

        recipient_classes = [klass.type_id for klass in Recipient.objects.filter(type="class")]
        recipient_huddles = [h.type_id for h in Recipient.objects.filter(type="huddle")]

        # Create subscriptions to classes
        profiles = UserProfile.objects.all()
        for i, profile in enumerate(profiles):
            # Subscribe to some classes.
            for recipient in recipient_classes[:int(len(recipient_classes) * float(i)/len(profiles)) + 1]:
                new_subscription = Subscription(userprofile=profile,
                                                recipient=Recipient.objects.get(type="class",
                                                                                type_id=recipient))
                new_subscription.save()

        # Create some test zephyrs, including:
        # - multiple classes
        # - multiple instances per class
        # - multiple zephyrs per instance
        # - both single and multi-line content

        texts = file("zephyr/management/commands/test_zephyrs.txt", "r").readlines()
        offset = 0
        num_zephyrs = 0
        random_max = 1000000
        recipients = {}
        while num_zephyrs < options["num_zephyrs"]:
            saved_data = ''
            new_zephyr = Zephyr()
            length = random.randint(1, 5)
            new_zephyr.content = "".join(texts[offset: offset + length])
            offset += length
            offset = offset % len(texts)

            randkey = random.randint(1, random_max)
            if (num_zephyrs > 0 and
                random.randint(1, random_max) * 100. / random_max < options["stickyness"]):
                # Use an old recipient
                zephyr_type, recipient, saved_data = recipients[num_zephyrs - 1]
                if zephyr_type == "personal":
                    personals_pair = saved_data
                    random.shuffle(personals_pair)
                elif zephyr_type == "class":
                    new_zephyr.instance = saved_data
                    new_zephyr.recipient = recipient
                elif zephyr_type == "huddle":
                    new_zephyr.recipient = recipient
            elif (randkey <= random_max * options["percent_huddles"] / 100.):
                zephyr_type = "huddle"
                new_zephyr.recipient = Recipient.objects.get(type="huddle", type_id=random.choice(recipient_huddles))
            elif (randkey <= random_max * (options["percent_huddles"] + options["percent_personals"]) / 100.):
                zephyr_type = "personal"
                personals_pair = random.choice(personals_pairs)
                random.shuffle(personals_pair)
            elif (randkey <= random_max * 1.0):
                zephyr_type = "class"
                new_zephyr.recipient = Recipient.objects.get(type="class", type_id=random.choice(recipient_classes))

            if zephyr_type == "huddle":
                new_zephyr.sender = UserProfile.objects.get(id=random.choice(huddle_members[new_zephyr.recipient.type_id]))
            elif zephyr_type == "personal":
                new_zephyr.recipient = Recipient.objects.get(type="personal", type_id=personals_pair[0])
                new_zephyr.sender = UserProfile.objects.get(id=personals_pair[1])
                saved_data = personals_pair
            elif zephyr_type == "class":
                zephyr_class = ZephyrClass.objects.get(pk=new_zephyr.recipient.type_id)
                # Pick a random subscriber to the class
                new_zephyr.sender = random.choice(Subscription.objects.filter(recipient=new_zephyr.recipient)).userprofile
                new_zephyr.instance = zephyr_class.name + str(random.randint(1, 3))
                saved_data = new_zephyr.instance

            new_zephyr.pub_date = datetime.datetime.utcnow().replace(tzinfo=utc)
            new_zephyr.save()

            recipients[num_zephyrs] = [zephyr_type, new_zephyr.recipient, saved_data]
            num_zephyrs += 1

        # Create internal users
        internal_usernames = []
        create_users(internal_usernames, realm)

        create_classes(subs_list, realm)

        # Now subscribe everyone to these classes
        profiles = UserProfile.objects.all()
        for cls in subs_list:
            zephyr_class = ZephyrClass.objects.get(name=cls, realm=realm)
            recipient = Recipient.objects.get(type="class", type_id=zephyr_class.id)
            for i, profile in enumerate(profiles):
            # Subscribe to some classes.
                new_subscription = Subscription(userprofile=profile, recipient=recipient)
                new_subscription.save()

        self.stdout.write("Successfully populated test database.\n")
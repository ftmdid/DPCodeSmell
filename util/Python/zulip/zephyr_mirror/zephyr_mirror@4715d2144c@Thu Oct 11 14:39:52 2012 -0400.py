#!/usr/bin/python
import urllib
import sys
import logging
import traceback
import simplejson
import re
import time
import subprocess
import optparse
import os
import datetime
import textwrap
from urllib2 import HTTPError

sys.path.append("/mit/tabbott/Public/python-zephyr/")
sys.path.append("/mit/tabbott/Public/python-zephyr/build/lib.linux-x86_64-2.6/")

parser = optparse.OptionParser()
parser.add_option('--forward-class-messages',
                  dest='forward_class_messages',
                  default=False,
                  action='store_true')
parser.add_option('--resend-log',
                  dest='resend_log',
                  default=False,
                  action='store_true')
parser.add_option('--enable-log',
                  dest='enable_log',
                  default=False,
                  action='store_true')
parser.add_option('--no-forward-personals',
                  dest='forward_personals',
                  default=True,
                  action='store_false')
parser.add_option('--forward-from-humbug',
                  dest='forward_to_humbug',
                  default=True,
                  action='store_false')
parser.add_option('--site',
                  dest='site',
                  default="https://app.humbughq.com",
                  action='store')
parser.add_option('--api-key',
                  dest='api_key',
                  default="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                  action='store')
(options, args) = parser.parse_args()

sys.path.append(".")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import api.common
humbug_client = api.common.HumbugAPI(email=os.environ["USER"] + "@mit.edu",
                                     api_key=options.api_key,
                                     verbose=True,
                                     site=options.site)

import zephyr
zephyr.init()
subs = zephyr.Subscriptions()

def compute_humbug_username(zephyr_username):
    return zephyr_username.lower().split("@")[0] + "@mit.edu"

def send_humbug(zeph):
    zeph["forged"] = "yes"
    zeph["sender"] = compute_humbug_username(zeph["sender"])
    zeph['fullname']  = username_to_fullname(zeph['sender'])
    zeph['shortname'] = zeph['sender'].split('@')[0]
    if "subject" in zeph:
        zeph["subject"] = zeph["subject"][:60]

    for key in zeph.keys():
        if isinstance(zeph[key], unicode):
            zeph[key] = zeph[key].encode("utf-8")
        elif isinstance(zeph[key], str):
            zeph[key] = zeph[key].decode("utf-8")

    return humbug_client.send_message(zeph)

def fetch_fullname(username):
    try:
        match_user = re.match(r'([a-zA-Z0-9_]+)@mit\.edu', username)
        if match_user:
            proc = subprocess.Popen(['hesinfo', match_user.group(1), 'passwd'], stdout=subprocess.PIPE)
            out, _err_unused = proc.communicate()
            if proc.returncode == 0:
                return out.split(':')[4].split(',')[0]
    except:
        print >>sys.stderr, 'Error getting fullname for', username
        traceback.print_exc()

    return username.title().replace('@', ' at ').replace('.', ' dot ')

fullnames = {}
def username_to_fullname(username):
    if username not in fullnames:
        fullnames[username] = fetch_fullname(username)
    return fullnames[username]

current_zephyr_subs = {}
def ensure_subscribed(sub):
    if sub in current_zephyr_subs:
        return
    subs.add((sub, '*', '*'))
    current_zephyr_subs[sub] = True

def update_subscriptions_from_humbug():
    try:
        res = humbug_client.get_public_streams()
        streams = res["streams"]
    except:
        print "Error getting public streams:"
        traceback.print_exc()
        return
    for stream in streams:
        ensure_subscribed(stream)

def process_loop(log):
    sleep_count = 0
    sleep_time = 0.1
    while True:
        notice = zephyr.receive(block=False)
        if notice is None and options.forward_class_messages:
            # Ask the Humbug server about any new classes to subscribe to
            time.sleep(sleep_time)
            sleep_count += sleep_time
            if sleep_count > 15:
                sleep_count = 0
                update_subscriptions_from_humbug()
            continue

        try:
            zsig, body = notice.message.split("\x00", 1)
            is_personal = False
            is_huddle = False

            if notice.opcode == "PING":
                # skip PING messages
                continue

            if isinstance(zsig, str):
                # Check for width unicode character u'\u200B'.encode("utf-8")
                if u'\u200B'.encode("utf-8") in zsig:
                    print "Skipping message from Humbug!"
                    continue

            sender = notice.sender.lower().replace("athena.mit.edu", "mit.edu")
            recipient = notice.recipient.lower().replace("athena.mit.edu", "mit.edu")

            if (notice.cls.lower() == "message" and
                notice.instance.lower() == "personal"):
                is_personal = True
                if body.startswith("CC:"):
                    is_huddle = True
                    # Map "CC: sipbtest espuser" => "starnine@mit.edu,espuser@mit.edu"
                    huddle_recipients_list = [compute_humbug_username(x.strip()) for x in
                                              body.split("\n")[0][4:].split()]
                    if sender not in huddle_recipients_list:
                        huddle_recipients_list.append(sender)
                    huddle_recipients = ",".join(huddle_recipients_list)

            # Drop messages not to the listed subscriptions
            if (notice.cls.lower() not in current_zephyr_subs) and not \
                    (is_personal and options.forward_personals):
                print "Skipping ...", notice.cls, notice.instance, is_personal
                continue

            if is_huddle:
                zeph = { 'type'      : 'personal',
                         'time'      : str(notice.time),
                         'sender'    : sender,
                         'recipient' : huddle_recipients,
                         'zsig'      : zsig,  # logged here but not used by app
                         'content'   : body.split("\n", 1)[1] }
            elif is_personal:
                zeph = { 'type'      : 'personal',
                         'time'      : str(notice.time),
                         'sender'    : sender,
                         'recipient' : compute_humbug_username(recipient),
                         'zsig'      : zsig,  # logged here but not used by app
                         'content'   : body }
            else:
                zeph = { 'type'      : 'stream',
                         'time'      : str(notice.time),
                         'sender'    : sender,
                         'stream'    : notice.cls.lower(),
                         'subject'   : notice.instance.lower(),
                         'zsig'      : zsig,  # logged here but not used by app
                         'content'   : body }

            print "%s: received a message on %s/%s from %s..." % \
                (datetime.datetime.now(), notice.cls, notice.instance, notice.sender)
            log.write(simplejson.dumps(zeph) + '\n')
            log.flush()

            res = send_humbug(zeph)
            if res.get("result") != "success":
                print >>sys.stderr, 'Error relaying zephyr'
                print zeph
                print res
        except:
            print >>sys.stderr, 'Error relaying zephyr'
            traceback.print_exc()
            time.sleep(2)


def zephyr_to_humbug(options):
    import mit_subs_list
    if options.forward_class_messages:
        for sub in mit_subs_list.all_subs:
            ensure_subscribed(sub)
    update_subscriptions_from_humbug()
    if options.forward_personals:
        subs.add(("message", "personal", "*"))

    if options.resend_log:
        with open('zephyrs', 'r') as log:
            for ln in log:
                try:
                    zeph = simplejson.loads(ln)
                    print "sending saved message to %s from %s..." % \
                        (zeph.get('class', zeph.get('recipient')), zeph['sender'])
                    send_humbug(zeph)
                except:
                    print >>sys.stderr, 'Could not send saved zephyr'
                    traceback.print_exc()
                    time.sleep(2)

    print "Starting receive loop"

    if options.enable_log:
        log_file = "zephyrs"
    else:
        log_file = "/dev/null"

    with open(log_file, 'a') as log:
        process_loop(log)

def forward_to_zephyr(message):
    zsig = u"%s\u200B" % (username_to_fullname(message["sender_email"]))
    if ' dot ' in zsig:
        print "ERROR!  Couldn't compute zsig for %s!" % (message["sender_email"])
        return

    content = message["content"]
    cleaned_content = content.replace('&lt;','<').replace('&gt;','>').replace('&amp;', '&')
    wrapped_content = "\n".join("\n".join(textwrap.wrap(line))
            for line in cleaned_content.split("\n"))

    print "Sending message from %s humbug=>zephyr at %s" % (message["sender_email"], datetime.datetime.now())
    if message['type'] == "stream":
        zeph = zephyr.ZNotice(sender=message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                              auth=True, cls=message["display_recipient"],
                              instance=message["subject"])
        body = "%s\0%s" % (zsig, wrapped_content)
        zeph.setmessage(body)
        zeph.send()
    elif message['type'] == "personal":
        zeph = zephyr.ZNotice(sender=message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                              auth=True, recipient=message["display_recipient"].replace("mit.edu", "ATHENA.MIT.EDU"),
                              cls="message", instance="personal")
        body = "%s\0%s" % (zsig, wrapped_content)
        zeph.setmessage(body)
        zeph.send()
    elif message['type'] == "huddle":
        cc_list = ["CC:"]
        cc_list.extend([user["email"].replace("@mit.edu", "")
                        for user in message["display_recipient"]])
        body = "%s\0%s\n%s" % (zsig, " ".join(cc_list), wrapped_content)
        for r in message["display_recipient"]:
            zeph = zephyr.ZNotice(sender=message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                                  auth=True, recipient=r["email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                                  cls="message", instance="personal")
            zeph.setmessage(body)
            zeph.send()

def maybe_forward_to_zephyr(message):
    if message["sender_email"] == os.environ["USER"] + "@mit.edu":
        if float(message["timestamp"]) < float(datetime.datetime.now().strftime("%s")) - 15:
            print "Alert!  Out of order message!", message["timestamp"], datetime.datetime.now().strftime("%s")
            return
        forward_to_zephyr(message)

def humbug_to_zephyr(options):
    # Sync messages from zephyr to humbug
    print "Starting syncing messages."
    humbug_client.call_on_each_message(maybe_forward_to_zephyr,
                                       options={"mit_sync_bot": 'yes'})

if options.forward_to_humbug:
    zephyr_to_humbug(options)
else:
    humbug_to_zephyr(options)
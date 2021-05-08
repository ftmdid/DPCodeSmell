#!/usr/bin/python
import mechanize
import urllib.request, urllib.parse, urllib.error
import sys
import logging
import zephyr
import traceback
import simplejson
import re
import time
import subprocess
import optparse
import os
zephyr.init()

parser = optparse.OptionParser()
parser.add_option('--forward-class-messages',
                  dest='forward_class_messages',
                  default=False,
                  action='store_true')
parser.add_option('--resend-log',
                  dest='resend_log',
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
(options, args) = parser.parse_args()

browser = None
csrf_token = None

def browser_login():
    logger = logging.getLogger("mechanize")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)

    global browser
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    ## debugging code to consider
    # browser.set_debug_http(True)
    # browser.set_debug_responses(True)
    # browser.set_debug_redirects(True)
    # browser.set_handle_refresh(False)

    browser.add_password("https://app.humbughq.com/", "tabbott", "xxxxxxxxxxxxxxxxx", "wiki")
    browser.open("https://app.humbughq.com/")
    browser.follow_link(text_regex="\s*Log in\s*")
    browser.select_form(nr=0)
    browser["username"] = "starnine@mit.edu"
    browser["password"] = "xxxxxxxx"

    global csrf_token
    csrf_token = browser["csrfmiddlewaretoken"]

    browser.submit()

def send_humbug(zeph):
    zeph['fullname']  = username_to_fullname(zeph['sender'])
    zeph['shortname'] = zeph['sender'].split('@')[0]

    browser.addheaders.append(('X-CSRFToken', csrf_token))
    try:
        zephyr_data = urllib.parse.urlencode([(k, v.decode('utf-8').encode('utf-8')) for k,v in list(zeph.items())])
    except UnicodeDecodeError as e:
        print("UnicodeDecodeError!")
        print(zeph)
        print(e)
    browser.open("https://app.humbughq.com/forge_zephyr/", zephyr_data)

def fetch_fullname(username):
    try:
        match_user = re.match(r'([a-zA-Z0-9_]+)@mit\.edu', username)
        if match_user:
            proc = subprocess.Popen(['hesinfo', match_user.group(1), 'passwd'], stdout=subprocess.PIPE)
            out, _err_unused = proc.communicate()
            if proc.returncode == 0:
                return out.split(':')[4].split(',')[0]
    except:
        print('Error getting fullname for', username, file=sys.stderr)
        traceback.print_exc()

    return username.title().replace('@', ' at ').replace('.', ' dot ')

fullnames = {}
def username_to_fullname(username):
    if username not in fullnames:
        fullnames[username] = fetch_fullname(username)
    return fullnames[username]


def process_loop(log):
    import mit_subs_list
    while True:
        try:
            notice = zephyr.receive(block=True)
            zsig, body = notice.message.split("\x00", 1)
            is_personal = False
            is_huddle = False

            if zsig.endswith("`") and zsig.startswith("`"):
                print("Skipping message from Humbug!")
                continue

            sender = notice.sender.lower().replace("athena.mit.edu", "mit.edu")
            recipient = notice.recipient.lower().replace("athena.mit.edu", "mit.edu")

            if (notice.cls == "message" and
                notice.instance == "personal"):
                is_personal = True
                if body.startswith("CC:"):
                    is_huddle = True
                    # Map "CC: sipbtest espuser" => "starnine@mit.edu,espuser@mit.edu"
                    huddle_recipients_list = [x + "@mit.edu" for x in
                                              body.split("\n")[0][4:].split()]
                    if sender not in huddle_recipients_list:
                        huddle_recipients_list.append(sender)
                    huddle_recipients = ",".join(huddle_recipients_list)

            if notice.opcode != "":
                # skip PING messages
                continue

            # Drop messages not to the listed subscriptions
            if (notice.cls not in mit_subs_list.all_subs) and not (is_personal and
                                                                   options.forward_personals):
                print("Skipping ...", notice.cls, notice.instance, is_personal)
                continue

            if is_huddle:
                zeph = { 'type'      : 'personal',
                         'time'      : str(notice.time),
                         'sender'    : sender,
                         'recipient' : huddle_recipients,
                         'zsig'      : zsig,  # logged here but not used by app
                         'new_zephyr': body.split("\n", 1)[1] }
            elif is_personal:
                zeph = { 'type'      : 'personal',
                         'time'      : str(notice.time),
                         'sender'    : sender,
                         'recipient' : recipient,
                         'zsig'      : zsig,  # logged here but not used by app
                         'new_zephyr': body }
            else:
                zeph = { 'type'      : 'class',
                         'time'      : str(notice.time),
                         'sender'    : sender,
                         'class'     : notice.cls,
                         'instance'  : notice.instance,
                         'zsig'      : zsig,  # logged here but not used by app
                         'new_zephyr': body }

            log.write(simplejson.dumps(zeph) + '\n')
            log.flush()

            print("received a message on %s/%s from %s..." % \
                (notice.cls, notice.instance, notice.sender))
            send_humbug(zeph)
        except:
            print('Error relaying zephyr', file=sys.stderr)
            traceback.print_exc()
            time.sleep(2)


def zephyr_to_humbug(options):
    browser_login()

    import mit_subs_list
    subs = zephyr.Subscriptions()
    if options.forward_class_messages:
        for sub in mit_subs_list.all_subs:
            subs.add((sub, '*', '*'))
    if options.forward_personals:
        subs.add(("message", "personal", "*"))

    if options.resend_log:
        with open('zephyrs', 'r') as log:
            try:
                for ln in log:
                    zeph = simplejson.loads(ln)
                    print("sending saved message to %s from %s..." % \
                        (zeph.get('class', zeph.get('recipient')), zeph['sender']))
                    send_humbug(zeph)
            except:
                print('Could not send saved zephyr', file=sys.stderr)
                traceback.print_exc()
                time.sleep(2)

    print("Starting receive loop")

    with open('zephyrs', 'a') as log:
        process_loop(log)

def get_zephyrs(last_received):
        browser.addheaders.append(('X-CSRFToken', csrf_token))
        submit_hash = {'last_received': last_received,
                       "mit_sync_bot": 'yes'}
        submit_data = urllib.parse.urlencode([(k, v.encode('utf-8')) for k,v in list(submit_hash.items())])
        res = browser.open("https://app.humbughq.com/get_updates_longpoll", submit_data)
        return simplejson.loads(res.read())['zephyrs']


def send_zephyr(message):
    zsig = "`Timothy G. Abbott`"
    if message['type'] == "class":
        zeph = zephyr.ZNotice(sender=message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                              auth=True, cls="tabbott-test4",
                              instance=message["display_recipient"] + "/" + message["instance"])
        body = "%s\0%s" % (zsig, message['content'])
    elif message['type'] == "personal":
        zeph = zephyr.ZNotice(sender=message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                              auth=True, cls="tabbott-test4",
                              instance=message["display_recipient"])
        body = "%s\0%s" % (zsig, message['content'])
    elif message['type'] == "huddle":
        # TODO: This needs to send one message to each person, I think
        zeph = zephyr.ZNotice(sender=message["sender_email"].replace("mit.edu", "ATHENA.MIT.EDU"),
                              auth=True, cls="tabbott-test4",
                              instance="huddle!")
        cc_list = ["CC:"]
        cc_list.extend([user["email"].replace("@mit.edu", "")
                        for user in message["display_recipient"]])
        body = "%s\0%s\n%s" % (zsig, " ".join(cc_list), message['content'])
    zeph.setmessage(body)
    zeph.send()

def humbug_to_zephyr(options):
    # Sync messages from zephyr to humbug
    browser_login()
    print("Starting get_updates_longpoll.")
    zephyrs = get_zephyrs('0')
    while True:
        last_received = str(max([z["id"] for z in zephyrs]))
        new_zephyrs = get_zephyrs(last_received)
        for zephyr in new_zephyrs:
            print(zephyr)
            if zephyr["sender_email"] == os.environ["USER"] + "@mit.edu":
                send_zephyr(zephyr)
        zephyrs.extend(new_zephyrs)

if options.forward_to_humbug:
    zephyr_to_humbug(options)
else:
    humbug_to_zephyr(options)
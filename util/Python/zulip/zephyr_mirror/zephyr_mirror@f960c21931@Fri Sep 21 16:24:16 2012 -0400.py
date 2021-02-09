#!/usr/bin/python
import mechanize
import urllib
import sys
import logging
import zephyr
import traceback
import simplejson
import re
import time
import subprocess
import optparse

from mit_subs_list import subs_list

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

def send_zephyr(zeph):
    zeph['fullname']  = username_to_fullname(zeph['sender'])
    zeph['shortname'] = zeph['sender'].split('@')[0]

    browser.addheaders.append(('X-CSRFToken', csrf_token))
    zephyr_data = urllib.urlencode([(k, v.encode('utf-8')) for k,v in zeph.items()])
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
        print >>sys.stderr, 'Error getting fullname for', username
        traceback.print_exc()

    return username.title().replace('@', ' at ').replace('.', ' dot ')

fullnames = {}
def username_to_fullname(username):
    if username not in fullnames:
        fullnames[username] = fetch_fullname(username)
    return fullnames[username]

browser_login()

subs = zephyr.Subscriptions()
if options.forward_class_messages:
    for sub in subs_list:
        subs.add((sub, '*', '*'))
if options.forward_personals:
    subs.add(("message", "personal", "*"))

if options.resend_log:
    with open('zephyrs', 'r') as log:
        try:
            for ln in log:
                zeph = simplejson.loads(ln)
                print "sending saved message to %s from %s..." % \
                    (zeph.get('class', zeph.get('recipient')), zeph['sender'])
                send_zephyr(zeph)
        except:
            print >>sys.stderr, 'Could not send saved zephyr'
            traceback.print_exc()
            time.sleep(2)

with open('zephyrs', 'a') as log:
    print "Starting receive loop"
    while True:
        try:
            notice = zephyr.receive(block=True)
            zsig, body = notice.message.split("\x00", 1)
            is_personal = False
            is_huddle = False

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
            if (notice.cls not in subs_list) and not (is_personal and
                                                      options.forward_personals):
                print "Skipping ...", notice.cls, notice.instance, is_personal
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

            print "received a message on %s/%s from %s..." % \
                (notice.cls, notice.instance, notice.sender)
            send_zephyr(zeph)
        except:
            print >>sys.stderr, 'Error relaying zephyr'
            traceback.print_exc()
            time.sleep(2)
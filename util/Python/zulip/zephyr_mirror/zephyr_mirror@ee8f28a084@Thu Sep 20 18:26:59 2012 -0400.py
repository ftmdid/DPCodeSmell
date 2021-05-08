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

from mit_subs_list import subs_list

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
    zephyr_data = urllib.parse.urlencode([(k, v.encode('utf-8')) for k,v in list(zeph.items())])
    browser.open("https://app.humbughq.com/forge_zephyr/", zephyr_data)

def fetch_fullname(username):
    try:
        match_user = re.match(r'([a-zA-Z0-9_]+)@ATHENA\.MIT\.EDU', username)
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

browser_login()

subs = zephyr.Subscriptions()
for sub in subs_list:
    subs.add((sub, '*', '*'))

if sys.argv[1:] == ['--resend-log']:
    with open('zephyrs', 'r') as log:
        try:
            for ln in log:
                zeph = simplejson.loads(ln)
                print("sending saved message to %s from %s..." % (zeph['class'], zeph['sender']))
                send_zephyr(zeph)
        except:
            print('Could not send saved zephyr', file=sys.stderr)
            traceback.print_exc()
            time.sleep(2)

with open('zephyrs', 'a') as log:
    print("Starting receive loop")
    while True:
        try:
            notice = zephyr.receive(block=True)
            zsig, body = notice.message.split("\x00", 1)

            if notice.cls not in subs_list:
                continue
            zeph = { 'type'      : 'class',
                     'time'      : str(notice.time),
                     'sender'    : notice.sender[:30],
                     'class'     : notice.cls,
                     'instance'  : notice.instance,
                     'zsig'      : zsig,  # logged here but not used by app
                     'new_zephyr': body }

            log.write(simplejson.dumps(zeph) + '\n')
            log.flush()

            print("received a message on %s from %s..." % (zeph['class'], zeph['sender']))
            send_zephyr(zeph)
        except:
            print('Error relaying zephyr', file=sys.stderr)
            traceback.print_exc()
            time.sleep(2)
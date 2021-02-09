#!/usr/bin/env python

"""
Script to provide information about send-receive times.

It supports both munin and nagios outputs

It must be run on a machine that is using the live database for the
Django ORM.
"""

import datetime
import os
import sys
import optparse
import random


def total_seconds(timedelta):
    return (timedelta.microseconds + (timedelta.seconds + timedelta.days * 24 * 3600) * 10**6) / 10.**6

usage = """Usage: send-receive.py [options] [config]

       'config' is optional, if present will return config info.
        Otherwise, returns the output data."""

parser = optparse.OptionParser(usage=usage)
parser.add_option('--site',
                  dest='site',
                  default="https://humbughq.com",
                  action='store')

parser.add_option('--nagios',
                  dest='nagios',
                  action='store_true')

parser.add_option('--munin',
                  dest='munin',
                  action='store_true')
(options, args) = parser.parse_args()

if not options.nagios and not options.munin:
    print 'No output options specified! Please provide --munin or --nagios'
    sys.exit(0)

if len(args) > 2:
    print usage
    sys.exit(0)

if options.munin:
    if len(args) and args[0] == 'config':
        print \
"""graph_title Send-Receive times
graph_info The number of seconds it takes to send and receive a message from the server
graph_args -u 5 -l 0
graph_vlabel RTT (seconds)
sendreceive.label Send-receive round trip time
sendreceive.warning 3
sendreceive.critical 5"""
        sys.exit(0)

sys.path.append('/home/humbug/humbug-deployments/current/api')
import humbug

states = {
    "OK": 0,
    "WARNING": 1,
    "CRITICAL": 2,
    "UNKNOWN": 3
    }

def report(state, time, msg=None):
    if msg:
        print "%s: %s" % (state, msg)
    else:
        print "%s: send time was %s" % (state, time)
    exit(states[state])

def send_humbug(sender, message):
    result = sender.send_message(message)
    if result["result"] != "success" and options.nagios:
        report("CRITICAL", "Error sending Humbug, args were: %s, %s" % (message, result))

def get_humbug(recipient, max_message_id):
    result = recipient.get_messages({'last': str(max_message_id)})
    if result['result'] != "success" and options.nagios:
        report("CRITICAL", "Error receiving Humbugs, args were: %s, %s" % (max_message_id, result))
    return result['messages']

if options.site == "staging.humbughq.com":
    # hamlet and othello are default users on staging
    sender = "hamlet@humbughq.com"
    sender_key = "dfe1c934d555f4b9538d0d4cfd3069c2"
    recipient = "othello@humbughq.com"
    recipient_key = "4e5d97591bec64bf57d2698ffbb563e3"
else:
    # cordelia and iago are default users on prod
    sender = "iago@humbughq.com"
    sender_key = "d43b53c27a8106195b46781abc67901a"
    recipient = "cordelia@humbughq.com"
    recipient_key = "24cf18de98d5c31da9c6c79f0cbec195"

humbug_sender = humbug.Client(
    email=sender,
    api_key=sender_key,
    verbose=True,
    client="test: Humbug API",
    site=options.site)

humbug_recipient = humbug.Client(
    email=recipient,
    api_key=recipient_key,
    verbose=True,
    client="test: Humbug API",
    site=options.site)


max_message_id = humbug_recipient.get_profile().get('max_message_id')
msg_to_send = str(random.getrandbits(64))
time_start = datetime.datetime.now()

send_humbug(humbug_sender, {
    "type": 'private',
    "content": msg_to_send,
    "subject": "time to send",
    "to": recipient,
    })

msg_content = []

while msg_to_send not in msg_content:
    messages = get_humbug(humbug_recipient, max_message_id)
    time_diff = datetime.datetime.now() - time_start

    # Prevents checking the same messages everytime in the conditional
    # statement of the while loop
    max_message_id = max([msg['id'] for msg in messages])
    msg_content = [m['content'] for m in messages]

    if options.nagios:
        if time_diff.seconds > 3:
            report('WARNING', time_diff)
        if time_diff.seconds > 6:
            report('CRITICAL', time_diff)

if options.munin:
    print "sendreceive.value %s" % total_seconds(time_diff)
elif options.nagios:
    report('OK', time_diff)
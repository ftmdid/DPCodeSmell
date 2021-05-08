#!/usr/bin/python

"""
Forward messages sent to the configured email gateway to Zulip.

Messages to that address go to the Inbox of emailgateway@zulip.com.

Messages meant for Zulip have a special recipient form of

<stream name>+<regenerable stream token>@streams.zulip.com

We extract and validate the target stream from information in the
recipient address and retrieve, forward, and archive the message.

Run this management command out of a cron job.
"""



import email
import os
from email.header import decode_header
import logging
import re
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from zerver.lib.actions import decode_email_address
from zerver.lib.upload import upload_message_image
from zerver.models import Stream, get_user_profile_by_email, UserProfile

from twisted.internet import protocol, reactor, ssl
from twisted.mail import imap4

import html2text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../api"))
import zulip

## Setup ##

log_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=log_format)

formatter = logging.Formatter(log_format)
file_handler = logging.FileHandler(settings.EMAIL_LOG_PATH)
file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

email_gateway_user = None
api_key = None
try:
    email_gateway_user = get_user_profile_by_email(settings.EMAIL_GATEWAY_BOT_ZULIP_USER)
    api_key = email_gateway_user.api_key
except UserProfile.DoesNotExist:
    print("No configured %s user" % (settings.EMAIL_GATEWAY_BOT_ZULIP_USER,))


if settings.DEPLOYED:
    staging_api_client = zulip.Client(
            site="https://staging.zulip.com",
            email=settings.EMAIL_GATEWAY_BOT_ZULIP_USER,
            api_key=api_key)


    api_client = zulip.Client(
            site=settings.EXTERNAL_HOST,
            email=settings.EMAIL_GATEWAY_BOT_ZULIP_USER,
            api_key=api_key)
else:
    api_client = staging_api_client = zulip.Client(
            site=settings.EXTERNAL_HOST,
            email=settings.EMAIL_GATEWAY_BOT_ZULIP_USER,
            api_key=api_key)

def redact_stream(error_message):
    domain = settings.EMAIL_GATEWAY_PATTERN.rsplit('@')[-1]
    stream_match = re.search(r'\b(.*?)@' + domain, error_message)
    if stream_match:
        stream_name = stream_match.groups()[0]
        return error_message.replace(stream_name, "X" * len(stream_name))
    return error_message

def report_to_zulip(error_message):
    error_stream = Stream.objects.get(name="errors", realm__domain=settings.ADMIN_DOMAIN)
    send_zulip(error_stream, "email mirror error",
               """~~~\n%s\n~~~""" % (error_message,))

def log_and_report(email_message, error_message, debug_info):
    scrubbed_error = "Sender: %s\n%s" % (email_message.get("From"),
                                         redact_stream(error_message))

    if "to" in debug_info:
        scrubbed_error = "Stream: %s\n%s" % (redact_stream(debug_info["to"]),
                                             scrubbed_error)

    if "stream" in debug_info:
        scrubbed_error = "Realm: %s\n%s" % (debug_info["stream"].realm.domain,
                                            scrubbed_error)

    logger.error(scrubbed_error)
    report_to_zulip(scrubbed_error)

## Sending the Zulip ##

class ZulipEmailForwardError(Exception):
    pass

def send_zulip(stream, topic, content):
    # TODO: restrictions on who can send? Consider: cross-realm
    # messages, private streams.
    if stream.realm.domain == 'zulip.com':
        client = staging_api_client
    else:
        client = api_client

    message_data = {
        "type": "stream",
        # TODO: handle rich formatting.
        "content": content[:2000],
        "subject": topic[:60],
        "to": stream.name,
        "domain": stream.realm.domain
        }

    response = client.send_message(message_data)
    if response["result"] != "success":
        raise ZulipEmailForwardError(response["msg"])

def valid_stream(stream_name, token):
    try:
        stream = Stream.objects.get(email_token=token)
        return stream.name.lower() == stream_name.lower()
    except Stream.DoesNotExist:
        return False

def get_message_part_by_type(message, content_type):
    charsets = message.get_charsets()

    for idx, part in enumerate(message.walk()):
        if part.get_content_type() == content_type:
            content = part.get_payload(decode=True)
            if charsets[idx]:
                content = content.decode(charsets[idx], errors="ignore")
            return content

def extract_body(message):
    # If the message contains a plaintext version of the body, use
    # that.
    plaintext_content = get_message_part_by_type(message, "text/plain")
    if plaintext_content:
        return plaintext_content

    # If we only have an HTML version, try to make that look nice.
    html_content = get_message_part_by_type(message, "text/html")
    if html_content:
        converter = html2text.HTML2Text()
        converter.ignore_links = True
        converter.ignore_images = True
        return converter.handle(html_content)

    raise ZulipEmailForwardError("Unable to find plaintext or HTML message body")

def filter_footer(text):
    # Try to filter out obvious footers.
    possible_footers = [line for line in text.split("\n") if line.strip().startswith("--")]
    if len(possible_footers) != 1:
        # Be conservative and don't try to scrub content if there
        # isn't a trivial footer structure.
        return text

    return text.partition("--")[0].strip()

def extract_and_upload_attachments(message):
    attachment_links = []

    payload = message.get_payload()
    if not isinstance(payload, list):
        # This is not a multipart message, so it can't contain attachments.
        return ""

    for part in payload:
        content_type = part.get_content_type()
        filename = part.get_filename()
        if filename:
            s3_url = upload_message_image(filename, content_type,
                                          part.get_payload(decode=True),
                                          email_gateway_user)
            formatted_link = "[%s](%s)" % (filename, s3_url)
            attachment_links.append(formatted_link)

    return "\n".join(attachment_links)

def extract_and_validate(email):
    try:
        stream_name, token = decode_email_address(email)
    except TypeError:
        raise ZulipEmailForwardError("Malformed email recipient " + email)

    if not valid_stream(stream_name, token):
        raise ZulipEmailForwardError("Bad stream token from email recipient " + email)

    return Stream.objects.get(email_token=token)

## IMAP callbacks ##

def logout(result, proto):
    # Log out.
    return proto.logout()

def delete(result, proto):
    # Close the connection, which also processes any flags that were
    # set on messages.
    return proto.close().addCallback(logout, proto)

def find_emailgateway_recipient(message):
    # We can't use Delivered-To; if there is a X-Gm-Original-To
    # it is more accurate, so try to find the most-accurate
    # recipient list in descending priority order
    recipient_headers = ["X-Gm-Original-To", "Delivered-To", "To"]
    recipients = []
    for recipient_header in recipient_headers:
        r = message.get_all(recipient_header, None)
        if r:
            recipients = r
            break

    pattern_parts = [re.escape(part) for part in settings.EMAIL_GATEWAY_PATTERN.split('%s')]
    match_email_re = re.compile(".*?".join(pattern_parts))
    for recipient_email in recipients:
        if match_email_re.match(recipient_email):
            return recipient_email

    raise ZulipEmailForwardError("Missing recipient in mirror email")

def fetch(result, proto, mailboxes):
    if not result:
        return proto.logout()

    message_uids = list(result.keys())
    # Make sure we forward the messages in time-order.
    message_uids.sort()
    for uid in message_uids:
        message = email.message_from_string(result[uid]["RFC822"])
        subject = decode_header(message.get("Subject", "(no subject)"))[0][0]

        debug_info = {}

        try:
            body = filter_footer(extract_body(message))
            to = find_emailgateway_recipient(message)
            debug_info["to"] = to
            stream = extract_and_validate(to)
            debug_info["stream"] = stream
            body += extract_and_upload_attachments(message)
            if not body:
                # You can't send empty Zulips, so to avoid confusion over the
                # email forwarding failing, set a dummy message body.
                body = "(No email body)"
            send_zulip(stream, subject, body)
        except ZulipEmailForwardError as e:
            # TODO: notify sender of error, retry if appropriate.
            log_and_report(message, e.message, debug_info)

    # Delete the processed messages from the Inbox.
    message_set = ",".join([result[key]["UID"] for key in message_uids])
    d = proto.addFlags(message_set, ["\\Deleted"], uid=True, silent=False)
    d.addCallback(delete, proto)

    return d

def examine_mailbox(result, proto, mailbox):
    # Fetch messages from a particular mailbox.
    return proto.fetchMessage("1:*", uid=True).addCallback(fetch, proto, mailbox)

def select_mailbox(result, proto):
    # Select which mailbox we care about.
    mbox = [x for x in result if settings.EMAIL_GATEWAY_IMAP_FOLDER in x[2]][0][2]
    return proto.select(mbox).addCallback(examine_mailbox, proto, result)

def list_mailboxes(res, proto):
    # List all of the mailboxes for this account.
    return proto.list("","*").addCallback(select_mailbox, proto)

def connected(proto):
    d = proto.login(settings.EMAIL_GATEWAY_LOGIN, settings.EMAIL_GATEWAY_PASSWORD)
    d.addCallback(list_mailboxes, proto)
    d.addErrback(login_failed)
    return d

def login_failed(failure):
    return failure

def done(_):
    reactor.callLater(0, reactor.stop)

def main():
    imap_client = protocol.ClientCreator(reactor, imap4.IMAP4Client)
    d = imap_client.connectSSL(settings.EMAIL_GATEWAY_IMAP_SERVER, settings.EMAIL_GATEWAY_IMAP_PORT, ssl.ClientContextFactory())
    d.addCallbacks(connected, login_failed)
    d.addBoth(done)

class Command(BaseCommand):
    help = """Forward emails sent to the configured email gateway to Zulip.

Run this command out of a cron job.
"""

    def handle(self, **options):
        if (not settings.EMAIL_GATEWAY_BOT_ZULIP_USER or not settings.EMAIL_GATEWAY_LOGIN or
            not settings.EMAIL_GATEWAY_PASSWORD or not settings.EMAIL_GATEWAY_IMAP_SERVER or
            not settings.EMAIL_GATEWAY_IMAP_PORT or not settings.EMAIL_GATEWAY_IMAP_FOLDER or
            not email_gateway_user):
            print("Please configure the Email Mirror Gateway in your local_settings.py")
            exit(1)

        reactor.callLater(0, main)
        reactor.run()
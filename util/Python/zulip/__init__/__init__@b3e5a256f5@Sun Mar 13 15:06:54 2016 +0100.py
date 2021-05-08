# Webhooks for external integrations.

from zerver.models import get_client
from zerver.lib.actions import check_send_message
from zerver.lib.response import json_success, json_error
from zerver.decorator import REQ, \
    has_request_variables, authenticated_rest_api_view, \
    api_key_only_webhook_view

import pprint
import ujson

from .github import build_commit_list_content, build_message_from_gitlog


def truncate(string, length):
    if len(string) > length:
        string = string[:length-3] + '...'
    return string

@authenticated_rest_api_view
def api_zendesk_webhook(request, user_profile):
    """
    Zendesk uses trigers with message templates. This webhook uses the
    ticket_id and ticket_title to create a subject. And passes with zendesk
    user's configured message to zulip.
    """
    try:
        ticket_title = request.POST['ticket_title']
        ticket_id = request.POST['ticket_id']
        message = request.POST['message']
        stream = request.POST.get('stream', 'zendesk')
    except KeyError as e:
        return json_error('Missing post parameter %s' % (e.message,))

    subject = truncate('#%s: %s' % (ticket_id, ticket_title), 60)
    check_send_message(user_profile, get_client('ZulipZenDeskWebhook'), 'stream',
                       [stream], subject, message)
    return json_success()


PAGER_DUTY_EVENT_NAMES = {
    'incident.trigger': 'triggered',
    'incident.acknowledge': 'acknowledged',
    'incident.unacknowledge': 'unacknowledged',
    'incident.resolve': 'resolved',
    'incident.assign': 'assigned',
    'incident.escalate': 'escalated',
    'incident.delegate': 'delineated',
}

def build_pagerduty_formatdict(message):
    # Normalize the message dict, after this all keys will exist. I would
    # rather some strange looking messages than dropping pages.

    format_dict = {}
    format_dict['action'] = PAGER_DUTY_EVENT_NAMES[message['type']]

    format_dict['incident_id'] = message['data']['incident']['id']
    format_dict['incident_num'] = message['data']['incident']['incident_number']
    format_dict['incident_url'] = message['data']['incident']['html_url']

    format_dict['service_name'] = message['data']['incident']['service']['name']
    format_dict['service_url'] = message['data']['incident']['service']['html_url']

    # This key can be missing on null
    if message['data']['incident'].get('assigned_to_user', None):
        format_dict['assigned_to_email'] = message['data']['incident']['assigned_to_user']['email']
        format_dict['assigned_to_username'] = message['data']['incident']['assigned_to_user']['email'].split('@')[0]
        format_dict['assigned_to_url'] = message['data']['incident']['assigned_to_user']['html_url']
    else:
        format_dict['assigned_to_email'] = 'nobody'
        format_dict['assigned_to_username'] = 'nobody'
        format_dict['assigned_to_url'] = ''

    # This key can be missing on null
    if message['data']['incident'].get('resolved_by_user', None):
        format_dict['resolved_by_email'] = message['data']['incident']['resolved_by_user']['email']
        format_dict['resolved_by_username'] = message['data']['incident']['resolved_by_user']['email'].split('@')[0]
        format_dict['resolved_by_url'] = message['data']['incident']['resolved_by_user']['html_url']
    else:
        format_dict['resolved_by_email'] = 'nobody'
        format_dict['resolved_by_username'] = 'nobody'
        format_dict['resolved_by_url'] = ''

    trigger_message = []
    trigger_subject = message['data']['incident']['trigger_summary_data'].get('subject', '')
    if trigger_subject:
        trigger_message.append(trigger_subject)
    trigger_description = message['data']['incident']['trigger_summary_data'].get('description', '')
    if trigger_description:
        trigger_message.append(trigger_description)
    format_dict['trigger_message'] = '\n'.join(trigger_message)
    return format_dict


def send_raw_pagerduty_json(user_profile, stream, message, topic):
    subject = topic or 'pagerduty'
    body = (
        'Unknown pagerduty message\n'
        '``` py\n'
        '%s\n'
        '```') % (pprint.pformat(message),)
    check_send_message(user_profile, get_client('ZulipPagerDutyWebhook'), 'stream',
                       [stream], subject, body)


def send_formated_pagerduty(user_profile, stream, message_type, format_dict, topic):
    if message_type in ('incident.trigger', 'incident.unacknowledge'):
        template = (':imp: Incident '
        '[{incident_num}]({incident_url}) {action} by '
        '[{service_name}]({service_url}) and assigned to '
        '[{assigned_to_username}@]({assigned_to_url})\n\n>{trigger_message}')

    elif message_type == 'incident.resolve' and format_dict['resolved_by_url']:
        template = (':grinning: Incident '
        '[{incident_num}]({incident_url}) resolved by '
        '[{resolved_by_username}@]({resolved_by_url})\n\n>{trigger_message}')
    elif message_type == 'incident.resolve' and not format_dict['resolved_by_url']:
        template = (':grinning: Incident '
        '[{incident_num}]({incident_url}) resolved\n\n>{trigger_message}')
    else:
        template = (':no_good: Incident [{incident_num}]({incident_url}) '
        '{action} by [{assigned_to_username}@]({assigned_to_url})\n\n>{trigger_message}')

    subject = topic or 'incident {incident_num}'.format(**format_dict)
    body = template.format(**format_dict)

    check_send_message(user_profile, get_client('ZulipPagerDutyWebhook'), 'stream',
                       [stream], subject, body)


@api_key_only_webhook_view
@has_request_variables
def api_pagerduty_webhook(request, user_profile, stream=REQ(default='pagerduty'), topic=REQ(default=None)):
    payload = ujson.loads(request.body)

    for message in payload['messages']:
        message_type = message['type']

        if message_type not in PAGER_DUTY_EVENT_NAMES:
            send_raw_pagerduty_json(user_profile, stream, message, topic)

        try:
            format_dict = build_pagerduty_formatdict(message)
        except:
            send_raw_pagerduty_json(user_profile, stream, message, topic)
        else:
            send_formated_pagerduty(user_profile, stream, message_type, format_dict, topic)

    return json_success()

@api_key_only_webhook_view
@has_request_variables
def api_travis_webhook(request, user_profile, stream=REQ(default='travis'), topic=REQ(default=None)):
    message = ujson.loads(request.POST['payload'])

    author = message['author_name']
    message_type = message['status_message']
    changes = message['compare_url']

    good_status = ['Passed', 'Fixed']
    bad_status  = ['Failed', 'Broken', 'Still Failing']
    emoji = ''
    if message_type in good_status:
        emoji = ':thumbsup:'
    elif message_type in bad_status:
        emoji = ':thumbsdown:'
    else:
        emoji = "(No emoji specified for status '%s'.)" % (message_type,)

    build_url = message['build_url']

    template = (
        'Author: %s\n'
        'Build status: %s %s\n'
        'Details: [changes](%s), [build log](%s)')

    body = template % (author, message_type, emoji, changes, build_url)

    check_send_message(user_profile, get_client('ZulipTravisWebhook'), 'stream', [stream], topic, body)
    return json_success()
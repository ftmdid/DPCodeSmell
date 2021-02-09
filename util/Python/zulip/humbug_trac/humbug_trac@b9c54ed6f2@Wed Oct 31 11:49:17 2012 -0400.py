#!/usr/bin/python
#
# Humbug trac plugin -- sends humbugs when tickets change.
#
# Install by placing in the plugins/ subdirectory and then adding
# "humbug_trac" to the [components] section of the conf/trac.ini file,
# like so:
#
# [components]
# humbug_trac = enabled
#
# You may then need to restart trac (or restart Apache) for the bot
# (or changes to the bot) to actually be loaded by trac.
#
# Our install is trac.humbughq.com:/home/humbug/trac/

from trac.core import Component, implements
from trac.ticket import ITicketChangeListener
import sys

sys.path.append("/home/humbug/humbug")
import api.common
client = api.common.HumbugAPI(email="humbug+trac@humbughq.com",
                              api_key="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

def markdown_ticket_url(ticket, heading="ticket"):
    return "[%s #%s](https://trac.humbughq.com/ticket/%s)" % (heading, ticket.id, ticket.id)

def markdown_block(desc):
    return "\n\n>" + "\n> ".join(desc.split("\n")) + "\n"

def truncate(string, length):
    if len(string) <= length:
        return string
    return string[:length - 3] + "..."

def trac_subject(ticket):
    return truncate("Trac #%s: %s" % (ticket.id, ticket.values.get("summary")), 60)

def send_update(ticket, content):
    client.send_message({
            "type": "stream",
            "stream": "trac",
            "content": content,
            "subject": trac_subject(ticket)
            })

class HumbugPlugin(Component):
    implements(ITicketChangeListener)

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        content = "%s created new %s in component %s:\n%s" % (ticket.values.get("reporter"),
                                                              markdown_ticket_url(ticket),
                                                              ticket.values.get("component"),
                                                              ticket.values.get("summary"))
        if ticket.values.get("description") != "":
            content += ":%s" % markdown_block(ticket.values.get("description"))
        send_update(ticket, content)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.

        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        content = "%s updated %s:\n\n" % (author, markdown_ticket_url(ticket))
        if "summary" not in old_values:
            content += "(%s)\n" % (ticket.values.get("summary"),)
        for key in old_values.keys():
            if key == "description":
                content += '- Changed %s from %s to %s' % (key, markdown_block(old_values.get(key)),
                                                           markdown_block(ticket.values.get(key)))
            elif old_values.get(key) == "":
                content += '- Added %s **%s**\n' % (key, ticket.values.get(key))
            elif ticket.values.get(key) == "":
                content += '- Remove %s **%s**\n' % (key, old_values.get(key))
            else:
                content += '- Changed %s from **%s** to **%s**\n' % (key, old_values.get(key),
                                                                     ticket.values.get(key))

        if comment:
            content += '- Added a comment: %s' % (markdown_block(comment,))
        send_update(ticket, content)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        content = "%s was deleted." % markdown_ticket_url(ticket, heading="Ticket")
        send_update(ticket, content)
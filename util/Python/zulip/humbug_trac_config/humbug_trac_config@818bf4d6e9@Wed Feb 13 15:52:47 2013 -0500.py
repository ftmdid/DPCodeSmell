# -*- coding: utf-8 -*-
#
# Copyright © 2012 Humbug, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Change these constants:
HUMBUG_USER = "humbug+trac@humbughq.com"
HUMBUG_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
STREAM_FOR_NOTIFICATIONS = "trac"
TRAC_BASE_TICKET_URL = "https://trac.humbughq.com/ticket"

# Most people find that having every change in Trac result in a
# notification is too noisy -- in particular, when someone goes
# through recategorizing a bunch of tickets, that can often be noisy
# and annoying.  We solve this issue by only sending a notification if
# one of the more important fields is changed or the person making the
# change makes a comment.
#
# Total list of fields is:
# (priority, milestone, cc, owner, keywords, component, severity,
#  type, versions, description, resolution, summary)
#
# The following is the list of fields which can be changed without
# triggering a Humbug notification
TRAC_NOTIFY_FIELDS = ["description", "summary", "resolution"]

## If properly installed, the Humbug API should be in your import
## path, but if not, set a custom path below
HUMBUG_API_PATH = "/home/humbug/humbug/api"

# This should not need to change unless you have a custom Humbug subdomain.
HUMBUG_SITE = "https://staging.humbughq.com"
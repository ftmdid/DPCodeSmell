#!/usr/bin/python
import mechanize
import urllib.request, urllib.parse, urllib.error
import simplejson
from urllib.error import HTTPError
import time

class HumbugAPI():
    def __init__(self, email, api_key, verbose=False, site="https://app.humbughq.com"):
        self.browser = mechanize.Browser()
        self.browser.set_handle_robots(False)
        self.browser.add_password("https://app.humbughq.com/", "tabbott", "xxxxxxxxxxxxxxxxx", "wiki")
        self.api_key = api_key
        self.email = email
        self.verbose = verbose
        self.base_url = site

    def send_message(self, submit_hash):
        submit_hash["email"] = self.email
        submit_hash["api-key"] = self.api_key
        submit_data = urllib.parse.urlencode([(k, v.encode('utf-8')) for k,v in list(submit_hash.items())])
        res = self.browser.open(self.base_url + "/api/v1/send_message", submit_data)
        return simplejson.loads(res.read())

    def get_messages(self, options = {}):
        options["email"] = self.email
        options["api-key"] = self.api_key
        submit_data = urllib.parse.urlencode([(k, v.encode('utf-8')) for k,v in list(options.items())])
        res = self.browser.open(self.base_url + "/api/v1/get_messages", submit_data)
        return simplejson.loads(res.read())['zephyrs']

    def call_on_each_message(self, callback, options = {}):
        max_message_id = None
        while True:
            try:
                options["first"] = "0"
                options["last"] = str(last_received)
                messages = self.get_messages(options)
            except HTTPError as e:
                # 502/503 typically means the server was restarted; sleep
                # a bit, then try again
                if self.verbose:
                    print("HTTP Error getting zephyrs; trying again soon.")
                    print(e)
                time.sleep(1)
            except Exception as e:
                # For other errors, just try again
                print(e)
                time.sleep(2)
                continue
            for message in sorted(messages, key=lambda x: x["id"]):
                max_message_id = max(max_message_id, message["id"])
                callback(message)
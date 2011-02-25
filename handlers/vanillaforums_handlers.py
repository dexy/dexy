from StringIO import StringIO
from dexy.handler import DexyHandler

import json
import os
import pycurl
import re
import urllib

class VanillaForumHandler(DexyHandler):
    ALIASES = ['vanilla']
    FORUM_CONFIG_FILE = 'vanilla-config.json'

    def load_forum_conf(self):
        if not os.path.exists(self.FORUM_CONFIG_FILE):
            raise Exception("Could not find config file called %s" %
                            self.FORUM_CONFIG_FILE)

        f = open(self.FORUM_CONFIG_FILE, "r")
        try:
            self.forum_conf = json.load(f)
        except ValueError as e:
            print "error parsing JSON in", self.FORUM_CONFIG_FILE
            raise e
        f.close()

    def load_discussion_conf(self):
        self.artifact.load_input_artifacts()
        matches = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith("discuss.json|dexy")]
        try:
            self.k = matches[0]
        except IndexError as e:
            raise Exception("""no files called discuss.json|dexy were available as
                            inputs to %s""" % self.doc.name)

        try:
            self.discussion_conf = json.loads(self.artifact.input_artifacts_dict[self.k]['data'])
        except ValueError as e:
            print "error parsing JSON in", self.k
            raise e
        
    
    def process_text(self, input_text):
        self.load_forum_conf()
        self.load_discussion_conf()
        
        if self.discussion_conf.has_key('Name'):
            discussion_name = self.discussion_conf['Name']
        else:
            print "No 'Name' specified, using default"
            discussion_name = self.artifact.doc.name

        if self.discussion_conf.has_key('CategoryID'):
            discussion_category_id = self.discussion_conf['CategoryID']
        else:
            print "No 'CategoryID' specified, using default"
            discussion_category_id = 1

        user_cookie = self.forum_conf['user-cookie']
        api = self.forum_conf['api'].rstrip("/")

        print "using user_cookie %s" % user_cookie
        print "using api %s" % api

        c = pycurl.Curl()
        b = StringIO()
        c.setopt(c.URL, "%s/session" % api)
        c.setopt(c.COOKIE, "Vanilla=%s" % user_cookie)
        c.setopt(c.WRITEFUNCTION, b.write)
        c.perform()

        session_info = json.loads(b.getvalue())
        transient_key = session_info['user']['TransientKey']
        print "transient key", transient_key

        discussion_data = [
          ("Discussion/Name", discussion_name),
          ("Discussion/CategoryID", discussion_category_id),
          ("Discussion/TransientKey", transient_key),
          ("Discussion/Body", input_text)
          ]

        if self.discussion_conf.has_key('DiscussionID'):
           discussion_data.append(('Discussion/DiscussionID', self.discussion_conf['DiscussionID']))
        else:
           print "no 'DiscussionID' specified, creating new discussion"
    
        c = pycurl.Curl()
        b = StringIO()
        c.setopt(c.URL, "http://discuss.dexy.it/api/discussion/add")
        c.setopt(c.COOKIE, "Vanilla=%s" % user_cookie)
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, urllib.urlencode(discussion_data))
        c.setopt(c.WRITEFUNCTION, b.write)
        c.perform()
        
        result = json.loads(b.getvalue())
        print result
        self.discussion_conf['DiscussionID'] = result['DiscussionID']

        json_file = re.sub('\|dexy$', "", self.k)
        f = open(json_file, 'w')
        json.dump(self.discussion_conf, f)
        f.close()
        return "ok"

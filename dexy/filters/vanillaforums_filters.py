from dexy.dexy_filter import DexyFilter
from StringIO import StringIO
import json
import os
import pycurl
import re
import urllib

class VanillaForumFilter(DexyFilter):
    ALIASES = ['vanilla']
    FORUM_CONFIG_FILE = 'vanilla-config.json'
    DISCUSSION_CONFIG_FILE = 'discuss.json|dexy'

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
        self.user_cookie = self.forum_conf['user-cookie']
        self.site = self.forum_conf['site'].rstrip('/')

    def load_discussion_conf(self):
        matches = [k for k in self.artifact.inputs().keys() if k.endswith(self.DISCUSSION_CONFIG_FILE)]
        try:
            self.k = matches[0]
        except IndexError as e:
            raise Exception("""no files matching %s were available as
                            inputs to %s""" % (self.DISCUSSION_CONFIG_FILE, self.artifact.key))

        try:
            self.discussion_conf = json.loads(self.artifact.inputs()[self.k]['data'])
        except ValueError as e:
            print "error parsing JSON in", self.k
            raise e

    def obtain_transient_key(self):
        c = pycurl.Curl()
        b = StringIO()
        c.setopt(c.URL, "%s/api/session" % self.site)
        c.setopt(c.COOKIE, "Vanilla=%s" % self.user_cookie)
        c.setopt(c.WRITEFUNCTION, b.write)
        c.perform()

        session_info = json.loads(b.getvalue())
        self.transient_key = session_info['user']['TransientKey']

    def process_text(self, input_text):
        self.load_forum_conf()
        self.load_discussion_conf()
        self.obtain_transient_key()

        if self.discussion_conf.has_key('Name'):
            discussion_name = self.discussion_conf['Name']
        else:
            raise Exception("Please specify a 'Name' for your discussion.")

        if self.discussion_conf.has_key('CategoryID'):
            discussion_category_id = self.discussion_conf['CategoryID']
        else:
            print "No 'CategoryID' specified, using default"
            discussion_category_id = 1


        discussion_data = [
          ("Discussion/Name", discussion_name),
          ("Discussion/CategoryID", discussion_category_id),
          ("Discussion/TransientKey", self.transient_key),
          ("Discussion/Body", input_text)
          ]

        if self.discussion_conf.has_key('DiscussionID'):
           discussion_data.append(('Discussion/DiscussionID', self.discussion_conf['DiscussionID']))
        else:
           print "no 'DiscussionID' specified, creating new discussion"

        c = pycurl.Curl()
        b = StringIO()
        c.setopt(c.URL, "%s/api/discussion/add" % self.site)
        c.setopt(c.COOKIE, "Vanilla=%s" % self.user_cookie)
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

class VanillaForumCommentFilter(VanillaForumFilter):
    ALIASES = ['vanillacomment']
    DISCUSSION_CONFIG_FILE = 'comment.json|dexy'

    def process_text(self, input_text):
        self.load_forum_conf()
        self.load_discussion_conf()

        self.obtain_transient_key()

        if self.discussion_conf.has_key('CategoryID'):
            comment_category_id = self.discussion_conf['CategoryID']
        else:
            print "No 'CategoryID' specified, using default"
            comment_category_id = 1

        if self.discussion_conf.has_key('DiscussionID'):
            comment_discussion_id = self.discussion_conf['DiscussionID']
        else:
            raise Exception("You must specify a valid DiscussionID")


        comment_data = [
          ("Comment/CategoryID", comment_category_id),
          ("Comment/DiscussionID", comment_discussion_id),
          ("Comment/TransientKey", self.transient_key),
          ("Comment/Body", input_text)
          ]

        if self.discussion_conf.has_key('CommentID'):
           comment_data.append(('Comment/CommentID', self.discussion_conf['CommentID']))
        else:
           print "no 'CommentID' specified, creating new comment"

        c = pycurl.Curl()
        b = StringIO()
        c.setopt(c.URL, "%s/api/comment/add" % self.site)
        c.setopt(c.COOKIE, "Vanilla=%s" % self.user_cookie)
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, urllib.urlencode(comment_data))
        c.setopt(c.WRITEFUNCTION, b.write)
        c.perform()

        result = json.loads(b.getvalue())
        print result
        self.discussion_conf['CommentID'] = result['CommentID']

        json_file = re.sub('\|dexy$', "", self.k)
        f = open(json_file, 'w')
        json.dump(self.discussion_conf, f)
        f.close()
        return "ok"

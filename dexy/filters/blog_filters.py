from dexy.dexy_filter import DexyFilter
import json
import os
import re

class BlogFilter(DexyFilter):
    ALIASES = ['blogfilter']
    BLOG_CONFIG_FILE = 'blog-config.json'
    PASSWORD_KEYS = ['password', 'pass', 'pw']
    USERNAME_KEYS = ['username', 'user']

    def load_blog_conf(self):
        if not os.path.exists(self.BLOG_CONFIG_FILE):
            raise Exception("Could not find config file called %s" % self.BLOG_CONFIG_FILE)
        f = open(self.BLOG_CONFIG_FILE, "r")
        self.blog_conf = json.load(f)
        f.close()

        self.password = None
        for k in self.PASSWORD_KEYS:
            if self.blog_conf.has_key(k):
                self.password = self.blog_conf[k]
        if not self.password:
            raise Exception("none of %s was found in blog conf file %s, need to set a password" % (",".join(self.PASSWORD_KEYS), self.BLOG_CONFIG_FILE))

        self.username = None
        for k in self.USERNAME_KEYS:
            if self.blog_conf.has_key(k):
                self.username = self.blog_conf[k]
        if not self.username:
            raise Exception("none of %s was found in blog conf file %s, need to set a username" % (",".join(self.USERNAME_KEYS), self.BLOG_CONFIG_FILE))


    def load_post_conf(self):
        matches = [k for k in self.artifact.inputs().keys() if k.endswith("post.json|dexy")]
        if len(matches) == 0:
            raise Exception("no input found matching post.json|dexy! Make sure you create a post.json file, run it through the dexy filter, and make it an input to your blog post")
        self.k = matches[0]
        self.post_conf = json.loads(self.artifact.inputs()[self.k].output_text())

    def process_text(self, input_text):
        self.load_blog_conf()
        self.load_post_conf()
        api = self.initialize_api()

        if self.post_conf.has_key('post-id'):
            post_id = self.post_conf['post-id']
            self.update_post(api, input_text, self.post_conf['post-id'])
        else:
            post_id = self.new_post(api, input_text)
            self.post_conf['post-id'] = post_id

            json_file = re.sub('\|dexy$', "", self.k)
            f = open(json_file, 'w')
            json.dump(self.post_conf, f)
            f.close()

        return "%s" % post_id

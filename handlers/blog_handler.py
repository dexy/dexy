from dexy.handler import DexyHandler

import os
import re
import json

class BlogHandler(DexyHandler):
    ALIASES = None
    BLOG_CONFIG_FILE = 'blog-config.json'

    def load_blog_conf(self):
        if not os.path.exists(self.BLOG_CONFIG_FILE):
            raise Exception("Could not find config file called %s" % self.BLOG_CONFIG_FILE)
        f = open(self.BLOG_CONFIG_FILE, "r")
        self.blog_conf = json.load(f)
        f.close()
    
    def load_post_conf(self):
        self.artifact.load_input_artifacts()
        matches = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith("post.json|dexy")]
        self.k = matches[0]
        self.post_conf = json.loads(self.artifact.input_artifacts_dict[self.k]['data'])

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

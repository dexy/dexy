from dexy.dexy_filter import DexyFilter
import json
import os
import re

class BlogFilter(DexyFilter):
    ALIASES = ['blogfilter']



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

import dexy.filters.blog_filters

# TODO write tumblr access from scratch as e.g. saving as draft raises an error
# http://code.google.com/p/python-tumblr/
from tumblr import Api
class TumblrFilter(dexy.filters.blog_filters.BlogFilter):
    """
    Posts to a tumblr blog.
    """
    ALIASES = ['tumblr']
    BLOG_CONFIG_FILE = 'tumblr-config.json'

    def initialize_api(self):
        blog = self.blog_conf['blog']
        user = self.blog_conf['user']
        password = self.blog_conf['password']
        return Api(blog, user, password)

    def new_post(self, api, input_text):
        title = self.post_conf.pop('title')
        post = api.write_regular(title, input_text, **self.post_conf)
        return post['post-id']

    def update_post(self, api, input_text, post_id):
        raise Exception("not implemented!")


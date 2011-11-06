import dexy.filters.blog_filter
import posterous # http://github.com/nureineide/posterous-python

class PosterousFilter(dexy.filters.blog_filter.BlogFilter):
    """
    IN DEVELOPMENT. Post to a posterous blog. (Due to posterous' stripping out
    formatting, is difficult to apply syntax highlighting in usual way.)
    """
    ALIASES = ['posterous']
    BLOG_CONFIG_FILE = 'posterous-config.json'

    def initialize_api(self):
        user = self.blog_conf['user']
        password = self.blog_conf['pass']
        return posterous.API(user, password)

    def new_post(self, api, input_text):
        post = api.new_post(title = self.post_conf['title'], body = input_text)
        return post.id

    def update_post(self, api, input_text, post_id):
        api.update_post(
            post_id = post_id,
            title = self.post_conf['title'],
            body = input_text
        )



import dexy.filters.blog_filters
import re
import xmlrpclib

class WordPressFilter(dexy.filters.blog_filters.BlogFilter):
    """
    Posts to a WordPress blog.

    Create a file called wp-config.json in the root of your project directory.
    This should include your blog's XMLRPC endpoint URL, your username and your
    password in a JSON object.

    For example:

    {
       "user" : "author",
       "pass" : "password",
       "xmlrpc_url" : "http://blog.dexy.it:80/xmlrpc.php"
    }

    """
    ALIASES = ['wp']
    BLOG_CONFIG_FILE = 'wp-config.json'
    MIME_TYPES = {
        'png' : 'image/png',
        'jpg' : 'image/jpeg',
        'jpeg' : 'image/jpeg',
        'aiff' : 'audio/x-aiff',
        'wav' : 'audio/x-wav',
        'wave' : 'audio/x-wav',
        'mp3' : 'audio/mpeg'
    }
    BLOG_ID = 0

    def initialize_api(self):
        api = xmlrpclib.ServerProxy(self.blog_conf["xmlrpc_url"], verbose=False)
        #print api.system.listMethods()
        return api

    def content_dict(self, api, input_text):
        input_text = self.upload_files_and_replace_links(api, input_text)
        content = { 'title' : self.post_conf['title'], 'description' : input_text}
        return content

    def new_post(self, api, input_text):
        post_id = api.metaWeblog.newPost(
            self.BLOG_ID,
            self.username,
            self.password,
            self.content_dict(api, input_text),
            self.post_conf['publish']
        )
        return post_id

    def update_post(self, api, input_text, post_id):
        api.metaWeblog.editPost(
            post_id,
            self.username,
            self.password,
            self.content_dict(api, input_text),
            self.post_conf['publish']
        )

    def upload_files_and_replace_links(self, api, input_text):
        url_cache = {}

        def upload_files_to_wp(regexp, input_text):
            for t in re.findall(regexp, input_text):
                if url_cache.has_key(t[1]):
                    url = url_cache[t[1]]
                    self.log.info("using cached url %s %s" % (t[1], url))
                else:
                    f = open(t[1], 'rb')
                    image_base_64 = xmlrpclib.Binary(f.read())
                    f.close()

                    upload_file = {
                        'name' : t[1].split("/")[1],
                        'type' : self.MIME_TYPES[t[2]], # *should* raise error if not on whitelist
                        'bits' : image_base_64,
                        'overwrite' : 'true'
                    }
                    upload_result = api.wp.uploadFile(
                        self.BLOG_ID,
                        self.username,
                        self.password,
                        upload_file
                    )
                    url = upload_result['url']
                    url_cache[t[1]] = url
                    self.log.info("uploaded %s to %s" % (t[1], url))

                replace_string = t[0].replace(t[1], url)
                input_text = input_text.replace(t[0], replace_string)
            return input_text

        input_text = upload_files_to_wp('(<img src="(artifacts/.+\.(\w{2,4}))")', input_text)
        input_text = upload_files_to_wp('(<embed src="(artifacts/.+\.(\w{2,4}))")', input_text)
        input_text = upload_files_to_wp('(<audio src="(artifacts/.+\.(\w{2,4}))")', input_text)
        return input_text

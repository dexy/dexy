from dexy.plugins.api_filters import ApiFilter
import dexy.exceptions
import json
import mimetypes
import os
import xmlrpclib

class WordPressFilter(ApiFilter):
    """
    Posts to a WordPress blog.

    WordPress has a very confusing API setup since it implements its own API
    methods (under the wp namespace) and also supports the Blogger, metaWeblog
    and MovableType APIs. Unfortunately the wp namespace methods are incomplete,
    so you have to mix and match.

    Uses the WP XMLRPC API where possible:
    http://codex.wordpress.org/XML-RPC_wp

    Creating and editing blog posts uses the metaWeblog API:
    http://xmlrpc.scripting.com/metaWeblogApi.html

    If this filter is applied to a document with file extension in
    PAGE_CONTENT_EXTENSIONS (defined in ApiFilter class and inherited here)
    then the document will be uploaded to WordPress as a blog post.

    If not, then the document is assumed to be an image or other binary asset,
    and file upload will be used instead, so a new element will be added to the
    Media Library. If this is the case, then the URL is the resulting image is
    returned, so you can use that URL directly in your blog posts or other
    documents that need to link to the asset.

    IMPORTANT There is currently a frustrating bug in WP:
    http://core.trac.wordpress.org/ticket/17604
    which means that every time you run this filter, a *new* image asset will
    be created, even though we tell WordPress to overwrite the existing image
    of the same name. You will end up with dozens of copies of this image
    cluttering up your media library.

    For now, we recommend using an external site to host your images and
    assets, such as Amazon S3.
    """
    ALIASES = ['wp', 'wordpress']
    API_KEY_NAME = 'wordpress'
    BLOG_ID = 0
    DOCUMENT_API_CONFIG_FILE = "wordpress.json"
    DOCUMENT_API_CONFIG_FILE_KEY = "wordpress-config-file"
    OUTPUT_EXTENSIONS = ['.txt']

    @classmethod
    def docmd_create_keyfile(klass):
        """
        Creates a key file for WordPress in the local directory.
        """
        if os.path.exists(klass.PROJECT_API_KEY_FILE):
            msg = "File %s already exists!" % klass.PROJECT_API_KEY_FILE
            raise dexy.exceptions.UserFeedback(msg)

        keyfile_content = {}
        keyfile_content[klass.API_KEY_NAME] = dict((k, "TODO") for k in klass.API_KEY_KEYS)

        with open(klass.PROJECT_API_KEY_FILE, "wb") as f:
            json.dump(keyfile_content, f, sort_keys = True, indent=4)

    @classmethod
    def api_url(klass):
        base_url = klass.read_param_class('url')
        if base_url.endswith("xmlrpc.php"):
            return base_url
        else:
            if not base_url.endswith("/"):
                base_url = "%s/" % base_url
            return "%sxmlrpc.php" % base_url

    @classmethod
    def api(klass):
        if not hasattr(klass, "_api"):
            klass._api = xmlrpclib.ServerProxy(klass.api_url())
        return klass._api

    @classmethod
    def docmd_list_methods(klass):
        """
        List API methods exposed by WordPress API.
        """
        for method in sorted(klass.api().system.listMethods()):
            print method

    @classmethod
    def docmd_list_categories(klass):
        """
        List available blog post categories.
        """
        username = klass.read_param_class('username')
        password = klass.read_param_class('password')
        headers = ['categoryName']
        print "\t".join(headers)
        for category_info in klass.api().wp.getCategories(klass.BLOG_ID, username, password):
            print "\t".join(category_info[h] for h in headers)

    def upload_page_content(self):
        input_text = self.input().as_text()
        document_config = self.read_document_config()

        document_config['description'] = input_text
        post_id = document_config.get('postid')
        publish = document_config.get('publish', False)

        for key, value in document_config.iteritems():
            if not key == "description":
                self.log.debug("%s: %s" % (key, value))

        if post_id:
            self.api().metaWeblog.editPost(
                    post_id,
                    self.read_param('username'),
                    self.read_param('password'),
                    document_config,
                    publish
                    )
        else:
            post_id = self.api().metaWeblog.newPost(
                    self.BLOG_ID,
                    self.read_param('username'),
                    self.read_param('password'),
                    document_config,
                    publish
                    )
            document_config['postid'] = post_id

        post_info = self.api().metaWeblog.getPost(
                post_id,
                self.read_param('username'),
                self.read_param('password')
                )

        for key, value in post_info.iteritems():
            if not key == "description":
                self.log.debug("%s: %s" % (key, value))

        del document_config['description']
        document_config['publish'] = publish
        self.save_document_config(document_config)

        if publish:
            self.output().set_data(post_info['permaLink'])
        else:
            self.output().set_data(json.dumps(post_info))

    def upload_image_content(self):
        with open(self.input().storage.data_file(), 'rb') as f:
            image_base_64 = xmlrpclib.Binary(f.read())

            upload_file = {
                     'name' : self.input_filename(),
                     'type' : mimetypes.types_map[os.path.splitext(self.input_filename())[1]],
                     'bits' : image_base_64,
                     'overwrite' : 'true'
                     }

            upload_result = self.api().wp.uploadFile(
                     self.BLOG_ID,
                     self.read_param('username'),
                     self.read_param('password'),
                     upload_file
                     )

            self.log.debug("wordpress upload results: %s" % upload_result)
            url = upload_result['url']
            self.log.debug("uploaded %s to %s" % (self.artifact.key, url))

        self.output().set_data(url)

    def process(self):
        try:
            if self.input().ext in self.PAGE_CONTENT_EXTENSIONS:
                self.upload_page_content()
            else:
                self.upload_image_content()

        except xmlrpclib.Fault as e:
            raise dexy.exceptions.UserFeedback(str(e))

from dexy.filters.api import ApiFilter
import dexy.exceptions
import json
import xmlrpc.client

try:
    import mimetypes
    wp_aliases = ['wp', 'wordpress']
except UnicodeDecodeError:
    print("Unable to load mimetypes library. WordPressFilter will not work. See http://bugs.python.org/issue9291")
    mimetypes = None
    wp_aliases = []

class WordPressFilter(ApiFilter):
    """
    Posts to a WordPress blog.

    WordPress has a very confusing API setup since it implements its own API
    methods (under the wp namespace) and also supports the Blogger, metaWeblog
    and MovableType APIs. Unfortunately the wp namespace methods are
    incomplete, so you have to mix and match.

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
    aliases = wp_aliases

    _settings = {
            'blog-id' : ("The wordpress blog id.", 0),
            'page-content-extensions' : ('', ['.md', '.txt', '.html']),
            'document-api-config-file' : 'wordpress.json',
            'api-key-name' : 'wordpress',
            'output-extensions' : ['.txt']
            }

    def docmd_create_keyfile(self):
        """
        Creates a key file for WordPress in the local directory.
        """
        self.create_keyfile("project-api-key-file")

    def api_url(self):
        base_url = self.read_param('url')
        if base_url.endswith("xmlrpc.php"):
            return base_url
        else:
            if not base_url.endswith("/"):
                base_url = "%s/" % base_url
            return "%sxmlrpc.php" % base_url

    def api(klass):
        if not hasattr(klass, "_api"):
            klass._api = xmlrpc.client.ServerProxy(klass.api_url())
        return klass._api

    def docmd_list_methods(klass):
        """
        List API methods exposed by WordPress API.
        """
        for method in sorted(klass.api().system.listMethods()):
            print(method)

    def docmd_list_categories(self):
        """
        List available blog post categories.
        """
        username = self.read_param('username')
        password = self.read_param('password')
        headers = ['categoryName']
        print("\t".join(headers))
        for category_info in self.api().wp.getCategories(self.setting('blog-id'), username, password):
            print("\t".join(category_info[h] for h in headers))

    def upload_page_content(self):
        input_text = str(self.input_data)
        document_config = self.read_document_config()

        document_config['description'] = input_text
        post_id = document_config.get('postid')
        publish = document_config.get('publish', False)

        for key, value in document_config.items():
            if not key == "description":
                self.log_debug("%s: %s" % (key, value))

        if post_id:
            self.log_debug("Making editPost API call.")
            self.api().metaWeblog.editPost(
                    post_id,
                    self.read_param('username'),
                    self.read_param('password'),
                    document_config,
                    publish
                    )
        else:
            self.log_debug("Making newPost API call.")
            post_id = self.api().metaWeblog.newPost(
                    self.setting('blog-id'),
                    self.read_param('username'),
                    self.read_param('password'),
                    document_config,
                    publish
                    )
            document_config['postid'] = post_id

        self.log_debug("Making getPost API call.")
        post_info = self.api().metaWeblog.getPost(
                post_id,
                self.read_param('username'),
                self.read_param('password')
                )

        for key, value in post_info.items():
            if key in ('date_modified_gmt', 'dateCreated', 'date_modified', 'date_created_gmt',):
                post_info[key] = value.value

            if not key == "description":
                self.log_debug("%s: %s" % (key, value))

        del document_config['description']
        document_config['publish'] = publish
        self.save_document_config(document_config)

        if publish:
            self.output_data.set_data(post_info['permaLink'])
        else:
            self.output_data.set_data(json.dumps(post_info))

    def upload_image_content(self):
        with open(self.input_data.storage.data_file(), 'rb') as f:
            image_base_64 = xmlrpc.client.Binary(f.read())

            upload_file = {
                     'name' : self.work_input_filename(),
                     'type' : mimetypes.types_map[self.prev_ext],
                     'bits' : image_base_64,
                     'overwrite' : 'true'
                     }

            upload_result = self.api().wp.uploadFile(
                     self.setting('blog-id'),
                     self.read_param('username'),
                     self.read_param('password'),
                     upload_file
                     )

            self.log_debug("wordpress upload results: %s" % upload_result)
            url = upload_result['url']
            self.log_debug("uploaded %s to %s" % (self.key, url))

        self.output_data.set_data(url)

    def process(self):
        try:
            if self.prev_ext in self.setting('page-content-extensions'):
                self.upload_page_content()
            else:
                self.upload_image_content()

        except xmlrpc.client.Fault as e:
            raise dexy.exceptions.UserFeedback(str(e))

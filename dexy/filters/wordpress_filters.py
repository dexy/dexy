from dexy.filters.api_filters import ApiFilter
import mimetypes
import os
import re
import xmlrpclib

class WordPressFilter(ApiFilter):
    """
    Posts to a WordPress blog.
    """
    ALIASES = ['wp', 'wordpress']
    API_KEY_NAME = 'wordpress'
    BLOG_ID = 0
    DOCUMENT_API_CONFIG_FILE = "wordpress.json"
    DOCUMENT_API_CONFIG_FILE_KEY = "wordpress-config-file"
    OUTPUT_EXTENSIONS = ['.txt']

    @classmethod
    def api_url(klass):
        base_url = klass.read_param_class('url')
        if base_url.endswith("xmlrpc.php"):
            return base_url
        else:
            return "%s/xmlrpc.php" % base_url

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

    def process_text(self, input_text):
        if self.artifact.input_ext in self.PAGE_CONTENT_EXTENSIONS:
            document_config = self.read_document_config()
            document_config['description'] = input_text
            post_id = document_config.get('post-id')
            publish = document_config.get('publish', False)

            self.log.debug("document config is :%s" % document_config)

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
                document_config['post-id'] = post_id

            self.save_document_config(document_config)
            return input_text # Allow chaining

        else:
            # Upload image, return image url.
            with open(self.artifact.previous_artifact_filepath, 'rb') as f:
                image_base_64 = xmlrpclib.Binary(f.read())

                upload_file = {
                         'name' : os.path.basename(self.artifact.previous_canonical_filename),
                         'type' : mimetypes.types_map[self.artifact.ext],
                         'bits' : image_base_64,
                         'overwrite' : 'true'
                         }

                upload_result = self.api().wp.uploadFile(
                         self.BLOG_ID,
                         self.read_param('username'),
                         self.read_param('password'),
                         upload_file
                         )
                url = upload_result['url']
                self.log.debug("uploaded %s to %s" % (self.artifact.key, url))

            return url

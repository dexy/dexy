from dexy.filters.api_filters import ApiFilter
import json
import mimetypes
import xmlrpclib

class ConfluenceFilter(ApiFilter):
    """
    Filter for the Confluence XMLRPC API Version 1.
    """
    ALIASES = ['cfl', 'confluence']
    API_KEY_NAME = 'confluence'
    DOCUMENT_API_CONFIG_FILE = "confluence.json"
    DOCUMENT_API_CONFIG_FILE_KEY = "confluence-config-file"
    OUTPUT_EXTENSIONS = [".json"]

    # Any file extensions not in this list will be treated as binary files
    # rather than pages.
    PAGE_CONTENT_EXTENSIONS = ['.md', '.txt', '.html']

    @classmethod
    def confluence(klass):
        if not hasattr(klass, '_confluence'):
            klass._confluence = xmlrpclib.Server("%s/rpc/xmlrpc" % klass.read_url())
        return klass._confluence

    @classmethod
    def login_token(klass, forcelogin = False):
        """
        Returns login token if we already have one. Otherwise logs in and saves token.
        """
        if forcelogin or not hasattr(klass, '_login_token'):
            username = klass.read_param('username')
            password = klass.read_param('password')

            klass._login_token = klass.confluence().confluence1.login(username, password)
        return klass._login_token

    @classmethod
    def page(klass, page_id):
        """
        Get content of page.
        """
        return klass.confluence().confluence1.getPage(klass.login_token(), page_id)

    @classmethod
    def docmd_page(klass, pageid):
        print klass.page(str(pageid))

    @classmethod
    def pages(klass, spacekey):
        """
        Get list of pages in a space.
        """
        return klass.confluence().confluence1.getPages(klass.login_token(), spacekey)

    @classmethod
    def docmd_pages(klass, spacekey):
        headers = ['id', 'title']
        print "\t".join(headers)
        for page in sorted(klass.pages(spacekey), key = lambda page : page['title']):
            print "\t".join(page[h] for h in headers)

    @classmethod
    def spaces(klass):
        """
        Get list of the spaces defined in confluence.
        """
        return klass.confluence().confluence1.getSpaces(klass.login_token())

    @classmethod
    def docmd_spaces(klass):
        headers = ['name', 'key', 'url']
        print "\t".join(headers)
        for space in klass.spaces():
            print "\t".join(space[h] for h in headers)

    def process_text(self, input_text):
        document_config = self.read_document_config()
        token = self.login_token()

        if document_config.has_key('page-id'):
            page_id = document_config['page-id']
            page = self.confluence().confluence1.getPage(token, page_id)
            page['content'] = input_text
        elif document_config.has_key('space') and document_config.has_key('title'):
            spaceKey = document_config['space']
            pageTitle = document_config['title']
            try:
                page = self.confluence().confluence1.getPage(token, spaceKey, pageTitle)
            except xmlrpclib.Fault:
                self.log.debug("page %s does not exist in space %s, creating new page" % (pageTitle, spaceKey))
                page = document_config
            page['content'] = input_text

        result = self.confluence().confluence1.storePage(token, page)

        if not document_config.has_key('page-id'):
            # store page id for next time
            document_config['page-id'] = result['id']

        self.save_document_config(document_config)

        result['modified'] = str(result['modified'])
        result['created'] = str(result['created'])

        # Now upload attachments.
        for k, a in self.artifact.inputs().iteritems():
            if a.final:
                attachment_info = {
                    "fileName" : a.canonical_filename(),
                    "comment" : "Created by dexy.",
                    "contentType" : mimetypes.types_map[a.ext]
                }
                attachment_content = xmlrpclib.Binary(open(a.filepath(), "rb").read())
                attachment_result = self.confluence().confluence1.addAttachment(
                    token,
                    document_config['page-id'],
                    attachment_info,
                    attachment_content
                )
                self.log.debug(attachment_result)

        return json.dumps(result)

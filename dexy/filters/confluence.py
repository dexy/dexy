from dexy.exceptions import UserFeedback
from dexy.filter import DexyFilter
import json
import requests

class ConfluenceRESTAPI(DexyFilter):
    """
    Filter for the Confluence REST API.
    """
    aliases = ['cfl', 'confluence']

    _settings = {
            'input-extensions' : ['.html'],
            'output-extensions' : ['.json'],
            'url-base' : ("Root of URL.", None),
            'wiki-path' : ("Path to wiki root.", "/wiki"),
            'api-path' : ("Path from wiki root to API endpoint.", "/rest/api"),
            'space-key' : ("Confluence space in which to publish page.", None),
            'page-title' : ("Title of page to publish.", None),
            'page-id' : ("ID of existing Confluence page to update.", None),
            'parent-page-id' : ("Page ID to use as parent (page will be moved or created under this parent).", None),
            'parent-page-title' : ("Page title to use as parent (page will be moved or created under this parent).", None),
            'authstring' : ("base64-encoded username:password string.", "$CONFLUENCE_AUTHSTRING"),
            'username' : ("Confluence account username.", "$CONFLUENCE_USERNAME"),
            'password' : ("Confluence account password.", "$CONFLUENCE_PASSWORD")
            }

    def wiki_root_url(self):
        return "%s%s" % (self.setting('url-base'), self.setting('wiki-path'))

    def url_for_path(self, path):
        if not path.startswith("/"):
            path = "/%s" % path
        return "%s%s%s" % (self.wiki_root_url(), self.setting('api-path'), path)

    def credentials(self):
        try:
            authstring = self.setting('authstring')
        except UserFeedback:
            authstring = None

        try:
            username = self.setting('username')
            password = self.setting('password')
        except UserFeedback:
            username = None
            password = None

        if authstring is not None:
            return { "headers" : { "Authorization" : "Basic %s" % authstring }}
        elif username is not None and password is not None:
            return { "auth" : (username, password) }
        else:
            raise UserFeedback("Must provide an authstring or both username and password.")

    def credentials_with_headers(self, headers):
        credentials = self.credentials()
        if not credentials.has_key('headers'):
            credentials['headers'] = {}
        credentials['headers'].update(headers)
        return credentials

    def credentials_with_json_content_type(self):
        json_content_type = {'content-type': 'application/json'}
        return self.credentials_with_headers(json_content_type)

    def handle_response_code(self, response):
        if response.status_code in (200,):
            pass
        elif response.status_code in (401,403,):
            raise UserFeedback(response.json()['message'])
        elif response.status_code in (500,):
            raise Exception("\nServer error %s:\n%s" % (response.status_code, response.json()['message']))
        else:
            print response.text
            raise Exception("Not set up to handle status code %s" % response.status_code)

    def get_path(self, path, params=None):
        response = requests.get(
                self.url_for_path(path),
                params=params,
                **self.credentials())
        self.handle_response_code(response)
        return response.json()

    def post_file(self, path, canonical_name, filepath):
        no_check = {"X-Atlassian-Token" : "no-check"}
        with open(filepath, 'rb') as fileref:
            files = {'file': (canonical_name, fileref,) }
            response = requests.post(
                    self.url_for_path(path),
                    files=files,
                    **self.credentials_with_headers(no_check))
        self.handle_response_code(response)
        return response.json()

    def delete_path(self, path):
        response = requests.delete(
                self.url_for_path(path),
                **self.credentials())
        self.handle_response_code(response)
        return response.json()

    def json_post_path(self, path, data=None):
        response = requests.post(
                self.url_for_path(path),
                data=json.dumps(data),
                **self.credentials_with_json_content_type())
        self.handle_response_code(response)
        return response.json()

    def json_put_path(self, path, data=None):
        response = requests.put(
                self.url_for_path(path),
                data=json.dumps(data),
                **self.credentials_with_json_content_type())
        self.handle_response_code(response)
        return response.json()

    def find_page_id_by_title(self):
        space_key = self.setting('space-key')
        page_title = self.setting('page-title')

        if space_key is None:
            raise UserFeedback("A space-key must be provided.")
        if page_title is None:
            raise UserFeedback("A page-title must be provided")

        params = {"spaceKey" : space_key, "title" : page_title }
        matching_pages = self.get_path("content", params)

        if matching_pages['size'] == 1:
            matching_page = matching_pages['results'][0]
            page_id = matching_page['id']
            print "Page found using title and space key, you should set page-id parameter to %s for greater robustness." % page_id
            return page_id

        elif matching_pages['size'] == 0:
            return None

        elif matching_pages['size'] > 1:
            # TODO Is this possible?
            raise UserFeedback("multiple pages match %s" % params)

        else:
            print matching_pages
            raise Exception("should not get here")

    def create_new_page(self):
        data = {
                "type" : "page",
                "title" : self.setting('page-title'),
                "space" : {"key" : self.setting('space-key') },
                "body" : {
                    "storage" : {
                        "representation" : "storage",
                        "value" : unicode(self.input_data)
                    }
                  }
                }
        return self.json_post_path("content", data)

    def update_existing_page(self, page_id):
        page_info_args = {"expand" : "version"}
        page_info = self.get_path("content/%s" % page_id, page_info_args)
        page_version = page_info['version']['number']

        page_title = self.setting('page-title')
        if page_title is None:
            page_title = page_info['title']

        data = {
                "type" : "page",
                "title" : page_title,
                "body" : {
                    "storage" : {
                        "representation" : "storage",
                        "value" : unicode(self.input_data)
                    }
                  },
                "version" : {
                    "number" : page_version + 1
                    }
                }
        return self.json_put_path("content/%s" % page_id, data)

    def fix_attachment_paths(self, page, attachments):
        print "fixing attachment paths not yet implemented."

    def upload_attachments(self, page):
        path = "content/%s/child/attachment" % page['id']
        existing_attachments = self.get_path(path)['results']
        attachment_ids = dict(
                (att['title'], att['id'],)
                for att in existing_attachments)

        attachments = []
        for input_doc in self.doc.walk_input_docs():
            if not input_doc.output_data().is_canonical_output():
                self.log_debug("Not uploading %s, set output to True if you want it." % input_doc)
                continue

            canonical_name = input_doc.output_data().basename()
            filepath = input_doc.output_data().storage.data_file()

            if canonical_name in attachment_ids:
                update_path = "%s/%s/data" % (path, attachment_ids[canonical_name])
                attachment = self.post_file(update_path, canonical_name, filepath)
            else:
                attachment = self.post_file(path, canonical_name, filepath)

            print attachment['_links']

        self.fix_attchment_paths(page, attachments)

    def move_page_under_parent(self, page):
        parent_page_id = self.setting('parent-page-id')
        parent_page_title = self.setting('parent-page-title')

        if parent_page_id or parent_page_title:
            raise Exception("not implemented yet")

    def save_result(self, page):
        result = {}
        result['page-id'] = page['id']
        result['version'] = page['version']['number']
        result['url'] = "%s%s" % (self.wiki_root_url(), page['_links']['webui'])
        result['short-url'] = "%s%s" % (self.wiki_root_url(), page['_links']['tinyui'])
        self.output_data.set_data(json.dumps(result))

    def process(self):
        if self.setting('page-id') is not None:
            page_id = self.setting('page-id')
        else:
            page_id = self.find_page_id_by_title()

        if page_id is None:
            page = self.create_new_page()
            print "New page created. You should now set page-id parameter to %s." % page['id']
        else:
            page = self.update_existing_page(page_id)

        self.upload_attachments(page)
        self.move_page_under_parent(page)
        self.save_result(page)

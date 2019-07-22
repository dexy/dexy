from dexy.exceptions import UserFeedback
from dexy.filter import DexyFilter
import json
import mimetypes
import os
import requests

class ConfluenceRESTAPI(DexyFilter):
    """
    Filter for the Confluence REST API.
    """
    aliases = ['cfl', 'confluence']

    _settings = {
            'publish' : False,
            'input-extensions' : ['.html'],
            'output-extensions' : ['.json', '.html'],
            'url-base' : ("Root of URL.", None),
            'upload-attachments' : ("If True, attachments will automatically be uploaded. Can also be a list of file extensions.", True),
            'skip-attachments' : ("A list of file extensions which should not be uploaded as attachments.", None),
            'fix-attachment-paths' : ("If True, automatically replace attachement filenames with uploaded paths in document content.", True),
            'attachment-minor-edit' : ("Whether an attachment should be uploaded as a minor edit.", True),
            'attachment-comment' : ("Comment for attachment.", "Uploaded by Dexy confluence filter."),
            'wiki-path' : ("Path to wiki root.", "/wiki"),
            'api-path' : ("Path from wiki root to API endpoint.", "/rest/api"),
            'page-minor-edit' : ("Whether to mark page changes as a minor edit.", True),
            'space-key' : ("Confluence space in which to publish page.", None),
            'page-title' : ("Title of page to publish.", None),
            'page-id' : ("ID of existing Confluence page to update.", None),
            'parent-page-id': ("ID of page to use as parent.", None),
            'authstring' : ("base64-encoded username:password string.", "$CONFLUENCE_AUTHSTRING"),
            'username' : ("Confluence account username.", "$CONFLUENCE_USERNAME"),
            'password' : ("Confluence account password.", "$CONFLUENCE_PASSWORD"),
            'custom-mime-types' : ("Map of file extensions to mime types to supplement the python mimetypes module.", None)
            }

    def wiki_root_url(self):
        url_base = self.setting('url-base')
        if url_base is None:
            raise UserFeedback("The url-base setting must be provided.")
        if not url_base.startswith("http"):
            raise UserFeedback("The url-base setting should start with https.")
        return "%s%s" % (url_base, self.setting('wiki-path'))

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
        if 'headers' in credentials:
            credentials['headers'] = {}
        credentials['headers'].update(headers)
        return credentials

    def credentials_with_json_content_type(self):
        json_content_type = {'content-type': 'application/json'}
        return self.credentials_with_headers(json_content_type)

    def handle_response_code(self, response):
        if response.status_code < 400:
            pass
        elif response.status_code in range(400,500):
            raise UserFeedback(response.json()['message'])
        elif response.status_code in (500,):
            raise Exception("\nServer error %s:\n%s" % (response.status_code, response.json()['message']))
        else:
            print(response.text)
            raise Exception("Not set up to handle status code %s" % response.status_code)

    def get_path(self, path, params=None):
        response = requests.get(
                self.url_for_path(path),
                params=params,
                **self.credentials())
        self.handle_response_code(response)
        return response.json()

    def guess_mimetype(self, canonical_name):
        custom_mimetypes = self.setting('custom-mime-types')
        if custom_mimetypes is None:
            custom_mimetypes = {}
        ext = ".%s" % os.path.splitext(canonical_name)[1]
        if ext in custom_mimetypes:
            return custom_mimetypes[ext]
        else:
            mimetype, _ = mimetypes.guess_type(canonical_name)
            return mimetype

    def attachment_minor_edit_setting(self):
        return self.bool_setting_to_string(
                self.setting('attachment-minor-edit'))

    def page_minor_edit_setting(self):
        return self.bool_setting_to_string(
                self.setting('page-minor-edit'))

    def bool_setting_to_string(self, setting):
        if isinstance(setting, bool):
            if setting:
                return "true"
            else:
                return "false"
        else:
            return setting

    def post_file(self, path, canonical_name, filepath):
        no_check = {"X-Atlassian-Token" : "no-check"}
        mimetype = self.guess_mimetype(canonical_name)
        with open(filepath, 'rb') as fileref:
            files = {
                    'file': (canonical_name, fileref, mimetype),
                    'comment' : str(self.setting('attachment-comment')),
                    'minorEdit' : self.attachment_minor_edit_setting()
                    }
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

    def find_page_info_by_title(self, page_title=None):
        space_key = self.setting('space-key')
        if page_title is None:
            page_title = self.setting('page-title')

        if space_key is None:
            raise UserFeedback("A space-key must be provided.")
        if page_title is None:
            raise UserFeedback("A page-title must be provided")

        params = {"spaceKey" : space_key, "title" : page_title }
        matching_pages = self.get_path("content", params)

        if matching_pages['size'] == 1:
            return matching_pages['results'][0]
        elif matching_pages['size'] == 0:
            return None
        else:
            print(matching_pages)
            raise Exception("Should only be 0 or 1 matching pages.")

    def find_page_id_by_title(self, page_title=None):
        page_info = self.find_page_info_by_title(page_title)
        if page_info is not None:
            print("Page found using title and space key, you should set page-id parameter to %s for greater robustness." % page_info['id'])
            return page_info['id']

    def ancestors(self):
        if self.setting('parent-page-id') is not None:
            return [{"type" : "page", "id" : self.setting('parent-page-id')}]
        else:
            return []

    def create_new_page(self):
        data = {
                "type" : "page",
                "title" : self.setting('page-title'),
                "ancestors" : self.ancestors(),
                "space" : {"key" : self.setting('space-key') },
                "body" : {
                    "storage" : {
                        "representation" : "storage",
                        "value" : str(self.input_data)
                    }
                  }
                }
        return self.json_post_path("content", data)

    def update_existing_page(self, page_id, page_text):
        page_info_args = {"expand" : "version"}
        page_info = self.get_path("content/%s" % page_id, page_info_args)
        page_version = page_info['version']['number']

        page_title = self.setting('page-title')
        if page_title is None:
            page_title = page_info['title']

        data = {
                "type" : "page",
                "title" : page_title,
                "ancestors" : self.ancestors(),
                "body" : {
                    "storage" : {
                        "representation" : "storage",
                        "value" : page_text
                    }
                  },
                'version' : {
                    'number' : page_version + 1,
                    'minorEdit' : self.bool_setting_to_string(
                        self.setting('page-minor-edit'))
                    }
                }
        return self.json_put_path("content/%s" % page_id, data)

    def upload_attachments(self, page_id):
        path = "content/%s/child/attachment" % page_id
        existing_attachments = self.get_path(path)['results']
        attachment_ids = dict(
                (att['title'], att['id'],)
                for att in existing_attachments)

        attachments = {}

        for input_doc in self.doc.walk_input_docs():
            if not input_doc.output_data().is_canonical_output():
                self.log_debug("Not uploading %s, set output to True if you want it." % input_doc)
                continue

            canonical_name = input_doc.output_data().basename()
            ext = os.path.splitext(canonical_name)[1]

            if not isinstance(self.setting('upload-attachments'), bool):
                if not ext in self.setting('upload-attachments'):
                    self.log_info("Skipping %s because %s not in %s" % (canonical_name, ext, self.setting('upload-attachments'),))
                    continue

            if self.setting('skip-attachments') is not None:
                if ext in self.setting('skip-attachments'):
                    self.log_info("Skipping %s because %s in %s" % (canonical_name, ext, self.setting('skip-attachments'),))
                    continue

            filepath = input_doc.output_data().storage.data_file()

            if canonical_name in attachment_ids:
                update_path = "%s/%s/data" % (path, attachment_ids[canonical_name])
                attachment = self.post_file(update_path, canonical_name, filepath)
                links = attachment['_links']
            else:
                attachment = self.post_file(path, canonical_name, filepath)
                links = attachment['results'][0]['_links']

            attachments[canonical_name] = links['download'].split("?")[0]

        return attachments

    def find_page_id(self):
        if self.setting('page-id') is not None:
            return self.setting('page-id')
        else:
            return self.find_page_id_by_title()

    def save_result(self, page):
        result = {}
        result['page-id'] = page['id']
        result['version'] = page['version']['number']
        result['url'] = "%s%s" % (self.wiki_root_url(), page['_links']['webui'])
        result['short-url'] = "%s%s" % (self.wiki_root_url(), page['_links']['tinyui'])
        try:
            self.output_data.set_data(json.dumps(result))
        except Exception as e:
            self.log_debug(e)
            self.log_debug(e.__class__.__name__)
            self.log_debug(result)

    def fix_attachment_paths(self, page_id, attachments):
        input_text = str(self.input_data)
        fixed_text = input_text

        for canonical_name, path in attachments.items():
            fullpath = self.wiki_root_url() + path
            fixed_text = fixed_text.replace(canonical_name, fullpath)

        return self.update_existing_page(page_id, fixed_text)

    def process(self):
        if not self.setting('publish'):
            self.output_data.set_data(str(self.input_data))
            print("not publishing", self.setting('space-key'), self.setting('page-title'))
            return
        else:
            print("uploading", self.setting('space-key'), self.setting('page-title'))

        page_id = self.find_page_id()

        if page_id is None:
            page = self.create_new_page()
            print("New page created. You should now set page-id parameter to %s." % page['id'])
        else:
            page = self.update_existing_page(page_id, str(self.input_data))

        if self.setting('upload-attachments'):
            attachments = self.upload_attachments(page['id'])
        else:
            attachments = {}

        if attachments and self.setting('fix-attachment-paths'):
            page = self.fix_attachment_paths(page['id'], attachments)

        self.save_result(page)

from dexy.filters.api_filters import ApiFilter
from StringIO import StringIO
import sys
import json
import requests

class MediaWikiFilter(ApiFilter):
    ALIASES = ['mediawiki']
    API_KEY_NAME = 'mediawiki'
    DOCUMENT_API_CONFIG_FILE = "mediawiki.json"
    DOCUMENT_API_CONFIG_FILE_KEY = "mediawiki-config-file"
    OUTPUT_EXTENSIONS = [".txt"]

    @classmethod
    def login_token(klass, forcelogin = False):
        """
        Returns login token if we already have one. Otherwise logs in and saves token.
        """
        if forcelogin or not hasattr(klass, '_login_token'):
            payload = {
                    'action' : 'login',
                    'lgname' : klass.read_param('username'),
                    'lgpassword' : klass.read_param('password'),
                    'format' : 'json'
                    }

            # TODO persist lgtoken somewhere?

            result = requests.post(klass.read_url(), data=payload)
            result_json = json.loads(result.text)
            klass._login_token = result_json['login']['token']
            klass.cookies = result.cookies

            # Activate login by posting lgtoken along with username + password
            payload['lgtoken'] = klass._login_token
            requests.post(klass.read_url(), data=payload, cookies=klass.cookies)

        return klass._login_token

    @classmethod
    def default_params(klass):
        return {
                'lgtoken' : klass.login_token(),
                'format' : 'json'
                }

    @classmethod
    def pages(klass):
        payload = klass.default_params()
        payload['action'] = 'query'
        payload['generator'] = 'allpages'
        payload['prop'] = 'info'
        payload['intoken'] = 'edit'
        result = requests.post(klass.read_url(), cookies=klass.cookies, data=payload)
        result_json = json.loads(result.text)
        return result_json['query']['pages']

    @classmethod
    def read_page(klass, pageid):
        payload = klass.default_params()
        payload['action'] = 'query'
        payload['prop'] = 'revisions'
        payload['pageids'] = [pageid]
        payload['rvprop'] = 'content'
        payload['rvlimit'] = '1'
        result = requests.post(klass.read_url(), cookies=klass.cookies, data=payload)
        result_json = json.loads(result.text)
        return result_json['query']['pages'][str(pageid)]['revisions'][0]['*']

    @classmethod
    def find_page(klass, title):
        payload = klass.default_params()
        payload['action'] = 'query'
        payload['prop'] = 'info'
        payload['inprop'] = 'url'
        payload['titles'] = [title]
        result = requests.post(klass.read_url(), cookies=klass.cookies, data=payload)
        if hasattr(klass, 'log'):
            klass.log.debug(result.text)
        result_json = json.loads(result.text)
        num_pages = len(result_json['query']['pages'])

        if num_pages == 0:
            print "No page found for %s" % title
        elif num_pages == 1:
            return result_json['query']['pages'].values()[0]
        else:
            raise Exception("More than 1 page found with title %s" % title)

    @classmethod
    def docmd_find_page(klass, title):
        print klass.find_page(title)

    @classmethod
    def docmd_pages(klass):
        for page_id, page_info in klass.pages().iteritems():
            print "%s\t%s" % (page_id, page_info['title'])

    @classmethod
    def docmd_read(klass, pageid):
        print klass.read_page(pageid)

    def process_text(self, input_text):
        document_config = self.read_document_config()
        payload = self.default_params()

        if self.artifact.input_ext in ['.html', '.txt', '.md']:
            # Create a new page or update an existing page.
            payload['action'] = 'edit'
            payload['text'] = input_text
            payload['token'] = self.pages().values()[0]['edittoken']
            payload['title'] = document_config['title']
            result = requests.post(self.read_url(), cookies=self.cookies, data=payload)

            self.log.debug(result.text)

            page_info = self.find_page(document_config['title'])
            if not page_info:
                raise Exception("No page created for %s" % document_config['title'])
            url = page_info['fullurl']
        else:
            # Upload a binary file.
            filename = self.artifact.previous_long_canonical_filename
            self.log.debug("Uploading binary file %s" % (filename))

            payload['action'] = 'upload'
            payload['token'] = self.pages().values()[0]['edittoken']
            payload['filename'] = filename
            payload['ignorewarnings'] = True # Replace existing files of this name.
            if document_config.has_key('comment'):
                payload['comment'] = document_config['comment']

            f = open(self.artifact.previous_artifact_filepath, "rb")
            files = {'file' : (payload['filename'], f) }
            result = requests.post(self.read_url(), cookies = self.cookies, data=payload, files=files)
            f.close()

            self.log.debug(result.text)

            result_json = json.loads(result.text)
            if not result_json['upload']['result'] == 'Success':
                raise Exception("An error occurred while uploading file to mediawiki.")
            url = result_json['upload']['imageinfo']['url']
        return url

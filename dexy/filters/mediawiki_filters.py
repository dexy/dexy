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
        if forcelogin or not hasattr(klass, '_login_token'):
            payload = {
                    'action' : 'login',
                    'lgname' : klass.read_param('username'),
                    'lgpassword' : klass.read_param('password'),
                    'format' : 'json'
                    }
            result = requests.post(klass.read_url(), data=payload)
            result_json = json.loads(result.text)
            klass._login_token = result_json['login']['token']
            klass.cookies = result.cookies
            payload['lgtoken'] = klass._login_token
            print requests.post(klass.read_url(), data=payload, cookies=klass.cookies).text

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
            self.log.debug("Creating page for %s" % self.artifact.key)
            # web page content
            payload['action'] = 'edit'
            payload['text'] = input_text
            payload['token'] = self.pages().values()[0]['edittoken']
            payload['title'] = document_config['title']
            result = requests.post(self.read_url(), cookies=self.cookies, data=payload)
            print json.loads(result.text)['edit']['result']
        else:
            print "Uploading binary file for %s" % self.artifact.key
            # binary or other file
            payload['action'] = 'upload'
            payload['token'] = self.pages().values()[0]['edittoken']
            payload['filename'] = self.artifact.previous_long_canonical_filename
            payload['ignorewarnings'] = True # Replace existing files of this name.

            files = {
                    'file' : (payload['filename'], open(self.artifact.previous_artifact_filepath, "rb"))
                    }
            print "posting", payload, "to", self.read_url()
            print self.cookies
            result = requests.post(self.read_url(), cookies = self.cookies, data=payload, files=files)
            print "upload result", json.loads(result.text)

        return ""

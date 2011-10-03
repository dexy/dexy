from dexy.dexy_filter import DexyFilter
import json
import mwclient
import os

class MediaWikiFilter(DexyFilter):
    """Posts content to a MediaWiki instance"""

    MW_CONFIG_FILE = "mw-config.json"
    OUTPUT_EXTENSIONS = ['.json']
    ALIASES = ["mw"]
    MEDIA_FILE_EXTENSIONS = ['.png', '.jpg']
    INPUT_EXTENSIONS = [".txt"] + MEDIA_FILE_EXTENSIONS

    def load_mw_config(self):
        if not os.path.exists(self.MW_CONFIG_FILE):
            raise Exception("Could not find config file called %s" % self.MW_CONFIG_FILE)
        f = open(self.MW_CONFIG_FILE, "r")
        self.config = json.load(f)
        f.close()

    def process(self):
        self.load_mw_config()

        if self.config.has_key("PATH"):
            path = self.config['PATH']
        else:
            path = '/'
        site = mwclient.Site(self.config['HOST'], path)

        site.login(self.config['USERNAME'], self.config['PASSWORD'])

        if (self.artifact.input_ext in self.MEDIA_FILE_EXTENSIONS):
            # upload an image
            f = open(self.artifact.previous_artifact_filepath, 'rb')
            self.artifact.data_dict['1'] = json.dumps(site.upload(f, self.artifact.previous_canonical_filename, 'Uploaded via Dexy', ignore = True))
            f.close()
        elif (self.artifact.input_ext == '.txt'):
            page = site.Pages["/%s" % self.artifact.previous_canonical_filename]
            page.edit()
            comment = 'Uploaded via Dexy'
            result = page.save(self.artifact.input_text(), comment)
            self.artifact.data_dict['1'] = json.dumps(result)
        else:
            raise Exception("unexpected file extension %s" % self.artifact.ext)


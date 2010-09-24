try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict

from dexy.handler import DexyHandler
from dexy.logger import log
import simplejson as json

import sys
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter
from pygments.lexers import get_lexer_for_filename
class PygHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html", ".tex"]
    ALIASES = ['pyg', 'pygments']

    FORMATTERS = {
        '.html' : HtmlFormatter,
        '.latex' : LatexFormatter,
        '.tex' : LatexFormatter,
    }

### @export "pyg-handler-process-dict"
    def process_dict(self, input_dict):
        lexer = get_lexer_for_filename("file%s" % self.ext)
        formatter = self.FORMATTERS[self.artifact.ext]()
        output_dict = OrderedDict()
        for k, v in input_dict.items():
            try:
                output_dict[k] = str(highlight(v, lexer, formatter))
            except UnicodeEncodeError as e:
                log.warn("error processing section %s of file %s" % (k, self.artifact.key))
                raise e
            return output_dict
### @end

from idiopidae.runtime import Composer
import idiopidae.parser
from pygments.lexers.agile import PythonConsoleLexer
from pygments.formatters import get_formatter_for_filename
class IdioHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html", ".tex", ".txt"]
    ALIASES = ['idio', 'idiopidae']

    def process_text_to_dict(self, input_text):
        composer = Composer()
        builder = idiopidae.parser.parse('Document', input_text + "\n\0")

        name = "input_text%s" % self.ext
        if self.ext == 'pycon':
            lexer = PythonConsoleLexer
        else:
            lexer = get_lexer_for_filename(name)
        formatter = get_formatter_for_filename(self.artifact.filename(), linenos=False)
        
        output_dict = OrderedDict()

        i = -1
        for s in builder.sections:
            i += 1
            formatted_lines = composer.format(builder.statements[i]['lines'], lexer, formatter) 
            output_dict[s] = formatted_lines

        return output_dict

import os
import re
from jinja2 import Template
class JinjaHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['jinja']

    def process_text(self, input_text):
        document_data = {}
        document_data['filename'] = {}
        document_data['sections'] = {}
        document_data['a'] = {}
        
        self.artifact.load_input_artifacts()
        for k, a in self.artifact.input_artifacts_dict.items():
            common_path = os.path.dirname(os.path.commonprefix([self.artifact.doc.name, k]))
            relpath = os.path.relpath(k, common_path)
            
            if re.search("..", k):
                relpath = os.path.basename(k)
            
            if document_data['filename'].has_key(relpath):
                raise Exception("Duplicate key %s" % relpath)

            document_data['filename'][relpath] = a['fn']
            document_data['sections'][relpath] = a['data_dict']
            document_data[relpath] = a['data']
            for k, v in a['additional_inputs'].items():
                document_data['a'][k] = v
                if v.endswith('.json') and os.path.exists(v):
                    document_data[k] = json.load(open(v, "r"))
        
        template = Template(input_text)
        return str(template.render({'d' : document_data, 'a' : self.artifact}))


class WebsiteHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['ws']

    def process_text(self, input_text):
        self.artifact.load_input_artifacts()
        
        header_keys = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith("_header.html|jinja")]
        if len(header_keys) > 0:
            header_key = header_keys[0]
            header_text = self.artifact.input_artifacts_dict[header_key]['data']
        else:
            header_text = "header not found"

        footer_keys = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith("_footer.html|jinja")]
        if len(footer_keys) > 0:
            footer_key = footer_keys[0]
            footer_text = self.artifact.input_artifacts_dict[footer_key]['data']
        else:
            footer_text = "footer not found"

        return "%s %s %s" % (header_text, input_text, footer_text)


class HeadHandler(DexyHandler):
    ALIASES = ['head']
### @export "head-handler-process-text"
    def process_text(self, input_text):
        return "\n".join(input_text.split("\n")[0:10]) + "\n"


class BlogHandler(DexyHandler):
    ALIASES = None
    BLOG_CONFIG_FILE = 'blog-config.json'

    def load_blog_conf(self):
        if not os.path.exists(self.BLOG_CONFIG_FILE):
            raise Exception("Could not find config file called %s" % self.BLOG_CONFIG_FILE)
        f = open(self.BLOG_CONFIG_FILE, "r")
        self.blog_conf = json.load(f)
        f.close()
    
    def load_post_conf(self):
        self.artifact.load_input_artifacts()
        matches = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith("post.json|dexy")]
        self.k = matches[0]
        self.post_conf = json.loads(self.artifact.input_artifacts_dict[self.k]['data'])

    def process_text(self, input_text):
        self.load_blog_conf()
        self.load_post_conf()
        api = self.initialize_api()
        
        if self.post_conf.has_key('post-id'):
            post_id = self.post_conf['post-id']
            self.update_post(api, input_text, self.post_conf['post-id'])
        else:
            post_id = self.new_post(api, input_text)
            self.post_conf['post-id'] = post_id

            json_file = re.sub('\|dexy$', "", self.k)
            f = open(json_file, 'w')
            json.dump(self.post_conf, f)
            f.close()

        return "%s" % post_id

# TODO write tumblr access from scratch as e.g. saving as draft raises an error
# http://code.google.com/p/python-tumblr/
from tumblr import Api
class TumblrHandler(BlogHandler):
    ALIASES = ['tumblr']
    BLOG_CONFIG_FILE = 'tumblr-config.json'

    def initialize_api(self):
        blog = self.blog_conf['blog']
        user = self.blog_conf['user']
        password = self.blog_conf['password']
        return Api(blog, user, password)
    
    def new_post(self, api, input_text):
        title = self.post_conf.pop('title')
        post = api.write_regular(title, input_text, **self.post_conf)
        return post['post-id']
    
    def update_post(self, api, input_text, post_id):
        raise Exception("not implemented!")
        

# http://github.com/nureineide/posterous-python
import posterous
class PosterousHandler(BlogHandler):
    ALIASES = ['posterous']
    BLOG_CONFIG_FILE = 'posterous-config.json'
    
    def initialize_api(self):
        user = self.blog_conf['user']
        password = self.blog_conf['pass']
        return posterous.API(user, password)
    
    def new_post(self, api, input_text):
        post = api.new_post(title = self.post_conf['title'], body = input_text)
        return post.id

    def update_post(self, api, input_text, post_id):
        api.update_post(
            post_id = post_id,
            title = self.post_conf['title'],
            body = input_text
        )


import xmlrpclib
class WordPressHandler(BlogHandler):
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
            self.blog_conf["user"], 
            self.blog_conf["pass"], 
            self.content_dict(api, input_text), 
            self.post_conf['publish']
        )
        return post_id

    def update_post(self, api, post_id):
        api.metaWeblog.editPost(
            post_id, 
            self.blog_conf["user"], 
            self.blof_conf["pass"], 
            self.content_dict(api, input_text), 
            self.post_conf['publish']
        )

    def upload_files_and_replace_links(self, api, input_text):
        url_cache = {}

        def upload_files_to_wp(regexp, input_text):
            for t in re.findall(regexp, input_text):
                if url_cache.has_key(t[1]):
                    url = url_cache[t[1]]
                    log.info("using cached url %s %s" % (t[1], url))
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
                        self.blog_conf["user"], 
                        self.blog_conf["pass"], 
                        upload_file
                    )
                    url = upload_result['url']
                    url_cache[t[1]] = url
                    log.info("uploaded %s to %s" % (t[1], url))

                replace_string = t[0].replace(t[1], url)
                input_text = input_text.replace(t[0], replace_string)
            return input_text
        
        input_text = upload_files_to_wp('(<img src="(artifacts/.+\.(\w{2,4}))")', input_text)
        input_text = upload_files_to_wp('(<embed src="(artifacts/.+\.(\w{2,4}))")', input_text)
        input_text = upload_files_to_wp('(<audio src="(artifacts/.+\.(\w{2,4}))")', input_text)
        return input_text

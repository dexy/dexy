from dexy.handler import DexyHandler

from jinja2 import Template, Environment
import os
import re
import simplejson as json

class JinjaHelper:
  def read_file(self, filename):
    f = open(filename, "r")
    return f.read()

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
        
        if self.artifact.ext == ".tex":
            print "changing jinja tags for", self.artifact.key
            env = Environment(
                block_start_string = '<%',
                block_end_string = '%>',
                variable_start_string = '<<',
                variable_end_string = '>>',
                comment_start_string = '<#',
                comment_end_string = '#>'
                )
        else:
            env = Environment()
        template = env.from_string(input_text)
        template_hash = {
            'd' : document_data, 
            'a' : self.artifact,
            'h' : JinjaHelper()
        }
        return str(template.render(template_hash))

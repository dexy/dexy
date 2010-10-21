try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from dexy.handler import DexyHandler
from pynliner import Pynliner

class PynlinerHandler(DexyHandler):
    ALIASES = ['pynliner', 'inlinecss']

    def process_dict(self, input_dict):
        #self.artifact.load_input_artifacts()
        #print self.artifact.input_artifacts_dict.keys()
        #matches = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith(".css|dexy")]
        #k = matches[0]
        css = open("pastie.css", "r").read()
        
        output_dict = OrderedDict()
        for k, v in input_dict.items():
            p = Pynliner()
            p.from_string(v).with_cssString(css)
            output_dict[k] = p.run()
        return output_dict

from dexy.handler import DexyHandler

from pynliner import Pynliner
class PynlinerHandler(DexyHandler):
    ALIASES = ['pynliner', 'inlinecss']

    def process_text(self, input_text):
        #self.artifact.load_input_artifacts()
        #print self.artifact.input_artifacts_dict.keys()
        #matches = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith(".css|dexy")]
        #k = matches[0]
        css = open("pastie.css", "r").read()

        p = Pynliner()
        p.from_string(input_text).with_cssString(css)
        return p.run()

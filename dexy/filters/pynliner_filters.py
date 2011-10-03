from dexy.dexy_filter import DexyFilter
from ordereddict import OrderedDict
from pynliner import Pynliner

class PynlinerFilter(DexyFilter):
    """
    Move CSS inline, for posting to web without a stylesheet or for emailing.
    For now hard-coded to look for a pastie.css file in project root.
    """
    ALIASES = ['pynliner', 'inlinecss']

    def process_dict(self, input_dict):
        #matches = [k for k in self.artifact.input_artifacts_dict.keys() if k.endswith(".css|dexy")]
        #k = matches[0]
        css = open("pastie.css", "r").read()

        output_dict = OrderedDict()
        for k, v in input_dict.items():
            try:
                p = Pynliner(self.log)
            except TypeError:
                print "the pynliner filter says: please install pynliner from source (https://github.com/rennat/pynliner.git) or version > 0.2.1"
                p = Pynliner()
            p.from_string(v).with_cssString(css)
            output_dict[k] = p.run()
        return output_dict

from dexy.plugin import PluginMeta
from dexy.doc import Doc
from dexy.doc import PatternDoc

class Parser:
    """
    Parse various types of config file.
    """
    ALIASES = []

    __metaclass__ = PluginMeta

    @classmethod
    def is_active(klass):
        return True

class OriginalDexyParser(Parser):
    ALIASES = ['dexy']
    PATTERNS = [".dexy", "dexy.json"]

    def parse(self, input_text):
        info = json.loads(input_text)
        for k, v in info.iteritems():
            print "loading %s: %s" % (k, v)
        return []

from dexy.filter import DexyFilter

try:
    import pynliner
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class PynlinerFilter(DexyFilter):
    aliases = ['pyn', 'pynliner']

    def is_active(self):
        return AVAILABLE

    def process_text(self, input_text):
        return pynliner.fromString(input_text)

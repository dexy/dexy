from dexy.filter import DexyFilter

try:
    import bleach
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class Bleach(DexyFilter):
    """
    Runs the Bleach HTML sanitizer. <https://github.com/jsocol/bleach>
    """
    aliases = ['bleach']

    _settings = {
            'added-in-version' : '0.9.9.6',
            'input-extensions' : ['.html', '.txt'],
            'output-extensions' : ['.html', '.txt']
            }

    def is_active(self):
        return AVAILABLE

    # TODO implement support for sections
    def process_text(self, input_text):
        return bleach.clean(input_text)

from dexy.filter import DexyFilter
from dexy.filters.templating_plugins import TemplatePlugin

# https://pypi.python.org/pypi/ansi2html
# https://github.com/ralphbean/ansi2html

try:
    from ansi2html import Ansi2HTMLConverter
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class Ansi2HTMLTemplatePlugin(TemplatePlugin):
    aliases = ['ansi2html']

    def is_active(self):
        return AVAILABLE

    def convert(self, doc, font_size='normal'):
        conv = Ansi2HTMLConverter(inline=True, font_size=font_size)
        return conv.convert(unicode(doc), full=False)

    def run(self):
        return { 'ansi2html' : self.convert }

class Ansi2HTMLFilter(DexyFilter):
    aliases = ['ansi2html']
    _settings = {
            'output-extensions' : ['.html'],
            'input-extensions' : ['.txt'],
            'pre' : ("Whether to wrap in <pre> tags.", True),
            'font-size' : ("CSS font size to be used.", "normal")
            }

    def is_active(self):
        return AVAILABLE

    def process_text(self, input_text):
        conv = Ansi2HTMLConverter(inline=True, font_size=self.setting('font-size'))
        if self.setting('pre'):
            s = "<pre>\n%s</pre>\n"
        else:
            s = "%s\n"
        return s % conv.convert(input_text, full=False)

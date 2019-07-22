from dexy.filter import DexyFilter
from dexy.plugin import TemplatePlugin

# https://pypi.python.org/pypi/ansi2html
# https://github.com/ralphbean/ansi2html

try:
    from ansi2html import Ansi2HTMLConverter
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class Ansi2HTMLTemplatePlugin(TemplatePlugin):
    """
    Expose ansi2html within templates.
    """
    aliases = ['ansi2html']

    def is_active(self):
        return AVAILABLE

    def convert(self, doc, font_size='normal'):
        conv = Ansi2HTMLConverter(inline=True, font_size=font_size)
        return conv.convert(str(doc), full=False)

    def run(self):
        return { 'ansi2html' : ("The convert method from ansi2html module.", self.convert) }

class Ansi2HTMLFilter(DexyFilter):
    """
    Generates HTML from ANSI color codes using ansi2html.
    """
    aliases = ['ansi2html']
    _settings = {
            'output-extensions' : ['.html'],
            'input-extensions' : ['.txt', '.sh-session'],
            'data-type' : 'sectioned',
            'pre' : ("Whether to wrap in <pre> tags.", True),
            'font-size' : ("CSS font size to be used.", "normal")
            }

    def is_active(self):
        return AVAILABLE

    def process(self):
        conv = Ansi2HTMLConverter(inline=True, font_size=self.setting('font-size'))
        if self.setting('pre'):
            s = "<pre>\n%s</pre>\n"
        else:
            s = "%s\n"

        for k, v in self.input_data.items():
            self.output_data[k] = s % conv.convert(str(v), full=False)
        self.output_data.save()


from ansi2html import Ansi2HTMLConverter
from dexy.dexy_filter import DexyFilter

class Ansi2HtmlFilter(DexyFilter):
    ALIASES = ['ansi2html']
    OUTPUT_EXTENSIONS = ['.html']

    def process_text(self, input_text):
        return Ansi2HTMLConverter().convert(input_text)

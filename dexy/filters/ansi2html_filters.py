from ansi2html import Ansi2HTMLConverter
from dexy.dexy_filter import DexyFilter
from ordereddict import OrderedDict

class Ansi2HtmlFilter(DexyFilter):
    ALIASES = ['ansi2html']
    OUTPUT_EXTENSIONS = ['.html']

    @classmethod
    def docmd_css(klass):
        converter = Ansi2HTMLConverter()
        print converter.produce_headers()

    def process_dict(self, input_dict):
        converter = Ansi2HTMLConverter()

        output_dict = OrderedDict()
        for section_name, section_text in input_dict.iteritems():
            output_dict[section_name] = converter.convert(section_text, full=False)

        return output_dict

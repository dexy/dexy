from ansi2html import Ansi2HTMLConverter
from dexy.dexy_filter import DexyFilter
from ordereddict import OrderedDict

class Ansi2HtmlFilter(DexyFilter):
    ALIASES = ['ansi2html']
    OUTPUT_EXTENSIONS = ['.html']

    def process_dict(self, input_dict):
        converter = Ansi2HTMLConverter()

        output_dict = OrderedDict()
        for section_name, section_text in input_dict.iteritems():
            output_dict[section_name] = converter.convert(section_text)

        return output_dict

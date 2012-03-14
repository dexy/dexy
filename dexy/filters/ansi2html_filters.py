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
        full = self.arg_value('full', False)

        p = None
        css = None
        inline_css = self.arg_value('inline', False)
        if inline_css:
            css = "\n".join(converter.produce_headers().strip().splitlines()[1:-1])
            self.log.debug(css)
            try:
                from pynliner import Pynliner
                p = Pynliner(self.log)
            except ImportError:
                raise Exception("You must install BeautifulSoup, cssutils and pynliner in order to use 'inline' option.")

        output_dict = OrderedDict()
        for section_name, section_text in input_dict.iteritems():
            html = converter.convert(section_text, full=full)
            if inline_css:
                p.from_string(html).with_cssString(css)
                html = "<pre>\n%s</pre>" % p.run()
            output_dict[section_name] = html

        return output_dict

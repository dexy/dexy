from ansi2html import Ansi2HTMLConverter
from dexy.dexy_filter import DexyFilter
from ordereddict import OrderedDict
from dexy.commands import UserFeedback

class Ansi2HtmlFilter(DexyFilter):
    ALIASES = ['ansi2html']
    OUTPUT_EXTENSIONS = ['.html']

    @classmethod
    def docmd_css(klass):
        print klass.generate_css()

    @classmethod
    def generate_css(klass):
        converter = Ansi2HTMLConverter()
        css = converter.produce_headers()
        lines = css.strip().splitlines()
        if "<style" in lines[0]:
            return "\n".join(lines[1:-1])
        else:
            return "\n".join(lines)

    def process_dict(self, input_dict):
        converter = Ansi2HTMLConverter()
        full = self.arg_value('full', False)

        ext = self.artifact.input_ext
        if input_dict.has_key('1') and not input_dict['1'] and ext == ".css":
            # Special case if we get a virtual empty file, generate style file
            self.artifact.final = True
            self.artifact.ext = ext
            output_dict = OrderedDict()
            output_dict['1'] = self.generate_css()

        else:
            p = None
            css = None
            inline_css = self.arg_value('inline', False)
            if inline_css:
                css = "\n".join(converter.produce_headers().strip().splitlines()[1:-1])
                self.log.debug(css)
                try:
                    from pynliner import Pynliner
                except ImportError:
                    raise UserFeedback("You must install BeautifulSoup, cssutils and pynliner in order to use 'inline' option.")

            output_dict = OrderedDict()
            for section_name, section_text in input_dict.iteritems():
                html = converter.convert(section_text, full=full)
                if inline_css:
                    p = Pynliner(self.log).from_string(html).with_cssString(css)
                    html = "<pre>\n%s</pre>" % p.run()
                output_dict[section_name] = html

        return output_dict

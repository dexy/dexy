from dexy.dexy_filter import DexyFilter
from ordereddict import OrderedDict
from pygments import highlight
from pygments.formatters import get_formatter_for_filename
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers import get_lexer_for_filename
from pygments.lexers.agile import PythonConsoleLexer
from pygments.lexers.agile import RubyConsoleLexer
from pygments.lexers.text import TexLexer
from pygments.lexers.web import JavascriptLexer
from pygments.lexers.web import XmlLexer
import pygments.lexers.web

class PygmentsFilter(DexyFilter):
    """
    Apply Pygments syntax highlighting. Image formats require PIL.
    """
    INPUT_EXTENSIONS = [".*"]
    IMAGE_OUTPUT_EXTENSIONS = ['.png', '.bmp', '.gif', '.jpg']
    MARKUP_OUTPUT_EXTENSIONS = [".html", ".tex", ".svg"]
    OUTPUT_EXTENSIONS = MARKUP_OUTPUT_EXTENSIONS + IMAGE_OUTPUT_EXTENSIONS
    ALIASES = ['pyg', 'pygments']
    FINAL = False

    @classmethod
    def docmd_css(klass, style='default'):
        print klass.generate_css(style)

    @classmethod
    def docmd_sty(klass, style='default'):
        print klass.generate_sty(style)

    @classmethod
    def generate_css(self, style='default'):
        formatter = HtmlFormatter(style=style)
        return formatter.get_style_defs()

    @classmethod
    def generate_sty(self, style='default'):
        formatter = LatexFormatter(style=style)
        return formatter.get_style_defs()

    def process_dict(self, input_dict):
        ext = self.artifact.input_ext

        if input_dict.has_key('1') and not input_dict['1']:
            # Special case if we get a virtual empty file, generate style file
            self.artifact.final = True
            self.artifact.ext = ext
            output_dict = OrderedDict()
            if ext == '.css':
                output_dict['1'] = self.generate_css(self.arg_value('style', 'default'))
            elif ext == '.sty':
                output_dict['1'] = self.generate_sty(self.arg_value('style', 'default'))
            else:
                raise Exception("pyg filter doesn't know how to generate a stylesheet for %s extension" % ext)
            return output_dict
        else:
            args = self.args().copy()

            if args.has_key('lexer'):
                self.log.debug("custom lexer alias %s specified" % args['lexer'])
                lexer = get_lexer_by_name(args['lexer'])
                del args['lexer']
            else:
                if ext == '.pycon':
                    lexer = PythonConsoleLexer()
                elif ext == '.rbcon':
                    lexer = RubyConsoleLexer()
                elif (ext in ('.json', '.dexy') or self.artifact.name.endswith(".dexy")) and (pygments.__version__ < '1.5'):
                    lexer = JavascriptLexer()
                elif ext in ('.dexy') or self.artifact.name.endswith(".dexy"):
                    # JSON lexer available in pygments 1.5
                    lexer = pygments.lexers.web.JSONLexer()
                elif ext == '.Rd':
                    lexer = TexLexer() # does a passable job
                elif ext == '.svg':
                    lexer = XmlLexer()
                else:
                    fake_file_name = "input_text%s" % ext
                    lexer = get_lexer_for_filename(fake_file_name)

            formatter_args = {'lineanchors' : self.artifact.web_safe_document_key() }

            # all args left are for the formatter...
            formatter_args.update(args)

            formatter = get_formatter_for_filename(self.artifact.filename(),
                    **formatter_args)

            # TODO whitelist acceptable formatter args
            # TODO allow passing lexer args?

            if self.artifact.ext in self.IMAGE_OUTPUT_EXTENSIONS:
                self.artifact.binary_output = True
                # TODO set to final
                with open(self.artifact.filepath(), 'wb') as f:
                    f.write(highlight(self.artifact.input_text(), lexer, formatter))
            else:
                output_dict = OrderedDict()
                for k, v in input_dict.items():
                    # TODO figure out where these characters are coming from and don't hard-code this.
                    v = v.replace(" \x08", "").replace(chr(13), "")
                    self.log.debug("Using lexer %s" % lexer.__class__.__name__)
                    output_dict[k] = highlight(v, lexer, formatter)
                return output_dict

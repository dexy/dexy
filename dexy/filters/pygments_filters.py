from dexy.dexy_filter import DexyFilter
from ordereddict import OrderedDict
from pygments import highlight
from pygments.formatters import get_formatter_for_filename
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

    def process_dict(self, input_dict):
        ext = self.artifact.input_ext
        has_args = self.artifact.args.has_key('pygments')
        if has_args:
            args = self.artifact.args['pygments']
        else:
            args = {}

        if args.has_key('lexer'):
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
        ### @end
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
                output_dict[k] = highlight(v, lexer, formatter)
            return output_dict

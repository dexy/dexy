from dexy.handler import DexyHandler
from idiopidae.runtime import Composer
from ordereddict import OrderedDict
from pygments.formatters import get_formatter_for_filename
from pygments.lexers import get_lexer_for_filename
from pygments.lexers import get_lexer_by_name
from pygments.lexers.agile import PythonConsoleLexer
from pygments.lexers.agile import RubyConsoleLexer
from pygments.lexers.web import JavascriptLexer
from pygments.lexers.web import PhpLexer
import idiopidae.parser

class IdioHandler(DexyHandler):
    """
    Apply idiopidae to split document into sections at ### @export
    "section-name" comments.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html", ".tex", ".txt"]
    ALIASES = ['idio', 'idiopidae']

    def process_text_to_dict(self, input_text):
        composer = Composer()
        builder = idiopidae.parser.parse('Document', input_text + "\n\0")

        ext = self.artifact.input_ext
        name = "input_text%s" % ext

        if self.doc.args.has_key('pyg-lexer'):
            lexer = get_lexer_by_name(self.doc.args['pyg-lexer'])
        elif ext == '.pycon':
            lexer = PythonConsoleLexer()
        elif ext == '.rbcon':
            lexer = RubyConsoleLexer()
        elif ext in ('.json', '.dexy'):
            lexer = JavascriptLexer()
        elif ext in ('.php'):
            # If we are using idio, then our code will be in sections so we
            # need to start inline with PHP. To avoid this, use pyg instead of
            # idio. (Eventually should be able to specify lexer + options in config.)
            lexer = PhpLexer(startinline=True)
        else:
            lexer = get_lexer_for_filename(name)

        formatter = get_formatter_for_filename(self.artifact.filename(),
                lineanchors='l')
        output_dict = OrderedDict()

        for i, s in enumerate(builder.sections):
            lines = builder.statements[i]['lines']
            formatted_lines = composer.format(lines, lexer, formatter) 
            output_dict[s] = formatted_lines

        return output_dict

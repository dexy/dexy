from dexy.handler import DexyHandler
from idiopidae.runtime import Composer
from ordereddict import OrderedDict
from pygments.formatters import get_formatter_for_filename
from pygments.lexers import get_lexer_for_filename
from pygments.lexers.agile import PythonConsoleLexer
from pygments.lexers.agile import RubyConsoleLexer
from pygments.lexers.web import JavascriptLexer
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
        # List any file extensions which don't map neatly to lexers.
        if ext == '.pycon':
            lexer = PythonConsoleLexer()
        elif ext == '.rbcon':
            lexer = RubyConsoleLexer()
        elif ext in ('.json', '.dexy'):
            lexer = JavascriptLexer()
        else:
            lexer = get_lexer_for_filename(name)
        formatter = get_formatter_for_filename(self.artifact.filename(), linenos=False)
        output_dict = OrderedDict()

        for i, s in enumerate(builder.sections):
            lines = builder.statements[i]['lines']
            formatted_lines = composer.format(lines, lexer, formatter) 
            output_dict[s] = formatted_lines

        return output_dict

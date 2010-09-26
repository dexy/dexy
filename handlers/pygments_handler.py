from dexy.handler import DexyHandler
from dexy.logger import log

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from idiopidae.runtime import Composer
from pygments import highlight
from pygments.formatters import get_formatter_for_filename
from pygments.lexers import get_lexer_for_filename
from pygments.lexers.agile import PythonConsoleLexer
import idiopidae.parser

class PygHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html", ".tex"]
    ALIASES = ['pyg', 'pygments']

    def process_dict(self, input_dict):
        name = "input_text%s" % self.ext
        if self.ext == 'pycon':
            lexer = PythonConsoleLexer
        else:
            lexer = get_lexer_for_filename(name)
        formatter = get_formatter_for_filename(self.artifact.filename(), linenos=False)
        output_dict = OrderedDict()
        for k, v in input_dict.items():
            try:
                output_dict[k] = str(highlight(v, lexer, formatter))
            except UnicodeEncodeError as e:
                log.warn("error processing section %s of file %s" % (k, self.artifact.key))
                raise e
            return output_dict

class IdioHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html", ".tex", ".txt"]
    ALIASES = ['idio', 'idiopidae']

    def process_text_to_dict(self, input_text):
        composer = Composer()
        builder = idiopidae.parser.parse('Document', input_text + "\n\0")

        name = "input_text%s" % self.ext
        if self.ext == 'pycon':
            lexer = PythonConsoleLexer
        else:
            lexer = get_lexer_for_filename(name)
        formatter = get_formatter_for_filename(self.artifact.filename(), linenos=False)
        
        output_dict = OrderedDict()

        i = -1
        for s in builder.sections:
            i += 1
            formatted_lines = composer.format(builder.statements[i]['lines'], lexer, formatter) 
            output_dict[s] = formatted_lines

        return output_dict

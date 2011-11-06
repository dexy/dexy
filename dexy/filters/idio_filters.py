from dexy.dexy_filter import DexyFilter
from idiopidae.runtime import Composer
from ordereddict import OrderedDict
from pygments.formatters import get_formatter_for_filename
from pygments.lexers import get_lexer_by_name
from pygments.lexers import get_lexer_for_filename
from pygments.lexers.agile import PythonConsoleLexer
from pygments.lexers.agile import RubyConsoleLexer
from pygments.lexers.web import JavascriptLexer
from pygments.lexers.web import PhpLexer
import idiopidae.parser
import re

class IdioFilter(DexyFilter):
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

        if self.artifact.args.has_key('pyg-lexer'):
            lexer = get_lexer_by_name(self.artifact.args['pyg-lexer'])
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

        if self.artifact.args.has_key('idio'):
            idio_args = self.artifact.args['idio']
        elif self.artifact.args.has_key('pygments'):
            idio_args = self.artifact.args['pygments']
        else:
            idio_args = {}

        formatter_args = {'lineanchors' : self.artifact.web_safe_document_key() }
        formatter_args.update(idio_args)

        formatter = get_formatter_for_filename(self.artifact.filename(),
            **formatter_args)

        output_dict = OrderedDict()
        lineno = 1

        for i, s in enumerate(builder.sections):
            lines = builder.statements[i]['lines']
            if len(lines) == 0:
                next
            if not re.match("^\d+$", s):
                # Manually named section, the sectioning comment takes up a
                # line, so account for this to keep line nos in sync.
                lineno += 1
            formatter.linenostart = lineno
            formatted_lines = composer.format(lines, lexer, formatter)
            output_dict[s] = formatted_lines
            lineno += len(lines)

        return output_dict

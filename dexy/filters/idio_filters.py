from dexy.filters.pygments_filters import PygmentsFilter
from idiopidae.runtime import Composer
from ordereddict import OrderedDict
import idiopidae.parser
import re

class IdioFilter(PygmentsFilter):
    """
    Apply idiopidae to split document into sections at ### @export
    "section-name" comments.
    """
    ALIASES = ['idio', 'idiopidae']
    OUTPUT_EXTENSIONS = PygmentsFilter.MARKUP_OUTPUT_EXTENSIONS + PygmentsFilter.IMAGE_OUTPUT_EXTENSIONS + [".txt"]

    def process_text_to_dict(self, input_text):
        composer = Composer()
        builder = idiopidae.parser.parse('Document', input_text + "\n\0")

        args = self.args().copy()
        lexer = self.create_lexer_instance(args)
        formatter = self.create_formatter_instance(args)

        output_dict = OrderedDict()
        lineno = 1

        for i, s in enumerate(builder.sections):
            self.log.debug("In section no. %s name %s" % (i, s))
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

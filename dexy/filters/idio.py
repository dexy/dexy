from dexy.common import OrderedDict
from dexy.filters.pyg import PygmentsFilter
from idiopidae.runtime import Composer
from idiopidae.parser import IdiopidaeParser, IdiopidaeParserScanner
from pygments.formatters import get_all_formatters
import dexy.exceptions
import idiopidae.parser
import json
import re
import zapps.rt

class IdioFilter(PygmentsFilter):
    """
    Apply idiopidae to split document into sections at ### @export
    "section-name" comments.
    """
    aliases = ['idio', 'idiopidae']
    _settings = {
            'output-extensions' : PygmentsFilter.MARKUP_OUTPUT_EXTENSIONS + PygmentsFilter.IMAGE_OUTPUT_EXTENSIONS + [".txt"]
            }

    def data_class_alias(klass, file_ext):
        if file_ext in PygmentsFilter.MARKUP_OUTPUT_EXTENSIONS + [".txt"]:
            return 'sectioned'
        else:
            return 'generic'

    def do_add_new_files(self):
        if self.setting('add-new-files'):
            return True
        elif self.ext in self.IMAGE_OUTPUT_EXTENSIONS:
            return True
        else:
            return False

    def process(self):
        lexer = self.create_lexer_instance()

        try:
            input_text = self.input_data.as_text()
        except UnicodeDecodeError:
            input_text = 'not printable'

        composer = Composer()

        try:
            P = IdiopidaeParser(IdiopidaeParserScanner(input_text + "\n\0"))
            builder = P.Document()
        except zapps.rt.SyntaxError as s:
            zapps_err = zapps.rt.print_error(input_text + "\n\0", s, P._scanner, False)
            msg = "Idiopidae was unable to parse input for %s\n%s" % (self.key, zapps_err)
            raise dexy.exceptions.UserFeedback(msg)
        except zapps.rt.NoMoreTokens as s:
            msg = "Could not complete parsing; stopped around here:%s" % P._scanner
            raise dexy.exceptions.UserFeedback(msg)

        output_dict = OrderedDict()
        all_lines = []
        lineno = 1

        add_new_files = self.do_add_new_files()

        for i, s in enumerate(builder.sections):
            self.log_debug("In section no. %s name %s" % (i, s))
            lines = builder.statements[i]['lines']
            all_lines.extend(lines)

            if len(lines) == 0:
                next
            if not re.match("^\d+$", s):
                # Manually named section, the sectioning comment takes up a
                # line, so account for this to keep line nos in sync.
                lineno += 1

            formatter = self.create_formatter_instance()

            if hasattr(formatter, 'linenostart'):
                formatter.linenostart = lineno
            elif hasattr(formatter, 'line_number_start'):
                formatter.line_number_start = lineno

            formatted_lines = composer.format(lines, lexer, formatter)

            if add_new_files:
                new_doc_name = "%s--%s%s" % (self.doc.key.replace("|", "--"), s, self.ext)
                self.add_doc(new_doc_name, formatted_lines)

            if not self.ext in self.IMAGE_OUTPUT_EXTENSIONS:
                if add_new_files:
                    self.update_all_args({'output' : False })
                output_dict[s] = formatted_lines

            lineno += len(lines)

        if self.ext in self.IMAGE_OUTPUT_EXTENSIONS:
            formatter = self.create_formatter_instance()
            formatted_lines = composer.format(lines, lexer, formatter)
            self.output_data.set_data(formatted_lines)
        else:
            self.output_data.set_data(output_dict)

class IdioMultipleFormatsFilter(PygmentsFilter):
    """
    Apply idiopidae to split document into sections at ### @export
    "section-name" comments, then apply syntax highlighting for all available
    text-based formats.
    """
    aliases = ['idiom']
    _settings = {
            'output-extensions' : ['.json']
            }

    def process(self):
        input_text = self.input_data.as_text()
        composer = Composer()
        builder = idiopidae.parser.parse('Document', input_text + "\n\0")

        lexer = self.create_lexer_instance()

        formatters = []
        for formatter_class in get_all_formatters():
            formatter_args = self.constructor_args('formatter')
            formatter_instance = formatter_class(**formatter_args)
            formatters.append(formatter_instance)

        output_dict = OrderedDict()
        lineno = 1

        for i, s in enumerate(builder.sections):
            self.log_debug("In section no. %s name %s" % (i, s))
            lines = builder.statements[i]['lines']
            if len(lines) == 0:
                next
            if not re.match("^\d+$", s):
                # Manually named section, the sectioning comment takes up a
                # line, so account for this to keep line nos in sync.
                lineno += 1

            output_dict[s] = {}
            for formatter in formatters:
                formatter.linenostart = lineno
                formatted_lines = composer.format(lines, lexer, formatter)

                for filename in formatter.filenames:
                    ext = filename.lstrip("*")
                    if not ext in self.IMAGE_OUTPUT_EXTENSIONS:
                        output_dict[s][ext] = formatted_lines

            lineno += len(lines)

        self.output_data.set_data(json.dumps(output_dict))

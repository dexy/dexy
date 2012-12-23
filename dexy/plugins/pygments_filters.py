from dexy.common import OrderedDict
from dexy.filter import DexyFilter
from dexy.plugins.standard_filters import StartSpaceFilter
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter
from pygments.formatters import get_formatter_for_filename
from pygments.lexers import get_lexer_by_name
from pygments.lexers import get_lexer_for_filename
from pygments.lexers.agile import PythonConsoleLexer
from pygments.lexers.agile import RubyConsoleLexer
from pygments.lexers.templates import DjangoLexer
from pygments.lexers.text import MakefileLexer
from pygments.lexers.text import TexLexer
from pygments.lexers.web import JavascriptLexer
from pygments.lexers.web import XmlLexer
import dexy.commands
import dexy.exceptions
import pygments.lexers.web
import re

class SyntaxHighlightRstFilter(DexyFilter):
    """
    Surrounds code with highlighting instructions for ReST
    """
    ALIASES = ['pyg4rst']

    def process_dict(self, input_dict):
        n = self.args().get('n', 2)
        result = OrderedDict()

        try:
            lexer = get_lexer_for_filename(self.input().storage.data_file())
        except pygments.util.ClassNotFound:
            msg = PygmentsFilter.LEXER_ERR_MSG
            raise dexy.exceptions.UserFeedback(msg % (self.input().name, self.artifact.key))

        lexer_alias = lexer.aliases[0]

        for section_name, section_text in input_dict.iteritems():
            with_spaces = StartSpaceFilter.add_spaces_at_start(section_text, n)
            result[section_name] = ".. code:: %s\n\n%s" % (lexer_alias, with_spaces)

        return result

class PygmentsFilter(DexyFilter):
    """
    Apply Pygments syntax highlighting. Image formats require PIL.
    """
    INPUT_EXTENSIONS = [".*"]
    IMAGE_OUTPUT_EXTENSIONS = ['.png', '.bmp', '.gif', '.jpg']
    MARKUP_OUTPUT_EXTENSIONS = [".html", ".tex", ".svg"] # make sure .html is first!
    OUTPUT_EXTENSIONS = MARKUP_OUTPUT_EXTENSIONS + IMAGE_OUTPUT_EXTENSIONS + ['.css', '.sty']
    ALIASES = ['pyg', 'pygments']
    FRAGMENT = True
    LEXER_ERR_MSG = "Pygments doesn't know how to syntax highlight files like '%s' (for '%s'). Either it can't be done or you need to specify the lexer manually."

    @classmethod
    def data_class_alias(klass, file_ext):
        if file_ext in klass.MARKUP_OUTPUT_EXTENSIONS:
            return 'sectioned'
        else:
            return 'generic'

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

    def calculate_canonical_name(self):
        ext = self.artifact.prior.ext
        if ext in [".css", ".sty"] and self.artifact.ext == ext:
            return self.artifact.doc.name
        else:
            return "%s%s" % (self.artifact.doc.name, self.artifact.ext)

    def create_lexer_instance(self, args):
        ext = self.artifact.prior.ext
        lexer = None
        lexer_args = {}

        # Pick out any options which are prefixed with "lexer-"
        for k in args.keys():
            m = re.match("^lexer-(.+)$", k)
            if m:
                option_name = m.groups()[0]
                option_value = args[k]
                self.log.debug("using custom lexer option for %s with value %s" % (option_name, option_value))
                del args[k]
                lexer_args[option_name] = option_value

        # Create a lexer instance.
        if args.has_key('lexer'):
            self.log.debug("custom lexer alias %s specified" % args['lexer'])
            lexer = get_lexer_by_name(args['lexer'], **lexer_args)
            del args['lexer']
        else:
            is_json_file = ext in ('.json', '.dexy') or self.output().name.endswith(".dexy")
            if ext == '.pycon':
                lexer_class = PythonConsoleLexer
            elif ext == '.rbcon':
                lexer_class = RubyConsoleLexer
            elif is_json_file and (pygments.__version__ < '1.5'):
                lexer_class = JavascriptLexer
            elif is_json_file:
                lexer_class = pygments.lexers.web.JSONLexer
            elif ext == '.Rd':
                lexer_class = TexLexer # does a passable job
            elif ext == '.svg':
                lexer_class = XmlLexer
            elif ext == '.jinja':
                lexer_class = DjangoLexer
            elif ext == '.Makefile' or (ext == '' and 'Makefile' in self.input().name):
                lexer_class = MakefileLexer
            else:
                fake_file_name = "input_text%s" % ext
                try:
                    lexer = get_lexer_for_filename(fake_file_name, **lexer_args)
                except pygments.util.ClassNotFound:
                    raise dexy.exceptions.UserFeedback(self.LEXER_ERR_MSG % (self.input().name, self.artifact.key))

            if not lexer:
                lexer = lexer_class(**lexer_args)

        self.log.debug("using lexer %s" % lexer.__class__.__name__)
        return lexer

    def create_formatter_instance(self, args):
        formatter_args = {'lineanchors' : self.output().web_safe_document_key() }

        # Python 2.6 doesn't like unicode keys as kwargs
        for k, v in args.iteritems():
            formatter_args[str(k)] = v

        self.log.debug("creating pygments formatter with args %s" % (formatter_args))
        return get_formatter_for_filename(self.output().name, **formatter_args)

    def process(self):
        if self.artifact.ext in self.IMAGE_OUTPUT_EXTENSIONS:
            try:
                import PIL
            except ImportError:
                print "python imaging library is required by pygments to create image output"
                raise dexy.exceptions.InactiveFilter('pyg', self.artifact.key)


        ext = self.artifact.prior.ext
        if ext in [".css", ".sty"] and self.artifact.ext == ext:
            self.log.debug("creating a style file in %s" % self.artifact.key)
            # Special case if we get a virtual empty file, generate style file
            if ext == '.css':
                output = self.generate_css(self.arg_value('style', 'default'))
            elif ext == '.sty':
                output = self.generate_sty(self.arg_value('style', 'default'))
            else:
                raise dexy.commands.UserFeedback("pyg filter doesn't know how to generate a stylesheet for %s extension" % ext)

            self.output().set_data(output)

        else:
            args = self.args().copy()
            lexer = self.create_lexer_instance(args)

            formatter_args = {'lineanchors' : self.output().web_safe_document_key() }

            # Python 2.6 hates unicode keys
            for k, v in args.iteritems():
                formatter_args[str(k)] = v

            if self.artifact.ext in self.IMAGE_OUTPUT_EXTENSIONS:
                # Place each section into an image.
                for k, v in self.input().as_sectioned().iteritems():
                    formatter = get_formatter_for_filename(self.output().name, **formatter_args)
                    output_for_section = highlight(v.decode("utf-8"), lexer, formatter)
                    new_doc_name = "%s--%s%s" % (self.artifact.doc.key.replace("|", "--"), k, self.artifact.ext)
                    self.add_doc(new_doc_name, output_for_section)

                # Place entire contents into main file.
                formatter = get_formatter_for_filename(self.output().name, **formatter_args)
                self.artifact.doc.canon = True
                with open(self.output_filepath(), 'wb') as f:
                    f.write(highlight(self.input().as_text(), lexer, formatter))

            else:
                formatter = get_formatter_for_filename(self.output().name, **formatter_args)
                output_dict = OrderedDict()
                for k, v in self.input().as_sectioned().iteritems():
                    output_dict[k] = highlight(v.decode("utf-8"), lexer, formatter)
                self.output().set_data(output_dict)

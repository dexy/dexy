from dexy.common import OrderedDict
from dexy.filter import DexyFilter
from dexy.filters.standard import StartSpaceFilter
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter
from pygments.formatters import get_formatter_for_filename
from pygments.lexers import get_lexer_by_name
from pygments.lexers import get_lexer_for_filename
from pygments.lexers.agile import PythonConsoleLexer
from pygments.lexers.agile import RubyConsoleLexer
from pygments.lexers.special import TextLexer
from pygments.lexers.templates import DjangoLexer
from pygments.lexers.text import MakefileLexer
from pygments.lexers.text import TexLexer
from pygments.lexers.web import JavascriptLexer
from pygments.lexers.web import XmlLexer
import dexy.commands
import dexy.exceptions
import pygments.lexers.web

class SyntaxHighlightRstFilter(DexyFilter):
    """
    Surrounds code with highlighting instructions for ReST
    """
    aliases = ['pyg4rst']
    _settings = {
            'n' : ("Number of chars to indent.", 2)
            }

    def process_dict(self, input_dict):
        n = self.setting('n')
        result = OrderedDict()

        try:
            lexer = get_lexer_for_filename(self.input_data.storage.data_file())
        except pygments.util.ClassNotFound:
            msg = PygmentsFilter.LEXER_ERR_MSG
            raise dexy.exceptions.UserFeedback(msg % (self.input_data.name, self.key))

        lexer_alias = lexer.aliases[0]

        for section_name, section_text in input_dict.iteritems():
            with_spaces = StartSpaceFilter.add_spaces_at_start(section_text, n)
            result[section_name] = ".. code:: %s\n\n%s" % (lexer_alias, with_spaces)

        return result

class PygmentsFilter(DexyFilter):
    """
    Apply Pygments syntax highlighting. Image formats require PIL.
    """
    aliases = ['pyg', 'pygments']
    IMAGE_OUTPUT_EXTENSIONS = ['.png', '.bmp', '.gif', '.jpg']
    MARKUP_OUTPUT_EXTENSIONS = [".html", ".tex", ".svg"] # make sure .html is first so it is default output format
    LEXER_ERR_MSG = """Pygments doesn't know how to syntax highlight files like '%s' (for '%s').\
    You might need to specify the lexer manually."""

    _settings = {
            'input-extensions' : [".*"],
            'output-extensions' : MARKUP_OUTPUT_EXTENSIONS + IMAGE_OUTPUT_EXTENSIONS + ['.css', '.sty'],

            'lexer' : ("""The name of the pygments lexer to use (will normally
            be determined automatically, only use this if you need to override
            the default setting or your filename isn't mapped to the lexer you
            want to use.""", None),
            'allow-unknown-ext' : ("""Whether to allow unknown file extensions
                to be parsed with the TextLexer by default instead of raising
                an exception.""", True),
            'allow-unprintable-input' : ("""Whether to allow unprintable input
                to be replaced with dummy text instead of raising an exception.""",
                True),
            'unprintable-input-text' : ("""Dummy text to use instead of
                unprintable binary input.""", 'not printable'),
            'lexer-settings' : (
                "List of all settings which will be passed to the lexer constructor.",
                []
            ),

            'formatter-settings' : (
                """List of all settings which will be passed to the formatter
                constructor.""", ['style', 'full', 'linenos']
            ),

            'style' : ( "Formatter style to output.", 'default'),
            'full' : ("""Pygments formatter option: output a 'full' document
                including header/footer tags.""", None),
            'linenos' : ("""Whether to include line numbers. May be set to
                'table' or 'inline'.""", None),
            }

    def data_class_alias(klass, file_ext):
        if file_ext in klass.MARKUP_OUTPUT_EXTENSIONS:
            return 'sectioned'
        else:
            return 'generic'

    def docmd_css(klass, style='default'):
        """
        Prints out CSS for the specified style.
        """
        print klass.generate_css(style)

    def docmd_sty(klass, style='default'):
        """
        Prints out .sty file (latex) for the specified style.
        """
        print klass.generate_sty(style)

    def generate_css(self, style='default'):
        formatter = HtmlFormatter(style=style)
        return formatter.get_style_defs()

    def generate_sty(self, style='default'):
        formatter = LatexFormatter(style=style)
        return formatter.get_style_defs()

    def calculate_canonical_name(self):
        ext = self.prev_ext
        if ext in [".css", ".sty"] and self.ext == ext:
            return self.doc.name
        else:
            return "%s%s" % (self.doc.name, self.ext)

    def constructor_args(self, constructor_type, custom_args=None):
        if custom_args:
            args = custom_args
        else:
            args = {}

        for argname in self.setting("%s-settings" % constructor_type):
            if self.setting(argname):
                args[argname] = self.setting(argname)
        return args

    def create_lexer_instance(self):
        ext = self.prev_ext
        lexer_args = self.constructor_args('lexer')
        lexer = None

        # Create a lexer instance.
        if self.setting('lexer'):
            self.log_debug("custom lexer %s specified" % self.setting('lexer'))
            lexer = get_lexer_by_name(self.setting('lexer'), **lexer_args)
        else:
            is_json_file = ext in ('.json', '.dexy') or self.output_data.name.endswith(".dexy")
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
            elif ext == '.Makefile' or (ext == '' and 'Makefile' in self.input_data.name):
                lexer_class = MakefileLexer
            else:
                fake_file_name = "input_text%s" % ext
                try:
                    lexer = get_lexer_for_filename(fake_file_name, **lexer_args)

                except pygments.util.ClassNotFound:
                    msg = self.LEXER_ERR_MSG
                    msgargs = (self.input_data.name, self.key)

                    if self.setting('allow-unknown-ext'):
                        self.log_warn(msg % msgargs)
                        lexer_class = TextLexer
                    else:
                        raise dexy.exceptions.UserFeedback(msg % msgargs)

            if not lexer:
                lexer = lexer_class(**lexer_args)

        self.log_debug("using pygments lexer %s with args %s" % (lexer.__class__.__name__, lexer_args))
        return lexer

    def create_formatter_instance(self):
        formatter_args = self.constructor_args('formatter', {
            'lineanchors' : self.output_data.web_safe_document_key() })
        self.log_debug("creating pygments formatter with args %s" % (formatter_args))
        return get_formatter_for_filename(self.output_data.name, **formatter_args)

    def process(self):
        if self.ext in self.IMAGE_OUTPUT_EXTENSIONS:
            try:
                import PIL
            except ImportError:
                print "python imaging library is required by pygments to create image output"
                raise dexy.exceptions.InactiveFilter('pyg')

        ext = self.prev_ext
        if ext in [".css", ".sty"] and self.ext == ext:
            # Special case if we get a virtual empty file, generate style file

            self.log_debug("creating a style file in %s" % self.key)
            if ext == '.css':
                output = self.generate_css(self.setting('style'))
            elif ext == '.sty':
                output = self.generate_sty(self.setting('style'))
            else:
                msg = "pyg filter doesn't know how to generate a stylesheet for %s extension"
                msgargs = (ext)
                raise dexy.commands.UserFeedback(msg % msgargs)

            self.output_data.set_data(output)
            self.add_runtime_args({'include-in-workspaces' : True })

        else:
            lexer = self.create_lexer_instance()

            if self.ext in self.IMAGE_OUTPUT_EXTENSIONS:
                # Place each section into an image.
                for k, v in self.input_data.as_sectioned().iteritems():
                    formatter = self.create_formatter_instance()
                    output_for_section = highlight(v.decode("utf-8"), lexer, formatter)
                    new_doc_name = "%s--%s%s" % (self.doc.key.replace("|", "--"), k, self.ext)
                    self.add_doc(new_doc_name, output_for_section)

                # Place entire contents into main file.
                formatter = self.create_formatter_instance()
                self.update_all_args({'output' : False })
                with open(self.output_filepath(), 'wb') as f:
                    f.write(highlight(self.input_data.as_text(), lexer, formatter))

            else:
                formatter = self.create_formatter_instance()
                output_dict = OrderedDict()
                for k, v in self.input_data.as_sectioned().iteritems():
                    try:
                        output_dict[k] = highlight(v.decode("utf-8"), lexer, formatter)
                    except UnicodeDecodeError:
                        if self.setting('allow-unprintable-input'):
                            input_text = self.setting('unprintable-input-text')
                            output_dict[k] = highlight(input_text, lexer, formatter)
                        else:
                            raise
                self.output_data.set_data(output_dict)

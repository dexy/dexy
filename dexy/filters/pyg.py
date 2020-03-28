from dexy.filter import DexyFilter
from dexy.utils import indent
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter
from pygments.formatters import get_formatter_for_filename
from pygments.lexers import LEXERS as PYGMENTS_LEXERS
from pygments.lexers import get_lexer_by_name
import dexy.commands
import dexy.exceptions
import posixpath
import pygments.lexers.web

pygments_lexer_cache = {}

file_ext_to_lexer_alias_cache = {
        '.pycon' : 'pycon',
        '.rbcon' : 'rbcon',
        '.Rd' : 'latex',
        '.svg' : 'xml',
        '.jinja' : 'jinja'
        }

# Add all pygments standard mappings.
for module_name, name, aliases, file_extensions, _ in list(PYGMENTS_LEXERS.values()):
    alias = aliases[0]
    for ext in file_extensions:
        ext = ext.lstrip("*")
        file_ext_to_lexer_alias_cache[ext] = alias

class SyntaxHighlightRstFilter(DexyFilter):
    """
    Surrounds code with highlighting instructions for ReST
    """
    aliases = ['pyg4rst']
    _settings = {
            'n' : ("Number of chars to indent.", 2),
            'data-type' : 'sectioned'
            }

    def process(self):
        n = self.setting('n')
        lexer_alias = file_ext_to_lexer_alias_cache[self.input_data.ext]

        for section_name, section_input in self.input_data.items():
            with_spaces = indent(section_input, n)
            section_output = ".. code:: %s\n\n%s" % (lexer_alias, with_spaces)
            self.output_data[section_name] = section_output

        self.output_data.save()

class SyntaxHighlightAsciidoctor(DexyFilter):
    """
    Surrounds code with highlighting instructions for Asciidoctor
    """
    aliases = ['asciisyn']
    _settings = {
            'lexer' : ("Specify lexer if can't be detected fro mfilename.", None),
            'data-type' : 'sectioned'
            }

    def process(self):
        if self.setting('lexer'):
            lexer_alias = self.setting('lexer')
        elif self.prev_filter and self.prev_filter.alias == 'idio':
            lexer_alias = file_ext_to_lexer_alias_cache[self.prev_filter.prev_ext]
        else:
            lexer_alias = file_ext_to_lexer_alias_cache[self.input_data.ext]

        for section_name, section_input in self.input_data.items():
            section_output = "[source,%s]\n----\n%s\n----\n" % (lexer_alias, section_input)
            self.output_data[section_name] = section_output

        self.output_data.save()

class PygmentsFilter(DexyFilter):
    """
    Apply Pygments <http://pygments.org/> syntax highlighting.
    
    Image output formats require PIL to be installed.
    """
    aliases = ['pyg', 'pygments']
    IMAGE_OUTPUT_EXTENSIONS = ['.png', '.bmp', '.gif', '.jpg']
    MARKUP_OUTPUT_EXTENSIONS = [".html", ".tex", ".svg", ".txt"] # make sure .html is first so it is default output format
    LEXER_ERR_MSG = """Pygments doesn't know how to syntax highlight files like '%s' (for '%s').\
    You might need to specify the lexer manually."""

    _settings = {
            'examples' : ['pygments', 'pygments-image', 'pygments-stylesheets'],
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
            'lexer-args' : (
                "Dictionary of custom arguments to be passed directly to the lexer.",
                {}
                ),
            'lexer-settings' : (
                "List of all settings which will be passed to the lexer constructor.",
                []
            ),
            'formatter-settings' : (
                """List of all settings which will be passed to the formatter
                constructor.""", ['style', 'full', 'linenos', 'noclasses']
            ),

            'style' : ( "Formatter style to output.", 'default'),
            'noclasses' : ( "If set to true, token <span> tags will not use CSS classes, but inline styles.", None),
            'full' : ("""Pygments formatter option: output a 'full' document
                including header/footer tags.""", None),
            'linenos' : ("""Whether to include line numbers. May be set to
                'table' or 'inline'.""", None),
            'line-numbers' : ("""Alternative name for 'linenos'.""", None),
            }

    lexer_cache = {}

    def data_class_alias(klass, file_ext):
        if file_ext in klass.MARKUP_OUTPUT_EXTENSIONS:
            return 'sectioned'
        else:
            return 'generic'

    def docmd_css(klass, style='default'):
        """
        Prints out CSS for the specified style.
        """
        print(klass.generate_css(style))

    def docmd_sty(klass, style='default'):
        """
        Prints out .sty file (latex) for the specified style.
        """
        print(klass.generate_sty(style))

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
        elif self.alias == 'htmlsections':
            name_without_ext = posixpath.splitext(self.doc.name)[0]
            return "%s%s" % (name_without_ext, self.ext)
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

    def lexer_alias(self, ext):
        if self.setting('lexer'):
            self.log_debug("custom lexer %s specified" % self.setting('lexer'))
            return self.setting('lexer')

        is_json_file = ext in ('.json', '.dexy') or self.output_data.name.endswith(".dexy")

        if is_json_file and (pygments.__version__ < '1.5'):
            return "javascript"
        elif is_json_file:
            return "json"

        if ext == '.Makefile' or (ext == '' and 'Makefile' in self.input_data.name):
            return 'makefile'

        try:
            return file_ext_to_lexer_alias_cache[ext]
        except KeyError:
            pass

    def create_lexer_instance(self):
        ext = self.prev_ext
        lexer_alias = self.lexer_alias(ext)
        lexer_args = self.constructor_args('lexer')
        lexer_args.update(self.setting('lexer-args'))

        if not lexer_alias:
            msg = self.LEXER_ERR_MSG
            msgargs = (self.input_data.name, self.key)

            if self.setting('allow-unknown-ext'):
                self.log_warn(msg % msgargs)
                lexer_alias = 'text'
            else:
                raise dexy.exceptions.UserFeedback(msg % msgargs)

        if lexer_alias in pygments_lexer_cache and not lexer_args:
            return pygments_lexer_cache[lexer_alias]
        else:
            lexer = get_lexer_by_name(lexer_alias, **lexer_args)
            if not lexer_args:
                pygments_lexer_cache[lexer_alias] = lexer
            return lexer

        return lexer

    def create_formatter_instance(self):
        if self.setting('line-numbers') and not self.setting('linenos'):
            self.update_settings({'linenos' : self.setting('line-numbers')})

        formatter_args = self.constructor_args('formatter', {
            'lineanchors' : self.output_data.web_safe_document_key() })
        if self.setting('style') and not 'style' in formatter_args:
            formatter_args['style'] = self.setting('style')
        self.log_debug("creating pygments formatter with args %s" % (formatter_args))

        return get_formatter_for_filename(self.output_data.name, **formatter_args)

    def process(self):
        if self.ext in self.IMAGE_OUTPUT_EXTENSIONS:
            try:
                import PIL
                PIL # because pyflakes
            except ImportError:
                print("python imaging library is required by pygments to create image output")
                raise dexy.exceptions.InactivePlugin('pyg')

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
            self.update_all_args({'override-workspace-exclude-filters' : True })

        else:
            lexer = self.create_lexer_instance()

            if self.ext in self.IMAGE_OUTPUT_EXTENSIONS:
                # Place each section into an image.
                for k, v in self.input_data.items():
                    formatter = self.create_formatter_instance()
                    output_for_section = highlight(str(v).decode("utf-8"), lexer, formatter)
                    new_doc_name = "%s--%s%s" % (self.doc.key.replace("|", "--"), k, self.ext)
                    self.add_doc(new_doc_name, output_for_section)

                # Place entire contents into main file.
                formatter = self.create_formatter_instance()
                self.update_all_args({'override-workspace-exclude-filters' : True })
                with open(self.output_filepath(), 'wb') as f:
                    f.write(highlight(str(self.input_data), lexer, formatter))

            else:
                formatter = self.create_formatter_instance()
                for section_name, section_input in self.input_data.items():
                    try:
                        if isinstance(section_input, str):
                            section_input = section_input
                        else:
                            # If section_input is an instance of
                            # SectionValue then calling 'str' on this
                            # instance will call the __str__ method of
                            # SectionValue.
                            section_input = str(section_input)
                        section_output = highlight(section_input, lexer, formatter)
                    except UnicodeDecodeError:
                        if self.setting('allow-unprintable-input'):
                            section_input = self.setting('unprintable-input-text')
                            section_output = highlight(section_input, lexer, formatter)
                        else:
                            raise
                    self.output_data[section_name] = section_output
                self.output_data.save()


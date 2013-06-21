from datetime import datetime
from dexy.exceptions import UserFeedback
from dexy.utils import levenshtein
from dexy.version import DEXY_VERSION
from pygments.styles import get_all_styles
import calendar
import dexy.commands
import dexy.commands.cite
import dexy.data
import dexy.exceptions
import dexy.plugin
import inflection
import json
import os
import pygments
import pygments.formatters
import re

class TemplatePlugin(dexy.plugin.Plugin):
    __metaclass__ = dexy.plugin.PluginMeta
    aliases = []
    _settings = {}

    def is_active(klass):
        return True

    def __init__(self, filter_instance=None):
        if filter_instance:
            self.filter_instance = filter_instance

    def run(self):
        return {}

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

class PrettyPrintHtml(TemplatePlugin):
    """
    Uses BeautifulSoup 4 to prettify HTML.
    """
    @classmethod
    def is_active(klass):
        return BS4_AVAILABLE

    @classmethod
    def prettify_html(klass, html):
        soup = BeautifulSoup(unicode(html))
        return soup.prettify()

class Debug(TemplatePlugin):
    """
    Adds debug() and throw() [a.k.a. raise()] methods to templates.
    """
    aliases = ['debug']

    def debug(self, debug_text):
        print "template debug from '%s': %s" % (self.filter_instance.key, debug_text)
        return debug_text

    def throw(self, err_message):
        raise UserFeedback("template throw from '%s': %s" % (self.filter_instance.key, err_message))

    def run(self):
        return {
                'debug' : self.debug,
                'throw' : self.throw,
                'raise' : self.throw
                }

class Bibtex(TemplatePlugin):
    """
    Produces a bibtex entry for dexy.
    """
    @classmethod
    def run(self):
        return { 'dexy_bibtex' : dexy.commands.cite.bibtex_text() }

class Inflection(TemplatePlugin):
    """
    Exposes the inflection package for doing nice things with strings 
    """
    aliases = ['inflection']
    _settings = {
            'methods' : ("Methods of the inflection module to expose.",
                ['camelize', 'dasherize', 'humanize', 'ordinal',
                'ordinalize', 'parameterize', 'pluralize', 'singularize',
                'titleize', 'transliterate', 'underscore'])
            }

    def run(self):
        args = {}
        for method in self.setting('methods'):
            args[method] = getattr(inflection, method)
        return args

class JavadocToRst(TemplatePlugin):
    """
    Exposes javadoc2rst command which strips HTML tags from javadoc comments.
    """

    ESCAPE = ['\\']
    REMOVE = ['<p>', '<P>']

    @classmethod
    def javadoc2rst(klass, javadoc):
        for x in klass.REMOVE:
            javadoc = javadoc.replace(x, '\n')
        for x in klass.ESCAPE:
            javadoc = javadoc.replace(x, "\\%s" % x)
        return javadoc

class PrettyPrintJson(TemplatePlugin):
    """
    Exposes ppjson command.
    """
    aliases = ['ppjson']

    def ppjson(self, json_string):
        return json.dumps(json.loads(json_string), sort_keys = True, indent = 4)

    def run(self):
        return {
            'ppjson' : self.ppjson
         }

class JinjaFilters(TemplatePlugin):
    """
    Custom jinja filters which can be accessed using the | fn() syntax in jinja templates.
    """
    @classmethod
    def indent(klass, s, width=4, indentfirst=False):
        """
        Replacement for jinja's indent method to ensure unicode() is called prior to splitlines().
        """
        output = []
        for i, line in enumerate(unicode(s).splitlines()):
            if indentfirst or i > 0:
                output.append("%s%s" % (' ' * width, line))
            else:
                output.append(line)
        return "\n".join(output)

    @classmethod
    def head(klass, s, n=15):
        """
        Returns the first n lines of input string.
        """
        lines = unicode(s).splitlines()[0:n]
        return "\n".join(lines)

class RstCode(TemplatePlugin):
    """
    Indents code 4 spaces and wraps in .. code:: directive.
    """
    @classmethod
    def rstcode(klass, text, language='python'):
        output = [
            ".. code:: %s" % language,
            '   :class: highlight',
            '']
        for line in unicode(text).splitlines():
            output.append("    %s" % line)
        output.append('')
        return os.linesep.join(output)

class PythonDatetime(TemplatePlugin):
    """
    Exposes python datetime and calendar functions.
    """
    aliases = ['datetime', 'calendar']
    def run(self):
        today = datetime.today()
        month = today.month
        year = today.year
        cal = calendar.Calendar()
        caldates = list(cal.itermonthdates(year, month))

        return {
            "datetime" : datetime,
            "calendar" : calendar,
            "caldates" : caldates,
            "cal" : cal,
            "today" : today,
            "month" : month,
            "year" : year
            }

class DexyVersion(TemplatePlugin):
    """
    Exposes the current dexy version
    """
    aliases = ['dexyversion']
    def run(self):
        return { "DEXY_VERSION" : DEXY_VERSION }

class SimpleJson(TemplatePlugin):
    """
    Exposes the json module.
    """
    aliases = ['json']
    def run(self):
        return { 'json' : json }

class RegularExpressions(TemplatePlugin):
    """
    Exposes re_match and re_search.
    """
    aliases = ['regex']
    def run(self):
        return { 're_match' : re.match, 're_search' : re.search}

class PythonBuiltins(TemplatePlugin):
    """
    Exposes python builtins.
    """
    aliases = ['builtins']
    # Intended to be all builtins that make sense to run within a document.
    PYTHON_BUILTINS = [abs, all, any, bin, bool, bytearray, callable, chr,
        cmp, complex, dict, dir, divmod, enumerate, filter, float, format, hex,
        id, int, isinstance, issubclass, iter, len, list, locals, long, map,
        hasattr, max, min, oct, ord, pow, range, reduce, repr, reversed, round,
        set, slice, sorted, str, sum, tuple, xrange, unicode, zip]

    def run(self):
        return dict((f.__name__, f) for f in self.PYTHON_BUILTINS)

class PygmentsStylesheet(TemplatePlugin):
    """
    Generates pygments stylesheets.
    """
    aliases = ['pygments']

    # TODO figure out default fmt based on document ext
    @classmethod
    def highlight(klass, text, lexer_name, fmt = 'html', noclasses = False, lineanchors = 'l'):
        if text:
            text = unicode(text)
            formatter_options = { "lineanchors" : lineanchors, "noclasses" : noclasses }
            lexer = pygments.lexers.get_lexer_by_name(lexer_name)
            formatter = pygments.formatters.get_formatter_by_name(fmt, **formatter_options)
            return pygments.highlight(text, lexer, formatter)

    def run(self):
        pygments_stylesheets = {}
        if self.filter_instance.doc.args.has_key('pygments'):
            formatter_args = self.filter_instance.doc.args['pygments']
        else:
            formatter_args = {}

        for style_name in get_all_styles():
            for formatter_class in [pygments.formatters.LatexFormatter, pygments.formatters.HtmlFormatter]:
                formatter_args['style'] = style_name
                pygments_formatter = formatter_class(**formatter_args)
                style_info = pygments_formatter.get_style_defs()

                for fn in pygments_formatter.filenames:
                    ext = fn.split(".")[1]
                    if ext == 'htm':
                        ext = 'css' # swap the more intuitive '.css' for the unlikely '.htm'
                    key = "%s.%s" % (style_name, ext)
                    pygments_stylesheets[key] = style_info
        return {'pygments' : pygments_stylesheets, 'highlight' : self.highlight }

class Subdirectories(TemplatePlugin):
    """
    Show subdirectories under this document.
    """
    aliases = ['subdirectories']
    def run(self):
        # The directory containing the document to be processed.
        doc_dir = os.path.dirname(self.filter_instance.output_data.name)

        # Get a list of subdirectories under this document's directory.
        subdirectories = [d for d in sorted(os.listdir(os.path.join(os.curdir, doc_dir))) if os.path.isdir(os.path.join(os.curdir, doc_dir, d))]
        return {'subdirectories' : subdirectories}

class Variables(TemplatePlugin):
    """
    Allow users to set variables in document args which will be available to an individual document.
    """
    aliases = ['variables']
    def run(self):
        variables = {}
        variables.update(self.filter_instance.setting('variables'))
        variables.update(self.filter_instance.setting('vars'))
        return variables

class Globals(TemplatePlugin):
    """
    Makes available the global variables specified on the dexy command line
    using the --globals option
    """
    aliases = ['globals']
    def run(self):
        raw_globals = self.filter_instance.doc.wrapper.globals
        env = {}
        for kvpair in raw_globals.split(","):
            if "=" in kvpair:
                k, v = kvpair.split("=")
                env[k] = v
        return env

class Inputs(TemplatePlugin):
    """
    Populates the 'd' object.
    """
    aliases = ['inputs']

    def input_tasks(self):
        return self.filter_instance.doc.walk_input_docs()

    def a(self, relative_ref):
        return self.map_relative_refs[relative_ref]

    def run(self):
        self.map_relative_refs = {}

        for doc in self.input_tasks():
            for ref in doc.output_data().relative_refs(self.filter_instance.output_data.name):
                self.map_relative_refs[ref] = doc.output_data()

        return {
            'a' : self.a,
            'args' : self.filter_instance.doc.args,
            'd' : D(self.filter_instance.doc, self.map_relative_refs),
            'f' : self.filter_instance,
            's' : self.filter_instance.output_data,
            'w' : self.filter_instance.doc.wrapper
            }

class D(object):
    def __init__(self, doc, map_relative_refs):
        self._artifact = doc
        self._map_relative_refs = map_relative_refs

    def keys(self):
        return self._map_relative_refs.keys()

    def __getitem__(self, relative_ref):
        if self._map_relative_refs.has_key(relative_ref):
            return self._map_relative_refs[relative_ref]
        else:
            msg = "No document named '%s'\nis available as an input to '%s'.\n"

            closest_match_lev = 15 # if more than this, not worth mentioning
            closest_match = None

            for k in sorted(self._map_relative_refs):
                lev = levenshtein(k, relative_ref)
                if lev < closest_match_lev:
                    closest_match = k
                    closest_match_lev = lev
                self._artifact.log_warn(k)

            msg += "There are %s input documents available, their keys have been written to dexy's log.\n" % len(self._map_relative_refs)
           
            if closest_match:
                msg += "Did you mean '%s'?" % closest_match

            msgargs = (relative_ref, self._artifact.key)
            raise dexy.exceptions.UserFeedback(msg % msgargs)

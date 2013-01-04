from datetime import datetime
from dexy.plugin import PluginMeta
from dexy.version import DEXY_VERSION
from pygments.styles import get_all_styles
import calendar
import dexy.artifact
import dexy.commands
import dexy.data
import dexy.exceptions
import json
import os
import pygments
import pygments.formatters
import re

class TemplatePlugin():
    __metaclass__ = PluginMeta

    @classmethod
    def is_active(klass):
        return True

    def __init__(self, filter_instance):
        self.filter_instance = filter_instance
        self.log = self.filter_instance.artifact.log

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
    ALIASES = ['ppjson']

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
    ALIASES = ['datetime', 'calendar']
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
    ALIASES = ['dexyversion']
    def run(self):
        return { "DEXY_VERSION" : DEXY_VERSION }

class SimpleJson(TemplatePlugin):
    """
    Exposes the json module.
    """
    ALIASES = ['json']
    def run(self):
        return { 'json' : json }

class RegularExpressions(TemplatePlugin):
    """
    Exposes re_match and re_search.
    """
    ALIASES = ['regex']
    def run(self):
        return { 're_match' : re.match, 're_search' : re.search}

class PythonBuiltins(TemplatePlugin):
    """
    Exposes python builtins.
    """
    ALIASES = ['builtins']
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
    ALIASES = ['pygments']

    # TODO figure out default fmt based on document ext
    @classmethod
    def highlight(klass, text, lexer_name, fmt = 'html', noclasses = False, lineanchors = 'l'):
        if text:
            formatter_options = { "lineanchors" : lineanchors, "noclasses" : noclasses }
            lexer = pygments.lexers.get_lexer_by_name(lexer_name)
            formatter = pygments.formatters.get_formatter_by_name(fmt, **formatter_options)
            return pygments.highlight(text, lexer, formatter)

    def run(self):
        pygments_stylesheets = {}
        if self.filter_instance.artifact.args.has_key('pygments'):
            formatter_args = self.filter_instance.artifact.args['pygments']
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
    ALIASES = ['subdirectories']
    def run(self):
        # The directory containing the document to be processed.
        doc_dir = os.path.dirname(self.filter_instance.output().name)

        # Get a list of subdirectories under this document's directory.
        subdirectories = [d for d in sorted(os.listdir(os.path.join(os.curdir, doc_dir))) if os.path.isdir(os.path.join(os.curdir, doc_dir, d))]
        return {'subdirectories' : subdirectories}

class Variables(TemplatePlugin):
    """
    Allow users to set variables in document args which will be available to an individual document.
    """
    ALIASES = ['variables']
    def run(self):
        variables = {}
        variables.update(self.filter_instance.arg_value('variables', {}))
        variables.update(self.filter_instance.arg_value('vars', {}))
        return variables

class Globals(TemplatePlugin):
    """
    Makes available the global variables specified on the dexy command line
    using the --globals option
    """
    ALIASES = ['globals']
    def run(self):
        raw_globals = self.filter_instance.artifact.wrapper.globals
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
    ALIASES = ['inputs']

    def input_tasks(self):
        for doc in self.filter_instance.processed():
            yield doc.final_artifact

    def a(self, relative_ref):
        return self.map_relative_refs[relative_ref]

    def run(self):
        self.map_relative_refs = {}

        for task in self.input_tasks():
            for ref in task.output_data.relative_refs(self.filter_instance.output().name):
                self.map_relative_refs[ref] = task.output_data

        return {
            'a' : self.a,
            'args' : self.filter_instance.artifact.args,
            'd' : D(self.filter_instance.artifact, self.map_relative_refs),
            'f' : self.filter_instance,
            's' : self.filter_instance.output(),
            'w' : self.filter_instance.artifact.wrapper
            }

class D(object):
    def __init__(self, artifact, map_relative_refs):
        self._artifact = artifact
        self._map_relative_refs = map_relative_refs

    def __getitem__(self, relative_ref):
        if self._map_relative_refs.has_key(relative_ref):
            return self._map_relative_refs[relative_ref]
        else:
            raise dexy.exceptions.UserFeedback("There is no document named %s available to %s" % (relative_ref, self._artifact.key))

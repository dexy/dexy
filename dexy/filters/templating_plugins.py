from datetime import datetime
from dexy.exceptions import UserFeedback
from dexy.plugin import TemplatePlugin
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
import markdown
import operator
import os
import pygments
import pygments.formatters
import re
import time
import uuid
import xml.etree.ElementTree as ET

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

class Etree(TemplatePlugin):
    """
    Exposes element tree as ET.
    """
    aliases = ['etree']
    def run(self):
        return { 'ET' : ("The xml.etree.ElementTree module.", ET,) }

class Markdown(TemplatePlugin):
    """
    Exposes markdown.
    """
    aliases = ['md', 'markdown']

    def run(self):
        md = markdown.Markdown()
        h = "Function which converts markdown to HTML."
        return {
                'markdown' : (h, md.convert),
                'md' : (h, md.convert)
                }

class Uuid(TemplatePlugin):
    """
    Exposes the UUID module.
    """
    aliases = ['uuid']
    def run(self):
        return { 'uuid' : ("The Python uuid module. http://docs.python.org/2/library/uuid.html", uuid) }

class Time(TemplatePlugin):
    """
    Exposes time module.
    """
    aliases = ['time']
    def run(self):
        return { 'time' : ("The Python time module.", time) }

class Operator(TemplatePlugin):
    """
    Exposes features of the operator module.
    """
    aliases = ['operator']
    keys = ['attrgetter', 'itemgetter']
    def run(self):
        d = {}
        for k in self.keys:
            fn = getattr(operator, k)
            d[k] = ("The %s method from Python's operator module." % k, fn)
        return d

class PrettyPrintHtml(TemplatePlugin):
    """
    Uses BeautifulSoup 4 to prettify HTML.
    """
    aliases = ['bs4']

    @classmethod
    def is_active(klass):
        return BS4_AVAILABLE

    @classmethod
    def prettify_html(klass, html):
        soup = BeautifulSoup(unicode(html))
        return soup.prettify()

    def run(self):
        return {
            'prettify_html' : ("Pretty-print HTML using BeautifulSoup", self.prettify_html,),
            'BeautifulSoup' : ("The BeautifulSoup module.", BeautifulSoup,)
            }

class LoadYaml(TemplatePlugin):
    """
    Loads YAML from a file.
    """
    aliases = ['loadyaml']

    def load_yaml(self, filename):
        import yaml
        with open(filename, 'rb') as f:
            return yaml.safe_load(f.read())

    def run(self):
        return {
                'load_yaml' : ("Safely load YAML from a file.", self.load_yaml,)
                }

class Debug(TemplatePlugin):
    """
    Adds debug() and throw() [a.k.a. raise()] methods to templates.
    """
    aliases = ['debug']

    def debug(self, debug_text, echo=True):
        if hasattr(self, 'filter_instance'):
            print "template debug from '%s': %s" % (self.filter_instance.key, debug_text)
        else:
            print "template debug: %s" % (debug_text)

        if echo:
            return debug_text
        else:
            return ""

    def throw(self, err_message):
        if hasattr(self, 'filter_instance'):
            raise UserFeedback("template throw from '%s': %s" % (self.filter_instance.key, err_message))
        else:
            raise UserFeedback("template throw: %s" % (err_message))

    def run(self):
        return {
                'debug' : ("A debugging method - prints content to command line stdout.", self.debug),
                'throw' : ("A debugging utility which raises exception with argument.", self.throw),
                'raise' : ("Alias for `throw`.", self.throw)
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
        return dict((method, ("The %s method from Python inflection module." % method, getattr(inflection, method),)) for method in self.setting('methods'))

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

class PrettyPrint(TemplatePlugin):
    """
    Exposes pprint (really pformat).
    """
    aliases = ['pp', 'pprint']

    def run(self):
        import pprint
        return {
            'pprint' : ("Pretty prints Python objects.", pprint.pformat,),
            'pformat' : ("Pretty prints Python objects.", pprint.pformat,)
         }

class PrettyPrintJson(TemplatePlugin):
    """
    Exposes ppjson command.
    """
    aliases = ['ppjson']

    def ppjson(self, json_string):
        return json.dumps(json.loads(json_string), sort_keys = True, indent = 4)

    def run(self):
        return {
            'ppjson' : ("Pretty prints valid JSON.", self.ppjson,)
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
            "datetime" : ("The Python datetime module.", datetime),
            "calendar" : ("A Calendar instance from Python calendar module.", calendar),
            "caldates" : ("List of calendar dates in current month.", caldates),
            "cal" : ("Shortcut for `calendar`.", calendar),
            "today" : ("Result of datetime.today().", today),
            "month" : ("Current month.", month),
            "year" : ("Current year.", year)
            }

class DexyVersion(TemplatePlugin):
    """
    Exposes the current dexy version
    """
    aliases = ['dexyversion']
    def run(self):
        return { "DEXY_VERSION" : ("The active dexy version. Currently %s." % DEXY_VERSION, DEXY_VERSION) }

class SimpleJson(TemplatePlugin):
    """
    Exposes the json module.
    """
    aliases = ['json']
    def run(self):
        return { 'json' : ("The Python json module.", json,) }

class RegularExpressions(TemplatePlugin):
    """
    Exposes re_match and re_search.
    """
    aliases = ['regex']
    def run(self):
        return { 're' : ("The Python re module.", re,), }

class PythonBuiltins(TemplatePlugin):
    """
    Exposes python builtins.
    """
    aliases = ['builtins']
    # Intended to be all builtins that make sense to run within a document.
    PYTHON_BUILTINS = [abs, all, any, basestring, bin, bool, bytearray,
            callable, chr, cmp, complex, dict, dir, divmod, enumerate, filter,
            float, format, hex, id, int, isinstance, issubclass, iter, len,
            list, locals, long, map, hasattr, max, min, oct, ord, pow, range,
            reduce, repr, reversed, round, set, slice, sorted, str, sum, tuple,
            type, xrange, unicode, zip]

    def run(self):
        return dict((f.__name__, ("The python builtin function %s" % f.__name__, f,)) for f in self.PYTHON_BUILTINS)

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
        if hasattr(self, 'filter_instance') and self.filter_instance.doc.args.has_key('pygments'):
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
                        ext = 'css'
                    key = "%s.%s" % (style_name, ext)
                    pygments_stylesheets[key] = style_info
        return {
            'pygments' : ("Dictionary of pygments stylesheets.", pygments_stylesheets,),
            'highlight' : ("Syntax highlights contents. Args are (text, lexer_name).", self.highlight)
            }

class Subdirectories(TemplatePlugin):
    """
    Show subdirectories under this document.
    """
    aliases = ['subdirectories']
    def run(self):
        if hasattr(self.filter_instance, 'output_data'):
            # The directory containing the document to be processed.
            doc_dir = os.path.dirname(self.filter_instance.output_data.name)

            # Get a list of subdirectories under this document's directory.
            subdirectories = [d for d in sorted(os.listdir(os.path.join(os.curdir, doc_dir))) if os.path.isdir(os.path.join(os.curdir, doc_dir, d))]
            return {'subdirectories' : ("List of subdirectories of this document.", subdirectories)}
        else:
            return {'subdirectories' : ("List of subdirectories of this document.", [])}

class Variables(TemplatePlugin):
    """
    Allow users to set variables in document args which will be available to an individual document.
    """
    aliases = ['variables']
    def run(self):
        variables = {}
        variables.update(self.filter_instance.setting('variables'))
        variables.update(self.filter_instance.setting('vars'))

        formatted_variables = {}
        for k, v in variables.iteritems():
            if isinstance(v, tuple):
                formatted_variables[k] = v
            elif isinstance(v, list) and len(v) == 2:
                formatted_variables[k] = v
            else:
                formatted_variables[k] = ("User-provided variable.", v)
        return formatted_variables

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

    def run(self):
        input_docs = {}

        for doc in self.input_tasks():
            input_docs[doc.key] = doc

        d = D(self.filter_instance.doc, input_docs)

        if hasattr(self.filter_instance, 'output_data'):
            output_data = self.filter_instance.output_data
        else:
            output_data = None

        return {
            'a' : ("Another way to reference 'd'. Deprecated.", d),
            'args' : ("The document args.", self.filter_instance.doc.args),
            'd' : ("The 'd' object.", d),
            'f' : ("The filter instance for this document.", self.filter_instance),
            's' : ("The data instance for this document.", output_data),
            'w' : ("The wrapper for the dexy run.", self.filter_instance.doc.wrapper)
            }

class D(object):
    def __init__(self, doc, input_docs):
        self._artifact = doc
        self._parent_dir = doc.output_data().parent_dir()
        self._input_docs = input_docs.values()
        self._input_doc_keys = [d.key for d in self._input_docs]
        self._input_doc_names = [d.output_data().long_name() for d in self._input_docs]
        self._input_doc_titles = ["title:%s" % d.output_data().title() for d in self._input_docs]

        self._ref_cache = {}

    def key_or_name_index(self, ref):
        if ref in self._input_doc_keys:
            return self._input_doc_keys.index(ref)
        elif ref in self._input_doc_names:
            return self._input_doc_names.index(ref)

    def matching_keys(self, ref):
        return [(i, k) for (i, k) in enumerate(self._input_doc_keys) if k.startswith(ref)]

    def unique_matching_key(self, ref):
        """
        If the reference unambiguously identifies a single key, return it.
        """
        matching_keys = self.matching_keys(ref)
        if len(matching_keys) == 1:
            return matching_keys[0]

    def title_index(self, ref):
        if ref in self._input_doc_titles:
            return self._input_doc_titles[ref]

    def __getitem__(self, ref):
        try:
            return self._ref_cache[ref]
        except KeyError:
            pass

        doc = None
        path_to_ref = None
        index = None

        if ref.startswith("/"):
            path_to_ref = ref.lstrip("/")
            index = self.key_or_name_index(path_to_ref)

        elif ref.startswith('title:'):
            index = self.title_index(ref)

        else:
            if self._parent_dir:
                path_to_ref = os.path.normpath(os.path.join(self._parent_dir, ref))
            else:
                path_to_ref = ref

            index = self.key_or_name_index(path_to_ref)

        if index is not None:
            doc = self._input_docs[index]
        else:
            matching_key = self.unique_matching_key(ref)
            if matching_key:
                doc = self._input_docs[matching_key[0]]

        if doc:
            # store this reference in cache for next time
            self._ref_cache[ref] = doc.output_data()
            return doc.output_data()
        else:
            msg = "No document named '%s'\nis available as an input to '%s'.\n"

            closest_match_lev = 15 # if more than this, not worth mentioning
            closest_match = None

            self._artifact.log_warn("Listing documents which are available:")
            for k in sorted(self._input_doc_keys):
                lev = levenshtein(k, path_to_ref)
                if lev < closest_match_lev:
                    closest_match = k
                    closest_match_lev = lev
                self._artifact.log_warn("  %s" % k)

            msg += "There are %s input documents available, their keys have been written to dexy's log.\n" % len(self._input_doc_keys)
           
            if closest_match:
                msg += "Did you mean '%s'?" % closest_match

            msgargs = (ref, self._artifact.key)
            raise dexy.exceptions.UserFeedback(msg % msgargs)

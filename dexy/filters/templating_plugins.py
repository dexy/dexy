from bs4 import BeautifulSoup
from collections import UserDict
from datetime import datetime
from dexy.exceptions import InternalDexyProblem
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
import inspect
import jinja2
import json
import markdown
import operator
import os
import pygments
import pygments.formatters
import random
import re
import time
import uuid
import xml.etree.ElementTree as ET

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

class Random(TemplatePlugin):
    """
    Exposes random module.
    """
    aliases = ['random']

    def shuffle(self, input_array):
        return sorted(input_array, key=lambda *args: random.random())

    def run(self):
        return { 'random' : ("The Python random module.", random),
                'shuffle' : ("Random shuffle not in place.", self.shuffle) }

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
    _settings = {
            'no-jinja-filter' : ['BeautifulSoup']
            }

    def prettify_html(self, html):
        soup = BeautifulSoup(str(html), 'html.parser')
        return soup.prettify()

    def run(self):
        return {
            'prettify_html' : ("Pretty-print HTML using BeautifulSoup", self.prettify_html),
            'BeautifulSoup' : ("The BeautifulSoup module.", BeautifulSoup)
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

class ParseYaml(TemplatePlugin):
    """
    Parse YAML from a string.
    """
    aliases = ['parseyaml']

    def parse_yaml(self, yamltext):
        import yaml
        return yaml.safe_load(str(yamltext))

    def run(self):
        return {
                'parse_yaml' : ("Safely load YAML from text.", self.parse_yaml,)
                }

class Debug(TemplatePlugin):
    """
    Adds debug() and throw() [a.k.a. raise()] methods to templates.
    """
    aliases = ['debug']

    def debug(self, debug_text, echo=True):
        if hasattr(self, 'filter_instance'):
            print("template debug from '%s': %s" % (self.filter_instance.key, debug_text))
        else:
            print("template debug: %s" % (debug_text))

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

class StripJavadocHTML(TemplatePlugin):
    """
    Exposes javadoc2rst command which strips HTML tags from javadoc comments.
    """
    aliases = ['stripjavadochtml']
    _settings = {
            'escape' : ("Escape characters.", ['\\']),
            'remove' : ("Remove characters.", ['<p>', '<P>'])
            }

    def strip_javadoc_html(self, javadoc):
        for symbol in self.setting('escape'):
            javadoc = javadoc.replace(symbol, '\n')
        for word in self.setting('remove'):
            javadoc = javadoc.replace(word, "\\%s" % symbol)
        return javadoc

    def run(self):
        h = "Replace escape character with newlines and remove paragraph tags."
        return {
                'javadoc2rst' : (h, self.strip_javadoc_html),
                'strip_javadoc_html' : (h, self.strip_javadoc_html)
                }

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

class ReplaceJinjaFilters(TemplatePlugin):
    """
    Replace some jinja filters so they call unicode() first.
    """
    aliases = ['replacejinjafilters']

    def do_indent(self, data, width=4, indentfirst=False):
        return jinja2.filters.do_indent(str(data), width, indentfirst)

    def run(self):
        return {
                'indent' : ("Jinja's indent function.", self.do_indent)
                }

class Assertions(TemplatePlugin):
    """
    Allow making assertions in documents.
    """
    aliases = ['assertions']

    def decorate_response(self, doc):
        if hasattr(self, 'filter_instance'):
            indicator = self.filter_instance.setting('assertion-passed-indicator')
        else:
            indicator = None

        if indicator:
            return str(doc) + indicator
        else:
            return doc

    def do_assert_equals(self, doc, expected):
        """
        Assert that input equals expected value.
        """
        assert str(doc) == expected, "input text did not equal '%s'" % expected
        return self.decorate_response(doc)

    def do_assert_contains(self, doc, contains):
        """
        Assert that input equals expected value.
        """
        assert contains in str(doc), "input text did not contain '%s'" % contains
        return self.decorate_response(doc)

    def do_assert_does_not_contain(self, doc, shouldnt_contain):
        """
        Assert that input equals expected value.
        """
        msg = "input text contained '%s'" % shouldnt_contain
        assert not shouldnt_contain in str(doc), msg
        return self.decorate_response(doc)

    def do_assert_startswith(self, doc, startswith):
        """
        Assert that the input starts with the specified value.
        """
        assert str(doc).startswith(startswith), "input text did not start with '%s'" % startswith
        return self.decorate_response(doc)

    def do_assert_matches(self, doc, regexp):
        """
        Assert that input matches the specified regular expressino.
        """
        assert re.match(regexp, str(doc)), "input text did not match regexp %s" % regexp
        return self.decorate_response(doc)

    def make_soup(self, doc):
        return BeautifulSoup(str(doc))

    def soup_select(self, doc, selector):
        soup = self.make_soup(doc)
        return soup.select(selector)

    def soup_select_unique(self, doc, selector):
        results = self.soup_select(doc, selector)

        n = len(results)
        if n == 0:
            msg = "no results found matching selector '%s'"
            msgargs = (selector,)
            raise AssertionError(msg % msgargs)

        elif n > 1:
            msg = "%s results found matching selector '%s', must be unique"
            msgargs = (n, selector,)
            raise AssertionError(msg % msgargs)

        return results[0]

    def do_assert_selector_text(self, doc, selector, expected_text):
        """
        Asserts that the contents of CSS selector matches the expected text.
        
        Leading/trailing whitespace is stripped before comparison.
        """
        element = self.soup_select_unique(doc, selector)
        err = "element '%s' did not contain '%s'" % (selector, expected_text)
        assert element.get_text().strip() == expected_text, err

    def run(self):
        methods = {}
        for name in dir(self):
            if name.startswith("do_"):
                method = getattr(self, name)
                docs = inspect.getdoc(method).splitlines()[0].strip()
                if not docs:
                    raise InternalDexyProblem("You must define docstring for %s" % name)
                methods[name.replace("do_", "")] = (docs, method)
        return methods

class Head(TemplatePlugin):
    """
    Provides a 'head' method.
    """
    aliases = ['head']

    def head(self, text, n=15):
        """
        Returns the first n lines of input string.
        """
        return "\n".join(str(text).splitlines()[0:n])

    def run(self):
        return {
                'head' : ("Returns the first n lines of input string.", self.head)
                }

class Tail(TemplatePlugin):
    """
    Provides a 'tail' method.
    """
    aliases = ['tail']

    def tail(self, text, n=15):
        """
        Returns the last n lines of input string.
        """
        return "\n".join(str(text).splitlines()[-n:])

    def run(self):
        return {
                'tail' : ("Returns the last n lines of inptu string.", self.tail)
                }

class Trunc(TemplatePlugin):
    """
    Provides a 'trunc[ate]' method.
    """
    aliases = ['trunc']

    def trunc(self, text, n=80, cont="..."):
        """
        Returns the first n characters of each line, indicating with cont (...) if it has been truncated.
        """
        def truncate_line(line):
            if len(line) < n:
                return line
            else:
                return line[0:n-len(cont)] + cont
        return "\n".join(truncate_line(line) for line in str(text).splitlines())

    def run(self):
        return {
                'trunc' : ("Returns the first n characters of each line, indicating with cont if it has been truncated", self.trunc)
                }

class RstCode(TemplatePlugin):
    """
    Indents code n spaces (defaults to 4) and wraps in .. code:: directive.
    """
    aliases = ['rstcode']

    def rstcode(self, text, n=4, language='python'):
        output = inspect.cleandoc("""
            .. code:: %s
            '   :class: highlight'
            """ % language)

        for line in str(text).splitlines():
            output += " " * n + line

        output += "\n"
        return output

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
    PYTHON_BUILTINS = [abs, all, any, bin, bool, bytearray,
            callable, chr, complex, dict, dir, divmod, enumerate, filter,
            float, format, hex, id, int, isinstance, issubclass, iter, len,
            list, locals, map, hasattr, max, min, oct, ord, pow, range,
            repr, reversed, round, set, slice, sorted, str, sum, tuple,
            type, str, zip]

    def run(self):
        return dict((f.__name__, ("The python builtin function %s" % f.__name__, f,)) for f in self.PYTHON_BUILTINS)

class PygmentsStylesheet(TemplatePlugin):
    """
    Inserts pygments style codes.
    """
    aliases = ['pygments']

    # TODO rewrite this so it's a function rather than pre-generating all
    # of the stylesheets. Detect document format automatically.

    def generate_stylesheets(self):
        pygments_stylesheets = {}
        if hasattr(self, 'filter_instance') and 'pygments' in self.filter_instance.doc.args:
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

        return pygments_stylesheets

    def run(self):
        return {
            'pygments' : (
                "Dictionary of pygments stylesheets.",
                self.generate_stylesheets()
             )}

class PygmentsHighlight(TemplatePlugin):
    """
    Provides a 'highlight' function for applying syntax highlighting.
    """
    aliases = ['highlight']
    # TODO figure out default fmt based on document ext - document would need
    # to implement a "final_ext()" method

    def highlight(self, text, lexer_name, fmt='html', noclasses=False, style=None, lineanchors='l'):
        text = str(text)
        formatter_options = { "lineanchors" : lineanchors, "noclasses" : noclasses }
        if style is not None:
            formatter_options['style'] = style
        lexer = pygments.lexers.get_lexer_by_name(lexer_name)
        formatter = pygments.formatters.get_formatter_by_name(fmt, **formatter_options)
        return pygments.highlight(text, lexer, formatter)

    def run(self):
        return {
                'highlight' : ("Pygments syntax highlighter.", self.highlight),
                'pygmentize' : ("Pygments syntax highlighter.", self.highlight)
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
        for k, v in variables.items():
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
                env[k] = ("Global variable %s" % k, v)
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
            self.filter_instance.log_debug("adding input doc %s" % doc.key)
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

class D(UserDict):
    def __init__(self, doc, input_docs):
        self._artifact = doc
        self._parent_dir = doc.output_data().parent_dir()
        self._input_docs_dict = input_docs
        self._input_docs = list(input_docs.values())
        self._input_doc_keys = list(input_docs.keys())
        self._input_doc_names = [d.output_data().long_name() for d in self._input_docs]
        self._input_doc_titles = ["title:%s" % d.output_data().title() for d in self._input_docs]

        self._ref_cache = {}

    def keys(self):
        return self._input_doc_keys

    def items(self):
        return self._input_docs_dict.items()

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

    def path_to(self, other):
        if self._parent_dir:
            return os.path.normpath(os.path.join(self._parent_dir, other))
        else:
            return other

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
            path_to_ref = self.path_to(ref)
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
                self._artifact.log_warn("  %s" % self.path_to(k))

            msg += "There are %s input documents available, their keys have been written to dexy's log.\n" % len(self._input_doc_keys)
           
            if closest_match:
                path_to_closest_match = self.path_to(closest_match)
                msg += "Did you mean '%s'?" % path_to_closest_match

            msgargs = (ref, self._artifact.key)
            raise dexy.exceptions.UserFeedback(msg % msgargs)

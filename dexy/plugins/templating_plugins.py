from datetime import datetime
from dexy.artifact import Artifact
from dexy.common import OrderedDict
from dexy.doc import Doc, PatternDoc
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
import pprint
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

class PrettyPrintJson(TemplatePlugin):
    ALIASES = ['ppjson']

    def ppjson(self, json_string):
        return json.dumps(json.loads(json_string), sort_keys = True, indent = 4)

    def run(self):
        return {
            'ppjson' : self.ppjson
         }

class PythonDatetime(TemplatePlugin):
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
    ALIASES = ['dexyversion']
    def run(self):
        return { "DEXY_VERSION" : DEXY_VERSION }

class SimpleJson(TemplatePlugin):
    ALIASES = ['json']
    def run(self):
        return { 'json' : json }

class PrettyPrinter(TemplatePlugin):
    ALIASES = ['pprint']
    def run(self):
        return { 'pformat' : pprint.pformat}

class RegularExpressions(TemplatePlugin):
    ALIASES = ['regex']
    def run(self):
        return { 're_match' : re.match, 're_search' : re.search}

class PythonBuiltins(TemplatePlugin):
    ALIASES = ['builtins']
    # Intended to be all builtins that make sense to run within a document.
    PYTHON_BUILTINS = [abs, all, any, bin, bool, bytearray, callable, chr,
        cmp, complex, dict, dir, divmod, enumerate, filter, float, format,
        hex, id, int, isinstance, issubclass, iter, len, list, long, map, hasattr,
        max, min, oct, ord, pow, range, reduce, repr, reversed, round,
        set, slice, sorted, str, sum, tuple, xrange, unicode, zip]

    def run(self):
        return dict((f.__name__, f) for f in self.PYTHON_BUILTINS)

class PygmentsStylesheet(TemplatePlugin):
    ALIASES = ['pygments']

    # TODO figure out default fmt based on document ext
    def highlight(self, text, lexer_name, fmt = 'html', noclasses = False, lineanchors = 'l'):
        if text:
            formatter_options = { "lineanchors" : lineanchors, "noclasses" : noclasses }
            lexer = pygments.lexers.get_lexer_by_name(lexer_name)
            formatter = pygments.formatters.get_formatter_by_name(fmt, **formatter_options)
            return pygments.highlight(text, lexer, formatter)
        else:
            raise dexy.commands.UserFeedback("calling 'highlight' command on blank text in %s" % self.filter_instance.artifact.key)

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
    ALIASES = ['inputs']

    @classmethod
    def load_sort_json_data(klass, a):
        try:
            unsorted_json = json.loads(a.output_text())
        except ValueError as e:
            print "unable to load JSON for", a.key
            print a.filename()
            print len(a.output_text())
            raise e

        def sort_dict(d):
            od = OrderedDict()
            for k in sorted(d.keys()):
                v = d[k]
                if isinstance(v, dict) or isinstance(v, OrderedDict):
                    od[k] = sort_dict(v)
                else:
                    od[k] = v
            return od

        if type(unsorted_json) == dict:
            return sort_dict(unsorted_json)
        else:
            return unsorted_json

    @classmethod
    def d_data_for_artifact(klass, a):
        data = a.output_data.data()
        if hasattr(data, 'keys') and data.keys() == ['1']:
            data = data['1']

        return data

    def input_tasks(self):
        for task in self.filter_instance.processed():
            if task.state != 'complete':
                raise Exception("All tasks should be complete! Task %s in state %s" % (task.key, task.state))

            if isinstance(task, Artifact):
                yield task
            elif isinstance(task, Doc):
                yield task.final_artifact
            elif isinstance(task, PatternDoc):
                next
            else:
                raise Exception("task is a %s" % task.__class__.__name__)

    def a(self, relative_ref):
        return self.map_relative_refs[relative_ref]

    def tc(self, input_text, id=None, title="show code"):
        return """<p class="heading" id="%(id)s">%(title)s</p>
<div class="toggle-code">
<div class="toggle-code-sidebar"></div>
<div class="toggle-code-content">
%(input_text)s
</div>
</div>""" % locals()

    def run(self):
        self.map_relative_refs = {}

        for task in self.input_tasks():
            for ref in task.output_data.relative_refs(self.filter_instance.output().name):
                self.map_relative_refs[ref] = task.output_data

        self.log.debug("relative refs are %s" % sorted(self.map_relative_refs))
        return {
            'a' : self.a,
            'd' : D(self.filter_instance.artifact, self.map_relative_refs),
            'tc' : self.tc,
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

from datetime import datetime
from dexy.version import Version
import dexy.artifact
from ordereddict import OrderedDict
from pygments.styles import get_all_styles
import calendar
import dexy.commands
import json
import os
import pprint
import pygments
import pygments.formatters
import re
import urllib

class TemplatePlugin(object):
    def __init__(self, filter_instance):
        self.filter_instance = filter_instance
        self.log = self.filter_instance.artifact.log

    def run(self):
        return {}

class PrettyPrintJsonTemplatePlugin(TemplatePlugin):
    def ppjson(self, json_string):
        return json.dumps(json.loads(json_string), sort_keys = True, indent = 4)

    def run(self):
        return {
            'ppjson' : self.ppjson
         }

class PythonDatetimeTemplatePlugin(TemplatePlugin):
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

class DexyVersionTemplatePlugin(TemplatePlugin):
    def run(self):
        return { "dexy_version" : Version.VERSION }

class DexyRootTemplatePlugin(TemplatePlugin):
    def run(self):
        return { "DEXY_ROOT" : os.path.abspath(os.getcwd()) }

class SimpleJsonTemplatePlugin(TemplatePlugin):
    def run(self):
        return { 'json' : json }

class PrettyPrinterTemplatePlugin(TemplatePlugin):
    def run(self):
        return { 'pformat' : pprint.pformat}

class RegularExpressionsTemplatePlugin(TemplatePlugin):
    def run(self):
        return { 're_match' : re.match, 're_search' : re.search}

class PythonBuiltinsTemplatePlugin(TemplatePlugin):
    # Intended to be all builtins that make sense to run within a document.
    PYTHON_BUILTINS = [abs, all, any, bin, bool, bytearray, callable, chr,
        cmp, complex, dict, dir, divmod, enumerate, filter, float, format,
        hex, id, int, isinstance, issubclass, iter, len, list, long, map, hasattr,
        max, min, oct, ord, pow, range, reduce, repr, reversed, round,
        set, slice, sorted, str, sum, tuple, xrange, unicode, zip]

    def run(self):
        return dict((f.__name__, f) for f in self.PYTHON_BUILTINS)

class PygmentsStylesheetTemplatePlugin(TemplatePlugin):
    def highlight(self, text, lexer_name, fmt = 'html', noclasses = False, lineanchors = 'l'):
        if text:
            formatter_options = { "lineanchors" : lineanchors, "noclasses" : noclasses }
            lexer = pygments.lexers.get_lexer_by_name(lexer_name)
            formatter = pygments.formatters.get_formatter_by_name(fmt, **formatter_options)
            return pygments.highlight(text, lexer, formatter)
        else:
            #raise dexy.commands.UserFeedback("calling highlight on blank text in %s" % self.filter_instance.artifact.key)
            pass

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

class SubdirectoriesTemplatePlugin(TemplatePlugin):
    def run(self):
        # The directory containing the document to be processed.
        doc_dir = os.path.dirname(self.filter_instance.artifact.name)

        # Get a list of subdirectories under this document's directory.
        subdirectories = [d for d in sorted(os.listdir(os.path.join(os.curdir, doc_dir))) if os.path.isdir(os.path.join(os.curdir, doc_dir, d))]
        return {'subdirectories' : subdirectories}

class VariablesTemplatePlugin(TemplatePlugin):
    def run(self):
        variables = {}
        if self.filter_instance.artifact.args.has_key('variables'):
            variables.update(self.filter_instance.artifact.args['variables'])
        if self.filter_instance.artifact.args.has_key('$variables'):
            variables.update(self.filter_instance.artifact.args['$variables'])
        return variables

class GlobalsTemplatePlugin(TemplatePlugin):
    """
    Makes available the global variables specified on the dexy command line
    using the --globals option
    """
    def run(self):
        if self.filter_instance.artifact.controller_args.has_key('globals'):
            return self.filter_instance.artifact.controller_args['globals']
        else:
            return {}

class NavigationTemplatePlugin(TemplatePlugin):
    """
    Creates a sitemap - dict with keys for each directory, values for each key
    are a set of final artifacts in that directory
    """
    def run(self):
        sitemap = {}
        inputs = self.filter_instance.artifact.inputs()

        keys = inputs.keys()
        keys.append(self.filter_instance.artifact.key)

        for key in keys:
            artifact = inputs.get(key, self.filter_instance.artifact)
            if artifact.name and artifact.final:
                artifact_dir = artifact.canonical_dir()
                if not artifact_dir in sitemap:
                    sitemap[artifact_dir] = []
                sitemap[artifact_dir].append(key)

        for k, v in sitemap.iteritems():
            v.sort()

        return {
                'sitemap' : sitemap,
                'artifacts' : inputs,
                's' : self.filter_instance.artifact
                }

class InputsTemplatePlugin(TemplatePlugin):
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
        # Do any special handling of data
        if a.ext == '.json':
            if len(a.output_text()) == 0:
                # Hack for JSON data being written directly to a file, e.g. filenames filter
                with open(a.filepath(), "rb") as f:
                    a.data_dict['1'] = f.read()
            data = klass.load_sort_json_data(a)
        elif a.ext == ".cpickle":
            with open(a.filepath(), "rb") as f:
                data = cPickle.load(f)
        else:
            data = a.data_dict

        if hasattr(data, 'keys') and data.keys() == ['1']:
            return data['1']
        else:
            return data

    def run(self):
        d_hash = {}
        a_hash = {}

        name = self.filter_instance.artifact.name
        inputs = self.filter_instance.artifact.inputs()

        for key, a in inputs.iteritems():
            keys = a.relative_refs(name)

            data = self.d_data_for_artifact(a)

            for k in keys:
                # Avoid adding duplicate keys
                if a_hash.has_key(k):
                    next

                a_hash[k] = a
                d_hash[k] = data

        return {
            'a' : a_hash,
            's' : self.filter_instance.artifact,
            'd' : d_hash,
            'f' : self.filter_instance,
        }


class D(object):
    def __init__(self, artifact, map_relative_refs):
        self._artifact = artifact
        self._map_relative_refs = map_relative_refs

    def __getitem__(self, relative_ref):
        if self._map_relative_refs.has_key(relative_ref):
            return self._map_relative_refs[relative_ref]
        else:
            raise dexy.commands.UserFeedback("There is no document named %s available to %s" % (relative_ref, self._artifact.key))

class InputsJustInTimeTemplatePlugin(InputsTemplatePlugin):
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
        for k, a in self.filter_instance.artifact.inputs().iteritems():
            for ref in a.relative_refs(self.filter_instance.artifact.name):
                self.map_relative_refs[ref] = a

        return {
            'a' : self.a,
            'd' : D(self.filter_instance.artifact, self.map_relative_refs),
            'tc' : self.tc,
            'f' : self.filter_instance,
            's' : self.filter_instance.artifact
            }

class ClippyHelperTemplatePlugin(TemplatePlugin):
    PRE_AND_CLIPPY_STRING = """
<pre>
%s
</pre>%s
    """
    CLIPPY_HELPER_STRING = """
<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000"
                width="110"
                height="14"
                id="clippy" >
<param name="movie" value="/clippy.swf"/>
<param name="allowScriptAccess" value="always" />
<param name="quality" value="high" />
<param name="scale" value="noscale" />
<param NAME="FlashVars" value="text=%s">
<param name="bgcolor" value="#ffffff">
<embed src="/clippy.swf"
       width="110"
       height="14"
       name="clippy"
       quality="high"
       allowScriptAccess="always"
       type="application/x-shockwave-flash"
       pluginspage="http://www.macromedia.com/go/getflashplayer"
       FlashVars="text=%s"
       bgcolor="#ffffff"
/>
</object>"""

    def run(self):
        return {
            'pre_and_clippy' : self.pre_and_clippy,
            'clippy_helper' : self.clippy_helper
        }

    def pre_and_clippy(self, text):
        self.log.debug("in pre_and_clippy")
        return self.PRE_AND_CLIPPY_STRING % (text, self.clippy_helper(text))

    def clippy_helper(self, text):
        if isinstance(text, dexy.artifact.Artifact):
            text = text.output_text()

        if not text or len(text) == 0:
            raise UserFeedback("You passed blank text to clippy helper!")

        self.log.debug("Applying clippy helper to %s" % text)
        quoted_text = urllib.quote(text)
        return self.CLIPPY_HELPER_STRING % (quoted_text, quoted_text)

from dexy.dexy_filter import DexyFilter
from jinja2 import Environment
from jinja2 import StrictUndefined
from jinja2.exceptions import TemplateSyntaxError
from ordereddict import OrderedDict
import json
import os
import pprint
import re
import traceback
import urllib

try:
    import pygments
    import pygments.formatters
    from pygments.styles import get_all_styles
    USE_PYGMENTS = True
except ImportError:
    USE_PYGMENTS = False

class FilenameFilter(DexyFilter):
    """Generate random filenames to track provenance of data."""
    ALIASES = ['fn']

    def process_text(self, input_text):
        # TODO this should not match more than two dashes
        for m in re.finditer("dexy--(\S+)\.([a-z]+)", input_text):
            local_key = m.groups()[0]
            ext = m.groups()[1]

            parent_dir = os.path.dirname(self.artifact.name)
            key = os.path.join(parent_dir, local_key)

            key_with_ext = "%s.%s" % (key, ext)
            key_with_ext_with_dexy = "%s|dexy" % key_with_ext

            if key_with_ext in self.artifact.inputs().keys():
                artifact = self.artifact.inputs()[key_with_ext]
                self.log.debug("[fn] existing key %s in artifact %s links to file %s" %
                          (key_with_ext, self.artifact.key, artifact.filename()))
            elif key_with_ext_with_dexy in self.artifact.inputs().keys():
                artifact = self.artifact.inputs()[key_with_ext_with_dexy]
                self.log.debug("[fn] existing key %s in artifact %s links to existing file %s" %
                          (key_with_ext, self.artifact.key, artifact.filename()))
            else:
                artifact = self.artifact.add_additional_artifact(key, ext)
                self.log.debug("[fn] added key %s to artifact %s ; links to new file %s" %
                          (key_with_ext, self.artifact.key, artifact.filename()))

            input_text = input_text.replace(m.group(), artifact.filename())

        # Hack to replace __ with -- in case we want to document how to use this
        # filter, we can't use -- because this will be acted upon.
        for m in re.finditer("dexy__(.+)\.([a-z]+)", input_text):
            key = m.groups()[0]
            ext = m.groups()[1]
            replacement_key = "dexy--%s.%s" % (key, ext)
            input_text = input_text.replace(m.group(), replacement_key)

        return input_text

class JinjaFilter(DexyFilter):
    """
    Runs the Jinja templating engine on your document to incorporate dynamic
    content.
    """
    ALIASES = ['jinja']
    FINAL = True
    CHANGE_EXTENSIONS = {
        ".mds" : ".md"
        }
    PYTHON_BUILTINS = [abs, all, any, bin, bool, bytearray, callable, chr,
        cmp, complex, dict, dir, divmod, enumerate, filter, float, format,
        hex, id, int, isinstance, issubclass, iter, len, list, long, map,
        max, min, oct, ord, pow, range, reduce, repr, reversed, round,
        set, slice, sorted, str, sum, tuple, xrange, zip
        ]

    def pre_and_clippy(self, text):
        return """<pre>
%s
</pre>%s
""" % (text, self.clippy_helper(text))

    def clippy_helper(self, text):
        if not text or len(text) == 0:
            raise Exception("You passed blank text to clippy helper!")
        quoted_text = urllib.quote(text)
        return """<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000"
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
        </object>""" % (quoted_text, quoted_text)

    def process_sort_json_data(self, a):
        try:
            unsorted_json = json.loads(a.output_text())
        except ValueError as e:
            print "unable to load JSON for", a.key
            raise e

        def sort_dict(d):
            od = OrderedDict()
            for k in sorted(d.keys()):
                v = d[k]
                if isinstance(v, dict) or isinstance(v, OrderedDict):
                    od[k] = sort_dict(v)
                else:
                    if self.notextile and isinstance(v, str) and "<span" in v and not "<notextile>" in v:
                        od[k] = "<notextile>\n%s\n</notextile>" % v
                    else:
                        od[k] = v
            return od

        return sort_dict(unsorted_json)

    def process_apply_notextile_html(self, a):
        data = OrderedDict()
        for s, h in a.data_dict.items():
            if "<notextile>" in h:
                data[s] = h
            else:
                data[s] = "<notextile>\n%s\n</notextile>" % h
        return data

    def setup_jinja_env(self):
        if self.artifact.ext == ".tex":
            self.log.debug("changing jinja tags to << >> etc. for %s" % self.artifact.key)
            env = Environment(
                block_start_string = '<%',
                block_end_string = '%>',
                variable_start_string = '<<',
                variable_end_string = '>>',
                comment_start_string = '<#',
                comment_end_string = '#>',
                undefined = StrictUndefined
                )
        else:
            env = Environment()
        return env

    def create_pygments_stylesheets(self):
        if not hasattr(self.__class__, 'PYGMENTS_STYLESHEETS'):
            pygments_stylesheets = {}
            for style_name in get_all_styles():
                for formatter_class in [pygments.formatters.LatexFormatter, pygments.formatters.HtmlFormatter]:
                    pygments_formatter = formatter_class(style=style_name)
                    style_info = pygments_formatter.get_style_defs()

                    for fn in pygments_formatter.filenames:
                        ext = fn.split(".")[1]
                        if ext == 'htm':
                            ext = 'css' # swap the more intuitive '.css' for the unlikely '.htm'
                        key = "%s.%s" % (style_name, ext)
                        pygments_stylesheets[key] = style_info

            # cache this so we only need to do this once per dexy run...
            self.__class__.PYGMENTS_STYLESHEETS = pygments_stylesheets
        return self.__class__.PYGMENTS_STYLESHEETS

    def process_text(self, input_text):
        if self.artifact.ext in self.CHANGE_EXTENSIONS.keys():
            self.artifact.ext = self.CHANGE_EXTENSIONS[self.artifact.ext]

        self.notextile = self.artifact.args.has_key('notextile') and self.artifact.args['notextile']

        d_hash = {}
        a_hash = {}

        # The directory containing the document to be processed.
        doc_dir = os.path.dirname(self.artifact.name)

        # Get a list of subdirectories under this document's directory.
        subdirectories = [d for d in os.listdir(os.path.join(os.curdir, doc_dir)) if os.path.isdir(os.path.join(os.curdir, doc_dir, d))]

        for key, a in self.artifact.inputs().items():
            if not a.is_loaded() and not a.binary_output:
                self.log.debug("Loading artifact %s" % key)
                print "loading artifact", key
                a.load() # reload

            keys = a.relative_refs(self.artifact.name)

            # Do any special handling of data
            if a.ext == '.json':
                data = self.process_sort_json_data(a)
            elif self.notextile and a.ext == '.html':
                data = self.process_apply_notextile_html(a)
            else:
                data = a.data_dict

            for k in keys:
                # Avoid adding duplicate keys
                if a_hash.has_key(k):
                    next

                a_hash[k] = a

                if data.keys() == ['1']:
                    d_hash[k] = data['1']
                else:
                    d_hash[k] = data

        jinja_env_data = {
            'a' : a_hash,
            's' : self.artifact,
            'd' : d_hash,
            'f' : self,
            'subdirectories' : subdirectories,
            'pformat' : pprint.pformat,
            'WARN_AUTOGEN' : "This document is generated using Dexy (http://dexy.it). You should modify the source files, not this generated output."
        }

        # Intended to be all builtins that make sense to run within a document.
        python_builtins = dict((f.__name__, f) for f in self.PYTHON_BUILTINS)
        jinja_env_data.update(python_builtins)

        if USE_PYGMENTS:
            jinja_env_data['pygments'] = self.create_pygments_stylesheets()

        if self.artifact.args.has_key('jinjavars'):
            for k, v in self.artifact.args['jinjavars'].iteritems():
                if jinja_env_data.has_key(k):
                    raise Exception("""Please do not set a jinjavar for %s
                    as this conflicts with an object already in the jinja env:
                    %s""" % (k, ', '.join(jinja_env_data.keys())))
                jinja_env_data[k] = v

        if self.artifact.controller_args['globals']:
            for k, v in self.artifact.controller_args['globals'].iteritems():
                if jinja_env_data.has_key(k):
                    raise Exception("""Please do not set a global value for %s
                    as this conflicts with an object already in the jinja env:
                    %s""" % (k, ', '.join(jinja_env_data.keys())))
                jinja_env_data[k] = v

        env = self.setup_jinja_env()

        try:
            template = env.from_string(input_text)
            result = str(template.render(jinja_env_data))
        except TemplateSyntaxError as e:
            # do not try to parse UndefinedError here, the lineno in the stack
            # trace is a red herring.

            # TODO maybe can parse UndefinedError stacktrace for the content of
            # the undefined element and search for it in the original source?

            lineno_str = "line %s of " % e.lineno

            result = """
            There is a problem with %s

            There was a problem with %syour file %s

            %s

            ==================================================

            """ % (self.artifact.key, lineno_str, self.artifact.name, e.message)

            input_lines = self.artifact.input_text().splitlines()
            if e.lineno >= 3:
                result += "   ", input_lines[e.lineno-3]
            if e.lineno >= 2:
                result += "   ", input_lines[e.lineno-2]
            result += ">>>", input_lines[e.lineno-1]
            if len(input_lines) >= lineno:
                result += "   ", input_lines[e.lineno-0]
            if len(input_lines) >= (lineno + 1):
                result += "   ", input_lines[e.lineno+1]
            raise Exception(result)
        except Exception as e:
            result = """
            There is a problem with %s

            There was a problem with your file %s

            %s

            ==================================================

            """ % (self.artifact.key, self.artifact.name, e.message)
            if len(self.artifact.input_text().splitlines()) < 20:
                result += self.artifact.input_text()
            else:
                result += "Please check your file, you may have mistyped a variable name."

            if traceback.print_exc():
                result += """
                Here is a traceback which may have more information about the problem:

                %s""" % traceback.print_exc()
            raise Exception(result)
        return result


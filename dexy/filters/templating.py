from dexy.filter import DexyFilter
from dexy.plugin import TemplatePlugin
from jinja2 import FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from jinja2.exceptions import TemplateSyntaxError
from jinja2.exceptions import UndefinedError
import dexy.exceptions
import jinja2
import jinja2.ext
import os
import re
import traceback

class PassThroughWhitelistUndefined(jinja2.StrictUndefined):
    call_whitelist = ('link', 'section',)

    def wrap_arg(self, arg):
        if isinstance(arg, str):
            return "\"%s\"" % str(arg)
        else:
            return str(arg)

    def __call__(self, *args, **kwargs):
        name = self._undefined_name

        if name in self.call_whitelist:
            msgargs = {
                    'name' : name,
                    'argstring' : ",".join(self.wrap_arg(a) for a in args)
                    }
            return "{{ %(name)s(%(argstring)s) }}" % msgargs
        else:
            self._fail_with_undefined_error(*args, **kwargs)

class TemplateFilter(DexyFilter):
    """
    Base class for templating system filters such as JinjaFilter. Templating
    systems are used to make generated artifacts available within documents.

    Plugins are used to prepare content.
    """
    aliases = ['template']

    _settings = {
            'output' : True,
            'variables' : ("Variables to be made available to document.", {}),
            'vars' : ("Variables to be made available to document.", {}),
            'plugins' : ("List of plugins for run_plugins to use.", []),
            'skip-plugins' : ("List of plugins which run_plugins should not use.", [])
            }

    def template_plugins(self):
        """
        Returns a list of plugin classes for run_plugins to use.
        """
        if self.setting('plugins'):
            return [TemplatePlugin.create_instance(alias, self)
                        for alias in self.setting('plugins')]
        else:
            return [instance for instance in TemplatePlugin.__iter__(self)
                        if not instance.alias in self.setting('skip-plugins')]

    def run_plugins(self):
        env = {}
        for plugin in self.template_plugins():
            self.log_debug("Running template plugin %s" % plugin.__class__.__name__)
            new_env_vars = plugin.run()
            if new_env_vars is None:
                msg = "%s did not return any values"
                raise dexy.exceptions.InternalDexyProblem(msg % plugin.alias)
            if any(v in list(env.keys()) for v in new_env_vars):
                new_keys = ", ".join(sorted(new_env_vars))
                existing_keys = ", ".join(sorted(env))
                msg = "plugin class '%s' is trying to add new keys '%s', already have '%s'"
                raise dexy.exceptions.InternalDexyProblem(msg % (plugin.__class__.__name__, new_keys, existing_keys))
            env.update(new_env_vars)

        return env

    def template_data(self):
        plugin_output = self.run_plugins()

        template_data = {}

        for k, v in plugin_output.items():
            if not isinstance(v, tuple) or len(v) != 2:
                msg = "Template plugin '%s' must return a tuple of length 2." % k
                raise dexy.exceptions.InternalDexyProblem(msg)
            template_data[k] = v[1]

        return template_data

    def process_text(self, input_text):
        template_data = self.template_data()
        return input_text % template_data

class JinjaFilter(TemplateFilter):
    """
    Runs the Jinja templating engine.
    """
    aliases = ['jinja']

    _settings = {
            'block-start-string' : ("Tag to indicate the start of a block.", "{%"),
            'block-end-string' : ("Tag to indicate the start of a block.", "%}"),
            'variable-start-string' : ("Tag to indicate the start of a variable.", "{{"),
            'variable-end-string' : ("Tag to indicate the start of a variable.", "}}"),
            'comment-start-string' : ("Tag to indicate the start of a comment.", "{#"),
            'comment-end-string' : ("Tag to indicate the start of a comment.", "#}"),
            'changetags' : ("Automatically change from { to < based tags for .tex and .wiki files.", True),
            'jinja-path' : ("List of additional directories to pass to jinja loader.", []),
            'jinja-extensions' : ("List of jinja extensions to activate.", ['jinja2.ext.do']),
            'workspace-includes' : [".jinja"],
            'assertion-passed-indicator' : (
                "Extra text to return with a passed assertion.",
                ""),
            'filters' : (
                "List of template plugins to make into jinja filters.",
                ['assertions', 'highlight', 'head', 'tail', 'rstcode', 'stripjavadochtml',
                    'replacejinjafilters', 'bs4']
                )
            }

    _not_jinja_settings = (
            'changetags',
            'jinja-path',
            'workspace-includes',
            'filters',
            'assertion-passed-indicator',
            'jinja-extensions'
            )

    TEX_TAGS = {
            'block_start_string': '<%',
            'block_end_string': '%>',
            'variable_start_string': '<<',
            'variable_end_string': '>>',
            'comment_start_string': '<#',
            'comment_end_string': '#>'
            }

    LYX_TAGS = {
            'block_start_string': '<%',
            'block_end_string': '%>',
            'variable_start_string': '<<',
            'variable_end_string': '>>',
            'comment_start_string': '<<#',
            'comment_end_string': '#>>'
            }

    def setup_jinja_env(self, loader=None):
        env_attrs = {}

        for k, v in self.setting_values().items():
            underscore_k = k.replace("-", "_")
            if k in self.__class__._settings and not k in self._not_jinja_settings:
                env_attrs[underscore_k] = v

        env_attrs['undefined'] = PassThroughWhitelistUndefined

        if self.ext in (".tex", ".wiki") and self.setting('changetags'):
            if 'lyxjinja' in self.doc.filter_aliases:
                tags = self.LYX_TAGS
            else:
                tags = self.TEX_TAGS

            self.log_debug("Changing tags to latex/wiki format: %s" % ' '.join(tags))

            for underscore_k, v in tags.items():
                hyphen_k = underscore_k.replace("_", "-")
                if env_attrs[underscore_k] == self.__class__._settings[hyphen_k][1]:
                    self.log_debug("setting %s to %s" % (underscore_k, v))
                    env_attrs[underscore_k] = v

        if loader:
            env_attrs['loader'] = loader

        extensions = []
        for ext in self.setting('jinja-extensions'):
            self.log_debug("attempting to activate %s" % ext)
            if ext.startswith("jinja2.ext"):
                ref = jinja2.ext.__dict__[ext.lstrip("jinja2.ext")]
                extensions.append(ref)
        env_attrs['extensions'] = extensions

        debug_attr_string = ", ".join("%s: %r" % (k, v) for k, v in env_attrs.items())
        self.log_debug("creating jinja2 environment with: %s" % debug_attr_string)
        return jinja2.Environment(**env_attrs)

    def handle_jinja_exception(self, e, input_text, template_data):
        result = []
        input_lines = input_text.splitlines()

        # Try to parse line number from stack trace...
        if isinstance(e, UndefinedError) or isinstance(e, TypeError):
            # try to get the line number
            m = re.search(r"File \"<template>\", line ([0-9]+), in top\-level template code", traceback.format_exc())
            if m:
                e.lineno = int(m.groups()[0])
            else:
                print((traceback.format_exc()))
                e.lineno = 0
                self.log_warn("unable to parse line number from traceback")

        args = {
                'error_type' : e.__class__.__name__,
                'key' : self.key,
                'lineno' : e.lineno,
                'message' : getattr(e, 'message', str(e)),
                'name' : self.output_data.name,
                'workfile' : self.input_data.storage.data_file()
                }

        result.append("a %(error_type)s problem was detected: %(message)s" % args)

        if isinstance(e, UndefinedError):
            match_has_no_attribute = re.match("^'[\w\s\.]+' has no attribute '(.+)'$", e.message)
            match_is_undefined = re.match("^'([\w\s]+)' is undefined$", e.message)

            if match_has_no_attribute:
                undefined_object = match_has_no_attribute.groups()[0]
                match_lines = []
                for i, line in enumerate(input_lines):
                    if (".%s" % undefined_object in line) or ("'%s'" % undefined_object in line) or ("\"%s\"" % undefined_object in line):
                        result.append("line %04d: %s" % (i+1, line))
                        match_lines.append(i)
                if len(match_lines) == 0:
                    self.log_info("Tried to automatically find source of error: %s. Could not find match for '%s'" % (e.message, undefined_object))

            elif match_is_undefined:
                undefined_object = match_is_undefined.groups()[0]
                for i, line in enumerate(input_lines):
                    if undefined_object in line:
                        result.append("line %04d: %s" % (i+1, line))
            else:
                self.log_debug("Tried to automatically find where the error was in the template, but couldn't.")

        else:
            result.append("line %04d: %s" % (e.lineno, input_lines[e.lineno-1]))

        raise dexy.exceptions.UserFeedback("\n".join(result))

    def jinja_template_filters(self):
        filters = {}
        for alias in self.setting('filters'):
            self.log_debug("  creating filters from template plugin %s" % alias)
            template_plugin = TemplatePlugin.create_instance(alias)

            if not template_plugin.is_active():
                self.log_debug("    skipping %s - not active" % alias)
                continue
        
            methods = template_plugin.run()

            for k, v in methods.items():
                if not k in template_plugin.setting('no-jinja-filter'):
                    self.log_debug("    creating jinja filter for method %s" % k)
                    filters[k] = v[1]

        return filters

    def process(self):
        self.populate_workspace()

        wd = self.parent_work_dir()

        macro_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'macros'))
        dirs = ['.', wd, os.path.dirname(self.doc.name), macro_dir] + self.setting('jinja-path')
        self.log_debug("setting up jinja FileSystemLoader with dirs %s" % ", ".join(dirs))
        loader = FileSystemLoader(dirs)

        self.log_debug("setting up jinja environment")
        env = self.setup_jinja_env(loader=loader)
        self.log_debug("setting up jinja template filters")
        env.filters.update(self.jinja_template_filters())

        self.log_debug("initializing template")

        template_data = self.template_data()
        self.log_debug("jinja template data keys are %s" % ", ".join(sorted(template_data)))

        try:
            self.log_debug("about to create jinja template")
            template = env.get_template(self.work_input_filename())
            self.log_debug("about to process jinja template")
            template.stream(template_data).dump(self.output_filepath(), encoding="utf-8")
        except (TemplateSyntaxError, UndefinedError, TypeError) as e:
            self.log_debug("%s error while running jinja... %s" % (e.__class__.__name__, str(e)))
            try:
                self.log_debug("removing %s since jinja had an error" % self.output_filepath())
                os.remove(self.output_filepath())
            except os.error:
                pass
            self.handle_jinja_exception(e, str(self.input_data), template_data)
        except TemplateNotFound as e:
            msg = "Jinja couldn't find the template '%s', make sure this file is an input to %s" 
            msgargs = (e.message, self.doc.key)
            raise dexy.exceptions.UserFeedback(msg % msgargs)
        except Exception as e:
            try:
                self.log_debug("removing %s since jinja had an error" % self.output_filepath())
                os.remove(self.output_filepath())
            except os.error:
                pass
            self.log_debug(str(e))
            raise

from dexy.filter import DexyFilter
from dexy.plugins.templating_plugins import TemplatePlugin
from jinja2 import FileSystemLoader
from jinja2.exceptions import TemplateSyntaxError
from jinja2.exceptions import UndefinedError
from jinja2.exceptions import TemplateNotFound
import dexy.exceptions
import jinja2
import os
import re
import traceback

class TemplateFilter(DexyFilter):
    """
    Base class for templating system filters such as JinjaFilter. Templating
    systems are used to make generated artifacts available within documents.

    Plugins are used to prepare content.
    """
    ALIASES = ['template']
    FRAGMENT = False

    def template_plugins(self):
        """
        Returns a list of plugin classes for run_plugins to use.
        """
        if self.args().get('plugins'):
            return [TemplatePlugin.aliases[alias] for alias in self.args()['plugins']]
        else:
            return TemplatePlugin.plugins

    def run_plugins(self):
        env = {}
        for plugin_class in self.template_plugins():
            self.log.debug("Running template plugin %s" % plugin_class.__name__)
            plugin = plugin_class(self)
            new_env_vars = plugin.run()
            if any(v in env.keys() for v in new_env_vars):
                new_keys = ", ".join(sorted(new_env_vars))
                existing_keys = ", ".join(sorted(env))
                msg = "plugin class '%s' is trying to add new keys '%s', already have '%s'"
                raise dexy.exceptions.InternalDexyProblem(msg % (plugin_class.__name__, new_keys, existing_keys))
            env.update(new_env_vars)
        return env

    def process_text(self, input_text):
        template_data = self.run_plugins()
        return input_text % template_data

class JinjaFilter(TemplateFilter):
    """
    Runs the Jinja templating engine.
    """
    ALIASES = ['jinja']
    FRAGMENT = False

    def setup_jinja_env(self, loader=None):
        env_attrs = self.args().copy()

        # Remove jinja attrs not intended for env
        if env_attrs.has_key('vars'):
            del env_attrs['vars']
        if env_attrs.has_key('variables'):
            del env_attrs['variables']
        if env_attrs.has_key('ext'):
            del env_attrs['ext']
        if env_attrs.has_key('changetags'):
            changetags = env_attrs['changetags']
            del env_attrs['changetags']
        else:
            changetags = True

        env_attrs['undefined'] = jinja2.StrictUndefined

        if self.artifact.ext in (".tex", ".wiki") and changetags:
            env_attrs.setdefault('block_start_string', '<%')
            env_attrs.setdefault('block_end_string', '%>')
            env_attrs.setdefault('variable_start_string', '<<')
            env_attrs.setdefault('variable_end_string', '>>')
            env_attrs.setdefault('comment_start_string', '<#')
            env_attrs.setdefault('comment_end_string', '#>')

        if loader:
            env_attrs['loader'] = loader

        debug_attr_string = ", ".join("%s: %r" % (k, v) for k, v in env_attrs.iteritems())
        self.log.debug("creating jinja2 environment with: %s" % debug_attr_string)
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
                e.lineno = 0
                self.log.warn("unable to parse line number from traceback")

        args = {
                'error_type' : e.__class__.__name__,
                'key' : self.artifact.key,
                'lineno' : e.lineno,
                'message' : e.message,
                'name' : self.output().name,
                'workfile' : self.input().storage.data_file()
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
                    raise dexy.exceptions.InternalDexyProblem("Tried to find source of: %s. Could not find match for '%s'" % (e.message, undefined_object))

            elif match_is_undefined:
                undefined_object = match_is_undefined.groups()[0]
                for i, line in enumerate(input_lines):
                    if undefined_object in line:
                        result.append("line %04d: %s" % (i+1, line))
            else:
                raise dexy.exceptions.InternalDexyProblem("don't know how to match pattern: %s" % e.message)
        else:
            result.append("line %04d: %s" % (e.lineno, input_lines[e.lineno-1]))

        raise dexy.exceptions.UserFeedback("\n".join(result))

    def process(self):
        wd = self.setup_wd()
        dirs = ['.', wd, self.artifact.tmp_dir()]
        self.log.debug("setting up jinja FileSystemLoader with dirs %s" % ", ".join(dirs))
        loader = FileSystemLoader(dirs)

        self.log.debug("setting up jinja environment")
        env = self.setup_jinja_env(loader=loader)

        env.filters['pygmentize'] = dexy.plugins.templating_plugins.PygmentsStylesheet.highlight
        env.filters['rstcode'] = dexy.plugins.templating_plugins.RstCode.rstcode
        env.filters['indent'] = dexy.plugins.templating_plugins.JinjaFilters.indent
        env.filters['head'] = dexy.plugins.templating_plugins.JinjaFilters.head
        env.filters['javadoc2rst'] = dexy.plugins.templating_plugins.JavadocToRst.javadoc2rst
        if dexy.plugins.templating_plugins.PrettyPrintHtml.is_active():
            env.filters['prettify_html'] = dexy.plugins.templating_plugins.PrettyPrintHtml.prettify_html

        self.log.debug("initializing template")

        template_data = self.run_plugins()
        self.log.debug("jinja template data keys are %s" % ", ".join(sorted(template_data)))

        try:
            self.log.debug("about to create jinja template")
            template = env.get_template(self.input_filename())
            self.log.debug("about to process jinja template")
            template.stream(template_data).dump(self.output_filepath(), encoding="utf-8")
        except (TemplateSyntaxError, UndefinedError, TypeError) as e:
            if os.path.exists(self.output_filepath()):
                self.log.debug("removing %s since jinja had an error" % self.output_filepath())
                os.remove(self.output_filepath())
            self.handle_jinja_exception(e, self.input().as_text(), template_data)
        except TemplateNotFound as e:
            raise dexy.exceptions.UserFeedback("Jinja couldn't find the template '%s', make sure this file is an input to %s" % (e.message, self.artifact.doc.key))
        except Exception as e:
            if os.path.exists(self.output_filepath()):
                self.log.debug("removing %s since jinja had an error" % self.output_filepath())
                os.remove(self.output_filepath())
            self.log.debug(str(e))
            raise

from dexy.commands import InternalDexyProblem
from dexy.commands import UserFeedback
from dexy.dexy_filter import DexyFilter
from dexy.dexy_filter import DexyFilterException
from dexy.filters.templating_plugins import *
from jinja2.exceptions import TemplateSyntaxError
from jinja2.exceptions import UndefinedError
import jinja2
import re
import sys
import traceback

class TemplateFilter(DexyFilter):
    """
    Base class for templating system filters such as JinjaFilter. Templating
    systems are used to make generated artifacts available within documents.

    Plugins are used to prepare content.
    """
    ALIASES = ['template']
    FINAL = True
    PLUGINS = [
        ClippyHelperTemplatePlugin,
        DexyVersionTemplatePlugin,
        DexyRootTemplatePlugin,
        GlobalsTemplatePlugin,
        InputsTemplatePlugin,
        PrettyPrintJsonTemplatePlugin,
#        NavigationTemplatePlugin,
        PrettyPrinterTemplatePlugin,
        PygmentsStylesheetTemplatePlugin,
        PythonBuiltinsTemplatePlugin,
        PythonDatetimeTemplatePlugin,
        RegularExpressionsTemplatePlugin,
        SubdirectoriesTemplatePlugin,
        VariablesTemplatePlugin
        ]

    def run_plugins(self):
        env = {}
        for plugin_class in self.plugins():
            self.log.debug("Creating instance of %s" % plugin_class.__name__)
            plugin = plugin_class(self)
            new_env_vars = plugin.run()
            if any(v in env.keys() for v in new_env_vars):
                raise InternalDexyProblem("plugin class %s trying to add new keys %s, already have %s" % (plugin_class.__name__, u", ".join(new_env_vars.keys()), u", ".join(env.keys())))
            env.update(new_env_vars)
        return env

    def plugins(self):
        if self.artifact.args.has_key('plugins'):
            plugin_names = self.artifact.args['plugins']
            dict_items = sys.modules[self.__module__].__dict__
            return [dict_items[name] for name in plugin_names]
        else:
            return self.PLUGINS

    def process_text(self, input_text):
        """
        Overwrite this in your subclass, or, perhaps better, overwrite
        process() and write output directly to artifact file.
        """
        template_data = self.run_plugins()
        return input_text % template_data

class JinjaTextFilter(TemplateFilter):
    """
    Runs the Jinja templating engine. Uses process_text and returns text rather
    than writing to file.
    """
    ALIASES = ['jinjatext']

    def process_text(self, input_text):
        env = self.setup_jinja_env()
        template_data = self.run_plugins()
        try:
            template = env.from_string(input_text)
            return template.render(template_data)
        except (TemplateSyntaxError, UndefinedError, TypeError) as e:
            self.handle_jinja_exception(e, input_text, template_data)

    def setup_jinja_env(self):
        if self.artifact.ext == ".tex":
            self.log.debug("changing jinja tags to << >> etc. for %s" % self.artifact.key)
            env = jinja2.Environment(
                block_start_string = '<%',
                block_end_string = '%>',
                variable_start_string = '<<',
                variable_end_string = '>>',
                comment_start_string = '<#',
                comment_end_string = '#>',
                undefined = jinja2.StrictUndefined
                )
        else:
            env = jinja2.Environment(
                undefined = jinja2.StrictUndefined
            )
        return env

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
                raise InternalDexyProblem("Unable to parse line number from %s" % traceback.format_exc())

        args = {
                'key' : self.artifact.key,
                'lineno' : e.lineno,
                'message' : e.message,
                'name' : self.artifact.name,
                'workfile' : self.artifact.previous_artifact_filepath
                }

        result.append("A problem was detected: %(message)s" % args)

        if hasattr(self.artifact, 'doc') and self.artifact.doc.step > 1:
            result.append("Your file has been processed through other filters before going through jinja.")
            result.append("The working file sent to jinja is at %(workfile)s" % args)
            result.append("Line numbers refer to the working file, not your original file.")

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
                    raise InternalDexyProblem("Tried to find source of: %s. Could not find match for '%s'" % (e.message, undefined_object))

            elif match_is_undefined:
                undefined_object = match_is_undefined.groups()[0]
                for i, line in enumerate(input_lines):
                    if undefined_object in line:
                        result.append("line %04d: %s" % (i+1, line))
            else:
                raise InternalDexyProblem("don't know how to match pattern: %s" % e.message)
        else:
            result.append("line %04d: %s" % (e.lineno, input_lines[e.lineno-1]))

        raise UserFeedback("\n".join(result))

class JinjaFilter(JinjaTextFilter):
    """
    Runs the Jinja templating engine on your document to incorporate dynamic
    content.
    """
    ALIASES = ['jinja']
    TAGS = ['template']

    def process(self):
        self.log.debug("entering JinjaFilter, about to create jinja env")
        env = self.setup_jinja_env()
        self.log.debug("jinja env created. about to run plugins")
        template_data = self.run_plugins()
        try:
            self.log.debug("creating jinja template from input text")
            template = env.from_string(self.artifact.input_text())
            self.log.debug("about to process jinja template")
            template.stream(template_data).dump(self.artifact.filepath(), encoding="utf-8")
        except (TemplateSyntaxError, UndefinedError, TypeError) as e:
            self.handle_jinja_exception(e, self.artifact.input_text(), template_data)

class JinjaJustInTimeFilter(JinjaFilter):
    ALIASES = ['jinjajit']
    PLUGINS = [
        ClippyHelperTemplatePlugin,
        DexyVersionTemplatePlugin,
        GlobalsTemplatePlugin,
        InputsJustInTimeTemplatePlugin,
        PrettyPrintJsonTemplatePlugin,
        PrettyPrinterTemplatePlugin,
        PygmentsStylesheetTemplatePlugin,
        PythonBuiltinsTemplatePlugin,
        PythonDatetimeTemplatePlugin,
        RegularExpressionsTemplatePlugin,
        SimpleJsonTemplatePlugin,
        SubdirectoriesTemplatePlugin,
        VariablesTemplatePlugin
        ]

class WebsiteTemplateJinjaFilter(JinjaFilter):
    """
    Makes website-relevant tags available to a jinja-based website template.
    """
    ALIASES = ['ws']
    PLUGINS = [
        DexyVersionTemplatePlugin,
        GlobalsTemplatePlugin,
        NavigationTemplatePlugin,
        PrettyPrinterTemplatePlugin,
        PygmentsStylesheetTemplatePlugin,
        PythonBuiltinsTemplatePlugin,
        PythonDatetimeTemplatePlugin,
        RegularExpressionsTemplatePlugin,
        SubdirectoriesTemplatePlugin,
        VariablesTemplatePlugin
        ]

    def process(self):
        website_template = self.find_closest_parent('template')

        env = self.setup_jinja_env()
        template_data = self.run_plugins()
        template_data['page_content'] = self.artifact.input_text()

        try:
            template = env.from_string(website_template.output_text())
            template.stream(template_data).dump(self.artifact.filepath(), encoding="utf-8")
        except (TemplateSyntaxError, UndefinedError, TypeError) as e:
            self.handle_jinja_exception(e, website_template.output_text(), template_data)


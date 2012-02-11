from dexy.dexy_filter import DexyFilter
from dexy.dexy_filter import DexyFilterException
from dexy.filters.templating_plugins import *
from jinja2.exceptions import TemplateSyntaxError
from jinja2.exceptions import UndefinedError
import jinja2
import sys
import re
import traceback

class TemplateFilterException(DexyFilterException):
    pass

class JinjaFilterException(TemplateFilterException):
    pass

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
        GlobalsTemplatePlugin,
        InputsTemplatePlugin,
        PrettyPrinterTemplatePlugin,
        PygmentsStylesheetTemplatePlugin,
        PythonBuiltinsTemplatePlugin,
        RegularExpressionsTemplatePlugin,
        SubdirectoriesTemplatePlugin,
        VariablesTemplatePlugin
        ]

    def run_plugins(self):
        env = {}
        for plugin_class in self.plugins():
            plugin = plugin_class(self)
            new_env_vars = plugin.run()
            if any(v in env.keys() for v in new_env_vars):
                raise Exception("trying to add new keys %s, already have %s" % (u", ".join(new_env_vars.keys()), u", ".join(env.keys())))
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
            self.handle_jinja_exception(e)

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

    def handle_jinja_exception(self, e):
        result = []
        br = "=================================================="
        s = "    "

        if isinstance(e, UndefinedError) or isinstance(e, TypeError):
            # try to get the line number
            m = re.search(r"File \"<template>\", line ([0-9]+), in top\-level template code", traceback.format_exc())
            if m:
                e.lineno = int(m.groups()[0])
            else:
                raise Exception("Unable to parse line number from %s" % traceback.format_exc())

        result.append("""There is a problem with %(key)s
        \nA problem was detected at line %(lineno)s of %(workfile)s
        """ % {'key' : self.artifact.key, 'lineno' : e.lineno, 'workfile' : self.artifact.previous_artifact_filepath })

        if isinstance(e, UndefinedError):
            result.append("WARNING: line number may not be accurate, check elsewhere in your file if the excerpt does not contain the undefined item from the stack trace.")

        input_lines = self.artifact.input_text().splitlines()

        result.append(br)

        # print context before line with problem, if available
        if e.lineno >= 3:
            result.append(s + input_lines[e.lineno-3])
        if e.lineno >= 2:
            result.append(s + input_lines[e.lineno-2])

        # this is the line that has the problem
        result.append(">>> %s" % input_lines[e.lineno-1])

        # print context after line with problem, if available
        if len(input_lines) > e.lineno:
            result.append(s + input_lines[e.lineno-0])
        if len(input_lines) > (e.lineno + 1):
            result.append(s + input_lines[e.lineno+1])

        result.append(br)
        result.append("The error is: %s" % e.message)

        result.append(traceback.format_exc())

        # Exception constructors don't like unicode, so print error messsage to
        # STDOUT then raise an exception.
        print u"\n".join(result)
        raise JinjaFilterException("An error has occurred while processing %s" % self.artifact.key)

class JinjaFilter(JinjaTextFilter):
    """
    Runs the Jinja templating engine on your document to incorporate dynamic
    content.
    """
    ALIASES = ['jinja']
    TAGS = ['template']

    def process(self):
        env = self.setup_jinja_env()
        template_data = self.run_plugins()
        try:
            template = env.from_string(self.artifact.input_text())
            template.stream(template_data).dump(self.artifact.filepath(), encoding="utf-8")
        except (TemplateSyntaxError, UndefinedError, TypeError) as e:
            self.handle_jinja_exception(e)

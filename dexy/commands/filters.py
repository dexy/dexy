from dexy.commands.utils import template_text
from pygments import highlight
import pygments.formatters
from pygments.lexers import PythonLexer
import dexy.filter
import inspect

extra_nodoc_aliseas = ('-',)

def filters_command(
        alias="", # Print docs for this filter.
        example=False, # Whether to run included examples (slower).
        nocolor=False, # Skip syntax highlighting if showing source code.
        source=False, # Print source code of filter.
        versions=False # Print the installed version of external software (slower).
        ):
    """
    Prints list of available filters or docs for a particular filter.
    """
    if alias:
        help_for_filter(alias, example, source, nocolor)
    else:
        list_filters(versions)

def help_for_filter(alias, run_example, show_source, nocolor):
    instance = dexy.filter.Filter.create_instance(alias)

    print "aliases: %s" % ", ".join(instance.aliases)
    print ''
    print inspect.getdoc(instance.__class__)
    print ''

    print('settings:')
    for k in sorted(instance._instance_settings):
        if not k in dexy.filter.Filter.nodoc_settings:
            tup = instance._instance_settings[k]
            setting_s = "  %s: %s (default value: %s)"
            print setting_s % (k, inspect.cleandoc(tup[0]).replace("\n", " "), tup[1])

    examples = instance.setting('examples')
    example_templates = dict((alias, dexy.template.Template.create_instance(alias))
                                    for alias in examples)

    if examples:
        print ''
        print "Examples for this filter:"
        for alias in examples:
            template = example_templates[alias]
            print ''
            print "  %s" % alias
            print "            %s" % inspect.getdoc(template.__class__)

        if run_example:
            for alias in examples:
                template = example_templates[alias]
                print ''
                print "Running example: %s" % template.setting('help')
                print ''
                print ''
                print template_text(template)

    print ''
    print "For online docs see http://dexy.it/docs/filters/%s" % alias

    if show_source:
        print ''
        source_code = inspect.getsource(instance.__class__)
        if nocolor:
            print source_code
        else:
            formatter = pygments.formatters.TerminalFormatter()
            lexer = PythonLexer()
            print highlight(source_code, lexer, formatter)

def list_filters(versions):
        print "Installed filters:"
        for filter_instance in dexy.filter.Filter:
            # Should we show this filter?
            no_aliases = not filter_instance.setting('aliases')
            no_doc = filter_instance.setting('nodoc')
            not_dexy = not filter_instance.__class__.__module__.startswith("dexy.")
            exclude = filter_instance.alias in extra_nodoc_aliseas

            if no_aliases or no_doc or not_dexy or exclude:
                continue

            # generate version message
            if versions:
                if hasattr(filter_instance, 'version'):
                    version = filter_instance.version()
                    if version:
                        version_message = "Installed version: %s" % version
                    else:
                        msg = "'%s' failed, filter may not be available."
                        msgargs = filter_instance.version_command()
                        version_message = msg % msgargs
                else:
                    version_message = ""


            filter_help = "  " + filter_instance.alias + \
                    " : " + filter_instance.setting('help').splitlines()[0]

            if versions and version_message:
                filter_help += " %s" % version_message

            print filter_help

        print ''
        print inspect.cleandoc("""For more information about a particular filter,
        use the -alias flag and specify the filter alias.""")

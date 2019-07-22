from dexy.commands.utils import template_text
from pygments import highlight
from pygments.lexers import PythonLexer
import dexy.filter
import inspect
import pygments.formatters

extra_nodoc_aliases = ('-',)

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

    print('')
    print(instance.setting('help'))

    print('')
    print("aliases: %s" % ", ".join(instance.setting('aliases')))
    print("tags: %s" % ", ".join(instance.setting('tags')))
    print('')

    print("Converts from file formats:")
    for ext in instance.setting('input-extensions'):
        print("   %s" % ext)
    print('')

    print("Converts to file formats:")
    for ext in instance.setting('output-extensions'):
        print("   %s" % ext)
    print('')

    print('Settings:')
    for k in sorted(instance._instance_settings):
        if k in dexy.filter.Filter.nodoc_settings:
            continue
        if k in ('aliases', 'tags'):
            continue

        tup = instance._instance_settings[k]
        print("    %s" % k)

        for line in inspect.cleandoc(tup[0]).splitlines():
            print("        %s" % line)

        print("        default value: %s" % tup[1])
        print('')

    examples = instance.setting('examples')
    example_templates = {}
    for alias in examples:
        try:
            template_instance = dexy.template.Template.create_instance(alias)
            example_templates[alias] = template_instance
        except dexy.exceptions.InactivePlugin:
            pass

    if examples:
        print('')
        print("Examples for this filter:")
        for alias, template in example_templates.items():
            print('')
            print("  %s" % alias)
            print("            %s" % inspect.getdoc(template.__class__))

        if run_example:
            for alias, template in example_templates.items():
                print('')
                print('')
                print("Running example: %s" % template.setting('help'))
                print('')
                print('')
                print(template_text(template))

    print('')
    print("For online docs see http://dexy.it/filters/%s" % alias)
    print('')
    print("If you have suggestions or feedback about this filter,")
    print("please contact info@dexy.it")
    print('')

    if show_source:
        print('')
        source_code = inspect.getsource(instance.__class__)
        if nocolor:
            print(source_code)
        else:
            formatter = pygments.formatters.TerminalFormatter()
            lexer = PythonLexer()
            print(highlight(source_code, lexer, formatter))

def list_filters(versions):
        print("Installed filters:")
        for filter_instance in dexy.filter.Filter:
            # Should we show this filter?
            no_aliases = not filter_instance.setting('aliases')
            no_doc = filter_instance.setting('nodoc')
            not_dexy = not filter_instance.__class__.__module__.startswith("dexy.")
            exclude = filter_instance.alias in extra_nodoc_aliases

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

            print(filter_help)

        print('')
        print("For more information about a particular filter,")
        print("use the -alias flag and specify the filter alias.")
        print('')


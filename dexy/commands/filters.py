import inspect
from dexy.commands.utils import template_text
from dexy.utils import s
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
import dexy.filter

def filter_command(
        alias="", # If a filter alias is specified, more detailed help for that filter is printed.
        example=False, # Whether to run examples
        nocolor=False, # When source = True, whether to omit syntax highlighting
        showall=False, # Whether to show all filters, including those which need missing software, implies versions=True
        showmissing=False, # Whether to just show filters missing external software, implies versions=True
        space=False, # Whether to add extra spacing to the output for extra readability
        source=False, # Whether to include syntax-highlighted source code when displaying an indvidual filter
        versions=False # Whether to check the installed version of external software required by filters, slower
        ):
    """
    Information about available dexy filters.
    """
    print filters_text(**locals())

def filters_command(
        alias="", # If a filter alias is specified, more detailed help for that filter is printed.
        example=False, # Whether to run examples
        nocolor=False, # When source = True, whether to omit syntax highlighting
        showall=False, # Whether to show all filters, including those which need missing software, implies versions=True
        showmissing=False, # Whether to just show filters missing external software, implies versions=True
        space=False, # Whether to add extra spacing to the output for extra readability
        source=False, # Whether to include syntax-highlighted source code when displaying an indvidual filter
        versions=False # Whether to check the installed version of external software required by filters, slower
        ):
    """
    Information about available dexy filters.
    """
    print filters_text(**locals())

def filters_text(
        alias="", # If a filter alias is specified, more detailed help for that filter is printed.
        example=False, # Whether to run examples
        nocolor=False, # When source = True, whether to omit syntax highlighting
        showall=False, # Whether to show all filters, including those which need missing software, implies versions=True
        showmissing=False, # Whether to just show filters missing external software, implies versions=True
        space=False, # Whether to add extra spacing to the output for extra readability
        source=False, # Whether to include syntax-highlighted source code when displaying an indvidual filter
        versions=False # Whether to check the installed version of external software required by filters, slower
        ):

    SETTING_STRING = "  %s: %s (default value: %s)"
    if len(alias) > 0:
        # We want help on a particular filter
        instance = dexy.filter.Filter.create_instance(alias)
        text = []
        text.append("aliases: %s" % ", ".join(instance.aliases))
        text.append("")
        text.append(inspect.getdoc(instance.__class__))
        text.append("")
        text.append("dexy-level settings:")
        for k in sorted(instance._instance_settings):
            if not k in dexy.filter.Filter.nodoc_settings and k in dexy.filter.Filter._settings:
                tup = instance._instance_settings[k]
                text.append(SETTING_STRING % (k, tup[0], tup[1]))

        text.append("")
        text.append("filter-specific settings:")
        for k in sorted(instance.filter_specific_settings()):
            tup = instance._instance_settings[k]
            text.append(SETTING_STRING % (k, tup[0], tup[1]))

        templates = instance.templates()
        if len(templates) > 0:
            text.append("")
            text.append("Templates which use this filter:")
            for t in templates:
                text.append("")
                text.append("  %s" % t.aliases[0])
                text.append("            %s" % dexy.utils.getdoc(t.__class__))

            if example:
                for t in templates:
                    aliases = [k for k, v in dexy.template.Template.plugins.iteritems() if v == t]
                    if t.__module__ == "dexy_filter_examples":
                        text.append('')
                        text.append("Running example: %s" % s(t.__doc__))
                        text.append('')
                        text.append('')
                        text.append(template_text(alias=aliases[0]))
                        text.append('')
        text.append("")
        text.append("For online docs see http://dexy.it/docs/filters/%s" % alias)
        if source:
            text.append("")
            source_code = inspect.getsource(instance.__class__)
            if nocolor:
                text.append(source_code)
            else:
                formatter = TerminalFormatter()
                lexer = PythonLexer()
                text.append(highlight(source_code, lexer, formatter))
        return "\n".join(text)

    else:
        text = []

        text.append("Available filters:")
        for filter_instance in dexy.filter.Filter:
            if showall:
                skip = False
            else:
                no_aliases = not filter_instance.setting('aliases')
                no_doc = filter_instance.setting('nodoc')
                not_dexy = not filter_instance.__class__.__module__.startswith("dexy.")
                exclude = filter_instance.alias in ('-')
                skip = no_aliases or no_doc or not_dexy or exclude

            if (versions or showmissing or showall) and not skip:
                if hasattr(filter_instance, 'version'):
                    version = filter_instance.version()
                else:
                    version = None
                no_version_info_available = (version is None)
                if no_version_info_available:
                    version_message = ""
                    if showmissing:
                        skip = True
                elif version:
                    version_message = "Installed version: %s" % version
                    if showmissing:
                        skip = True
                else:
                    if not (showmissing or showall):
                        skip = True
                    version_message = "'%s' failed, filter may not be available." % filter_instance.version_command()

            if not skip:
                filter_help = "  " + filter_instance.alias + " : " + filter_instance.setting('help').splitlines()[0]
                if (versions or showmissing or (showall and not version)):
                    filter_help += " %s" % version_message
                text.append(filter_help)

        text.append("\nFor more information about a particular filter, use the -alias flag and specify the filter alias.")
        if space:
            sep = "\n\n"
        else:
            sep = "\n"
        return sep.join(text)

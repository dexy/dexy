from dexy.commands.utils import print_indented
from dexy.commands.utils import print_rewrapped
import dexy.reporter

def reporters_command(
        alias=False, # Print detailed information about the specified reporter.
        simple=False, # Only print report aliases, without other information.
        ):
    """
    List available reports which dexy can run.
    """
    if simple:
        for reporter in dexy.reporter.Reporter:
            print(reporter.alias)

    elif alias:
        nodoc_settings = ('aliases', 'help',)

        reporter = dexy.reporter.Reporter.create_instance(alias)

        print_indented("%s Reporter" % reporter.__class__.__name__)
        print('')

        print_indented("settings:")
        print('')
        for name in sorted(reporter._instance_settings):
            if name in nodoc_settings:
                continue

            docs, default_value = reporter._instance_settings[name]
            print_indented(name, 2)
            print_rewrapped(docs, 4)
            print_indented("(default: %r)" % default_value, 4)
            print('')

        reporter.help()

        print('')

    else:
        FMT = "%-15s %-9s %s"
    
        print(FMT % ('alias', 'default', 'info'))
        for reporter in dexy.reporter.Reporter:
            help_text = reporter.setting('help').splitlines()[0]
            default_text = reporter.setting('default') and 'true' or 'false'
            print(FMT % (reporter.alias, default_text, help_text))

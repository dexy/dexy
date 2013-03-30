import dexy.reporter

def reporters_command(
        ):
    """
    List available reporters.
    """
    FMT = "%-15s %-9s %s"

    print FMT % ('alias', 'default', 'info')
    for reporter in dexy.reporter.Reporter:
        help_text = reporter.help().splitlines()[0]
        default_text = reporter.setting('default') and 'true' or 'false'
        print FMT % (reporter.alias, default_text, help_text)

def reports_command():
    reporters_command()

import dexy.reporter

def reporters_command(
        ):
    """
    List available reporters.
    """
    FMT = "%-10s %-20s %s"

    if dexy.reporter.Reporter:
        print FMT % ('ALIAS', 'DIRECTORY', 'INFO')

#    for k in sorted(dexy.reporter.Reporter.aliases):
#        reporter_class = dexy.reporter.Reporter.aliases[k]
#        reports_dir = reporter_class.REPORTS_DIR or ''
#        print FMT % (k, reports_dir, getdoc(reporter_class))


def reports_command():
    def sort_key(k):
        return k.__name__

    report_classes = sorted(dexy.reporter.Reporter.plugins, key=sort_key)
    for klass in report_classes:
        print "%s: %s" % (klass.__name__, ", ".join(klass.ALIASES))

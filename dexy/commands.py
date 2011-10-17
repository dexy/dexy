from dexy.constants import Constants
import cProfile
from dexy.controller import Controller
from dexy.version import Version
from modargs import args
import dexy.introspect
import os
import shutil
import sys

MOD = sys.modules[__name__]
PROG = 'dexy'
S = "   "

def run():
    args.parse_and_run_command(sys.argv[1:], MOD, default_command=Constants.DEFAULT_COMMAND)

def dexy_command(
        artifactclass=Constants.DEFAULT_ACLASS, # Name of class to use for artifacts
        artifactsdir=Constants.DEFAULT_ADIR, # Location of directory in which to store artifacts
        config=Constants.DEFAULT_CONFIG, # Name to use for configuration file
        danger=False, # Allow running remote files
        dbclass=Constants.DEFAULT_DBCLASS, # Name of database class to use
        dbfile=Constants.DEFAULT_DBFILE, # Name of the database file (it lives in the logs dir)
        directory=".", # The directory to process, you can just process a subdirectory of your project
        exclude="", # Directories to exclude from dexy processing
        filters=False, # DEPRECATED just to catch people who use the old dexy --filters syntax
        globals="DEXY_VERSION=%s" % Version.VERSION, # Global values to make available within dexy documents, should be KEY=VALUE pairs separated by spaces.
        help=False, # DEPRECATED just to catch people who use the old dexy --help syntax
        ignore=False, # Whether to ignore nonzero exit status or raise an error - may not be supported by all filters
        local=False, # Use cached local copies of remote URLs, faster but might not be up to date
        logfile=Constants.DEFAULT_LFILE, # Name of log file
        logsdir=Constants.DEFAULT_LDIR, # Location of directory in which to store logs
        profmem=False, # Whether to profile memory (slows Dexy down a lot, use for debugging only)
        recurse=True, # Whether to recurse into subdirectories when running Dexy
        reporters=False, # DEPRECATED just to catch people who use the old dexy --reporters syntax
        reports=Constants.DEFAULT_REPORTS, # Reports to be run after dexy runs
        reset=False, # Whether to purge existing artifacts and logs before running Dexy
        version=False, # DEPRECATED just to catch people who use the old dexy --version syntax
        zzzzz=True # remove me - just here to help alphabetical sorting during dev
    ):
    """
    Actually runs dexy.
    """
    ### @export "dexy-command-body"
    if not check_setup():
        print "Please run '%s setup' first to create the directories dexy needs to work with" % PROG
        sys.exit(1)

    if reset:
        reset_command(logsdir=logsdir, artifactsdir=artifactsdir)

    # catch deprecated arguments
    if help or version or reporters or filters:
        print "the command syntax has changed, please type 'dexy help' for help"
        sys.exit(1)

    controller = run_dexy(locals())
    print "processing batch", controller.batch_id, "is complete"
    reports_command(reports=reports, logsdir=logsdir, controller=controller)

def run_dexy(args):
    # validate args and do any conversions required
    args['globals'] = dict([g.split("=") for g in args['globals'].split()])
    controller = Controller(args)
    controller.run()
    return controller

def profile_command(
        reports="ProfileReporter",
        **kw # Accepts additional keyword arguments for the 'dexy' command
    ):
    """
    Runs dexy using cProfile to do time-based profiling. Uses ProfileReport
    (the only report enabled by default) to present profiling information.
    Other reports can be specified, report time is not included in profiling.
    Running ProfileReport each time ensures that profiling data is stored in
    sqlite database for comparison (a 'dexy reset' will delete this database).
    """
    dexy_fn = args.function_for(dexy.commands, "dexy")
    defaults = args.determine_kwargs(dexy_fn)
    defaults.update(kw)
    defaults['profile'] = True
    cProfile.runctx("run_dexy(args)", globals(), {'args' : defaults}, "logs/dexy.prof")
    reports_command(reports=reports)

def profreports_command(**kw):
    """
    Runs reports using cProfile to do time-based profiling.
    """
    pass

def check_setup(logsdir=Constants.DEFAULT_LDIR, artifactsdir=Constants.DEFAULT_ADIR):
    return os.path.exists(logsdir) and os.path.exists(artifactsdir)

def setup_command(logsdir=Constants.DEFAULT_LDIR, artifactsdir=Constants.DEFAULT_ADIR, logfile=Constants.DEFAULT_LFILE, showhelp=True):
    """
    Creates directories to hold artifacts and logs. Dexy needs these
    directories and they aren't created automatically as a precaution against
    accidentally running dexy somewhere you didn't mean to.
    """
    if check_setup():
        print "Dexy is already set up. Run 'reset' if you want to reset everything."
    else:
        if not os.path.exists(logsdir):
            os.mkdir(logsdir)
        if not os.path.exists(artifactsdir):
            os.mkdir(artifactsdir)

        if showhelp:
            print "Ok, we've created directories called %s and %s." % (logsdir, artifactsdir)
            if os.path.exists(Constants.DEFAULT_CONFIG):
                print "You are now ready to run dexy!  If you have problems, please check the"
                print "log file at %s/%s for clues." % (logsdir, logfile)
                print "Online help is available from dexy.it/help"
            else:
                print "You are almost ready to run dexy! You just need to create a config file,"
                print "check out the tutorials dexy.it/docs/tutorials if you aren't sure how."
                print "You can type '%s help -on %s' (without quotes) for help running dexy" % (PROG, Constants.DEFAULT_COMMAND)
                print "or visit dexy.it/help for more resources"

def cleanup_command(logsdir=Constants.DEFAULT_LDIR, artifactsdir=Constants.DEFAULT_ADIR):
    """
    Removes all dexy-generated content.
    """
    # Dexy itself should put all generated content into either artifacts or logs.
    # Reports may create files in other locations, but they should track where
    # they do this and be able to purge them.
    purge_artifacts(remake=False, artifactsdir=artifactsdir)
    purge_logs(logsdir=logsdir)
    #purge_reports()

def reset_command(logsdir=Constants.DEFAULT_LDIR, artifactsdir=Constants.DEFAULT_ADIR):
    """
    Runs cleanup and then setup to completely reset your dexy environment.
    """
    cleanup_command(logsdir=logsdir, artifactsdir=artifactsdir)
    setup_command(logsdir=logsdir, artifactsdir=artifactsdir, showhelp=False)

def purge_artifacts(remake=True, artifact_class=None, artifactsdir=Constants.DEFAULT_ADIR):
    shutil.rmtree(artifactsdir)
    if remake:
        os.mkdir(artifactsdir)

    if hasattr(artifact_class, 'purge'):
        artifact_class.purge()

def purge_logs(logsdir=Constants.DEFAULT_LDIR):
    shutil.rmtree(logsdir)

def purge_reports():
    raise Exception("needs more safety checks")
    reports_dirs = dexy.introspect.reports_dirs()
    for d in reports_dirs:
        if d and os.path.exists(d):
            print "purging contents of %s" % d
            shutil.rmtree(d)

def help_command(on=False):
    args.help_command(PROG, MOD, Constants.DEFAULT_COMMAND, on)

def help_text(on=False):
    return args.help_text(PROG, MOD, Constants.DEFAULT_COMMAND, on)

def version_command():
    """Print the current version."""
    print "%s version %s" % (PROG, Version.VERSION)

def filters_command():
    """Lists currently available dexy filters."""
    print filters_text()

def filters_text():
    filters = dexy.introspect.filters()
    text = []
    for k in sorted(filters.keys()):
        klass = filters[k]
        version = klass.version()
        if (version is None) or version:
            text.append("\n%s : %s" % (k, klass.__name__))
            if klass.executable():
                text.append(S + "calls '%s'" % klass.executable())
                if version:
                    text.append(S + version + " detected")
            if klass.__doc__:
                text.append(S + klass.__doc__.strip())
    return "\n".join(text) + "\n"

def reporters_command():
    """Lists currently available dexy reporters."""
    print reporters_text(Constants.NULL_LOGGER)

def reporters_text(log):
    text = []
    reporters = dexy.introspect.reporters(log)
    for reporter_name in sorted(reporters.keys()):
        r = reporters[reporter_name]
        text.append("\n" + r.__name__)

        if r.__doc__:
            text.append(S + r.__doc__)
        else:
            text.append(S + "no documentation available")

        if r.REPORTS_DIR:
            text.append(S + "any generated reports will be saved in %s" % r.REPORTS_DIR)

    return "\n".join(text) + "\n"

def report_command(**kwargs):
    """
    Alias for reports.
    """
    reports_command(kwargs)

def reports_command(
        aclass=Constants.DEFAULT_ACLASS, # What artifact class to use (must correspond to artifact class used by batch id)
        controller=False, # can pass the just-run controller instance to save having to load some data from disk which is already in memory
        batchid=False, # What batch id to run reports for. Leave false to run the most recent batch available (recommended).
        logsdir=Constants.DEFAULT_LDIR, # The location of the logs directory.
        reports="OutputReporter RunReporter LongOutputReporter OutputTgzReporter" # The class names for all reports to be run.
    ):
    """
    Runs reports to present Dexy output.
    """

    # convert False (needed for CLI) to None (expected by constructor)
    if not batchid:
        batchid = None
    if not controller:
        controller = None

    if isinstance(reports, str):
        reports = reports.split()
    elif isinstance(reports, bool):
        # either was set to False, or an empty string evaluated to True
        # either way we don't want to run any reports.
        reports = []
    reporters = dexy.introspect.reporters()

    for r in reports:
        report_class = reporters[r]
        print "running", r
        reporter = report_class(
                artifact_class=aclass,
                batch_id=batchid,
                controller=controller,
                logsdir=logsdir
            )

        reporter.load_batch_artifacts()
        reporter.run()

def it_command(**kwargs):
    dexy_command(kwargs)

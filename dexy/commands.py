from dexy.constants import Constants
from dexy.controller import Controller
from dexy.version import Version
from modargs import args
import copy
import cProfile
import datetime
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
        artifactclass=Constants.DEFAULT_ACLASS, # name of class to use for artifacts
        artifactsdir=Constants.DEFAULT_ADIR, # location of directory in which to store artifacts
        config=Constants.DEFAULT_CONFIG, # name to use for configuration file
        danger=False, # whether to allow running remote files
        dbclass=Constants.DEFAULT_DBCLASS, # name of database class to use
        dbfile=Constants.DEFAULT_DBFILE, # name of the database file (it lives in the logs dir)
        directory=".", # the directory to process, you can just process a subdirectory of your project
        disabletests=False, # Whether to disable the dexy 'test' filter
        dryrun=False, # if True, just parse config and print batch info, don't run dexy
        exclude="", # directories to exclude from dexy processing
        filters=False, # DEPRECATED just to catch people who use the old dexy --filters syntax
        globals="DEXY_VERSION=%s" % Version.VERSION, # global values to make available within dexy documents, should be KEY=VALUE pairs separated by spaces
        help=False, # DEPRECATED just to catch people who use the old dexy --help syntax
        hashfunction='md5', # What hash function to use, set to crc32 or adler32 for more speed, less reliability
        ignore=False, # whether to ignore nonzero exit status or raise an error - may not be supported by all filters
        local=False, # use cached local copies of remote URLs, faster but might not be up to date
        logfile=Constants.DEFAULT_LFILE, # name of log file
        logsdir=Constants.DEFAULT_LDIR, # location of directory in which to store logs
        nocache=False, # whether to force artifacts to run even if there is a matching file in the cache
        output=False, # Shortcut to mean "I just want the OutputReporter, nothing else"
        recurse=True, # whether to recurse into subdirectories when running Dexy
        reporters=False, # DEPRECATED just to catch people who use the old dexy --reporters syntax
        reports=Constants.DEFAULT_REPORTS, # reports to be run after dexy runs, enclose in quotes and separate with spaces
        reset=False, # whether to purge existing artifacts and logs before running Dexy
        setup=False, # DEPRECATED just to catch people who use the old dexy --setup syntax
        strictinherit=False, # set to true if you want 'allinputs' to only reference items in same dir or a subdir
        version=False # DEPRECATED just to catch people who use the old dexy --version syntax
    ):
    """
    Runs Dexy, by processing your .dexy configuration file and running content
    through the filters you have specified. Results are cached in the
    artifacts/ directory but are presented in a more usable format by
    reporters. Basic reports are run automatically but you can specify
    additional reports. Type 'dexy reporters' for a list of available reporters.

    If your project is large, then running reports will start to take up a lot
    of time, so you should specify only the reports you really need. You can
    always run more reports after a batch has finished running (you can run
    historical reports as far back as the last time you cleared out your
    artifacts cache with a 'dexy reset' or similar).

    After running Dexy, the output/ directory will hold what dexy thinks are
    the most important generated files (with pretty filenames), the output-long
    directory will hold all of your generated files (with ugly filenames), and
    the logs/ directory will hold the basic dexy.log logfile and also a more
    colorful and descriptive HTML log file in logs/run-latest/. Please look at
    these logfiles to learn more about how dexy works, and if you run into
    problems the dexy.log file might provide clues as to what has gone wrong.

    Your original files will be copied to logs/source-batch-00001/ by the
    SourceReporter (enabled by default). Each time you run dexy, your source
    code files will be copied so you have a mini-version history. (You can also
    use the 'dexy history' command to get a history for a given file, and you
    can run the SourceReporter again at any time to restore a given batch's
    source files.)

    If you run into trouble, visit http://dexy.it/help
    """
    ### @export "dexy-command-check-setup"
    if not check_setup():
        print "Please run '%s setup' first to create the directories dexy needs to work with" % PROG
        sys.exit(1)

    ### @export "dexy-command-process-args"
    if reset:
        reset_command(logsdir=logsdir, artifactsdir=artifactsdir)

    if output:
        if not reports == Constants.DEFAULT_REPORTS:
            raise Exception("if you pass --output you can't also modify reports! pick 1!")
        reports = "Output"

    # catch deprecated arguments
    if help or version or reporters or filters:
        print "the command syntax has changed, please type 'dexy help' for help"
        sys.exit(1)

    controller = run_dexy(locals())
    if not dryrun:
        reports_command(reports=reports, logsdir=logsdir, controller=controller)

def run_dexy(args):
    # validate args and do any conversions required
    args['globals'] = dict([g.split("=") for g in args['globals'].split()])
    args['exclude'] = [x.strip("/") for x in args['exclude'].split()]
    controller = Controller(args)
    controller.run()
    return controller

def profile_command(
        reports="ProfileReporter",
        n=1, # How many times to run dexy for profiling.
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

    locals_for_run_dexy = {'args' : defaults}

    logs_dir = kw.has_key("logsdir") and kw['logsdir'] or Constants.DEFAULT_LDIR
    prof_file = os.path.join(logs_dir, "dexy.prof")

    report_kwargs = {}
    if kw.has_key('artifactclass'):
        report_kwargs['artifactclass'] = kw['artifactclass']

    for i in xrange(n):
        print "===== run %s of %s =====" % (i+1, n)
        cProfile.runctx("run_dexy(args)", globals(), copy.deepcopy(locals_for_run_dexy), prof_file)
        reports_command(reports=reports, **report_kwargs)

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
            print
            print "Ok, we've created directories called %s and %s." % (logsdir, artifactsdir)
            if os.path.exists(Constants.DEFAULT_CONFIG):
                print "You are now ready to run dexy!  If you have problems,"
                print "please check the log file at %s/%s for clues." % (logsdir, logfile)
                print "Online help is available from dexy.it/help"
            else:
                print "You are almost ready to run dexy! You just need to create a config file,"
                print "check out the tutorials dexy.it/docs/tutorials if you aren't sure how."
                print "You can type '%s help -on %s' (without quotes) for help running dexy" % (PROG, Constants.DEFAULT_COMMAND)
                print "or visit dexy.it/help for more resources"
            print

def cleanup_command(logsdir=Constants.DEFAULT_LDIR, artifactsdir=Constants.DEFAULT_ADIR):
    """
    Removes all dexy-generated content.
    """
    # Dexy itself should put all generated content into either artifacts or logs.
    # Reports may create files in other locations, but they should track where
    # they do this and be able to purge them.
    purge_artifacts(remake=False, artifactsdir=artifactsdir)
    purge_logs(logsdir=logsdir)
    purge_reports()

def history_command(
        filename=None,
        logsdir=Constants.DEFAULT_LDIR,
        artifactsdir=Constants.DEFAULT_ADIR,
        dbclass=Constants.DEFAULT_DBCLASS,
        dbfile=Constants.DEFAULT_DBFILE
        ):
    """
    Returns a list of available versions of the file. This must be run from the
    dexy project root.
    """
    db = dexy.utils.get_db(dbclass, dbfile=dbfile, logsdir=logsdir)
    versions = {}
    for row in db.all():
        key = row['key']
        batch_id = int(row['batch_id'])
        if key == filename and not versions.has_key(batch_id):
            versions[batch_id] = row

    if len(versions) > 0:
        print
        print "Dexy found these versions of %s:" % filename
        for b in sorted(versions.keys()):
            row = versions[b]
            artifact_file = os.path.join(artifactsdir, "%s%s" % (row['hashstring'], row['ext']))

            batch_source_dir = os.path.join(logsdir, "batch-source-%0.5d" % b)
            batch_source_file = os.path.join(batch_source_dir, row['key'])
            time = row['mtime']
            if time and not time == 'None':
                human_time = datetime.datetime.fromtimestamp(float(time))
            else:
                human_time = "NA"

            batch_info_file = dexy.utils.batch_info_filename(b, logsdir)
            batch_ok = os.path.exists(batch_info_file)

            artifact_ok = os.path.exists(artifact_file)
            batch_source_ok = os.path.exists(batch_source_file)

            if artifact_ok and batch_ok:
                msg = "  batch id %5d  modified time %s available in %s" % (b, human_time, artifact_file)
                if batch_source_ok:
                    msg += " and %s" % batch_source_file
                print msg
        print
    else:
        print "No versions found for", filename

def reset_command(logsdir=Constants.DEFAULT_LDIR, artifactsdir=Constants.DEFAULT_ADIR):
    """
    Runs cleanup and then setup to completely reset your dexy environment.
    """
    cleanup_command(logsdir=logsdir, artifactsdir=artifactsdir)
    setup_command(logsdir=logsdir, artifactsdir=artifactsdir, showhelp=False)

def purge_artifacts(remake=True, artifact_class=None, artifactsdir=Constants.DEFAULT_ADIR):
    shutil.rmtree(artifactsdir, ignore_errors=True)
    if remake:
        os.mkdir(artifactsdir)

    if hasattr(artifact_class, 'purge'):
        artifact_class.purge()

def purge_logs(logsdir=Constants.DEFAULT_LDIR):
    shutil.rmtree(logsdir, ignore_errors=True)

def purge_reports():
    reports_dirs = dexy.introspect.reports_dirs()
    for d in reports_dirs:
        safety_file = os.path.join(d, ".dexy-generated")
        if d and os.path.exists(d) and os.path.exists(safety_file):
            print "purging contents of %s" % d
            shutil.rmtree(d)
        elif d and os.path.exists(d):
            print "not purging %s, please remove this directory manually" % d

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
        text.append("\n" + r.__name__.replace("Reporter", ""))

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
    if kwargs.has_key('report'):
        kwargs['reports'] = kwargs['report']
        del kwargs['report']
    reports_command(**kwargs)

def reports_command(
        artifactclass=Constants.DEFAULT_ACLASS, # What artifact class to use (must correspond to artifact class used by batch id)
        allreports=False, # whether to run all available reporters (except those that are specifically excluded by setting ALLREPORTS=False)
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
    if allreports:
        reports = [k for k, v in reporters.items() if v.ALLREPORTS]

    for r in reports:
        reporter_class_name = r.endswith("Reporter") and r or ("%sReporter" % r)
        if not reporters.has_key(reporter_class_name):
            raise Exception("No reporter class named %s available. Valid reporter classes are: %s" % (r, ", ".join(reporters.keys())))
        report_class = reporters[reporter_class_name]

        print "running", r
        reporter = report_class(
                artifact_class=artifactclass,
                batch_id=batchid,
                controller=controller,
                logsdir=logsdir
            )

        reporter.load_batch_artifacts()
        reporter.run()

def it_command(**kwargs):
    dexy_command(kwargs)


from modargs import args
import dexy.exceptions
import os
import shutil
import sys
import warnings
from dexy.params import RunParams

MOD = sys.modules[__name__]
PROG = 'dexy'
S = "   "
DEFAULT_COMMAND = 'dexy'
DEFAULT_PARAMS = RunParams()

import pkg_resources
for dist in pkg_resources.working_set:
    if dist.key.startswith("dexy-plugin"):
        import_pkg = dist.egg_name().split("-")[0]
        __import__(import_pkg)

import dexy.plugin

def run():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    try:
        if len(sys.argv) == 1 or (sys.argv[1] in args.available_commands(MOD)):
            args.parse_and_run_command(sys.argv[1:], MOD, default_command=DEFAULT_COMMAND)
        else:
            if ":" in sys.argv[1]:
                command, subcommand = sys.argv[1].split(":")
            else:
                command = sys.argv[1]
                subcommand = ""

            command_class = dexy.plugin.Command.aliases.get(command)
            mod_name = command_class.__module__
            mod = args.load_module(mod_name)

            if hasattr(command_class, 'DEFAULT_COMMAND'):
                default_command = command_class.DEFAULT_COMMAND
            else:
                default_command = command_class.NAMESPACE

            # TODO improve error message if not a valid command...
            args.parse_and_run_command([subcommand] + sys.argv[2:], mod, default_command=default_command)

    except dexy.exceptions.UserFeedback as e:
        sys.stderr.write(e.message)
        if not e.message.endswith("\n"):
            sys.stderr.write("\n")
        sys.exit(1)

def dexy_command(
        allreports=False, # whether to run all available reports
        artifactsdir=DEFAULT_PARAMS.artifacts_dir, # location of directory in which to store artifacts
        config=DEFAULT_PARAMS.config_file, # name to use for configuration file
        danger=False, # whether to allow running remote files
        dbfile=DEFAULT_PARAMS.db_file, # name of the database file (it lives in the logs dir)
        directory=".", # the directory to process, you can just process a subdirectory of your project
        disabletests=False, # Whether to disable the dexy 'test' filter
        dryrun=False, # if True, just parse config and print batch info, don't run dexy
        exclude="", # directories to exclude from dexy processing
        filters=False, # DEPRECATED just to catch people who use the old dexy --filters syntax
        globals="", # global values to make available within dexy documents, should be KEY=VALUE pairs separated by spaces
        help=False, # for people who type -help out of habit
        h=False, # for people who type -h out of habit
        hashfunction='md5', # What hash function to use, set to crc32 or adler32 for more speed, less reliability
        ignore=False, # whether to ignore nonzero exit status or raise an error - may not be supported by all filters
        inputs=False, # whether to log information about inputs for debugging
        logfile=DEFAULT_PARAMS.log_file, # name of log file
        loglevel=DEFAULT_PARAMS.log_level, # default log level (see Constants.LOGLEVELS.keys), can also be set per-document
        logsdir=DEFAULT_PARAMS.log_dir, # location of directory in which to store logs
        nocache=False, # whether to force artifacts to run even if there is a matching file in the cache
        output=False, # Shortcut to mean "I just want the OutputReporter, nothing else"
        recurse=True, # whether to recurse into subdirectories when running Dexy
        reporters=False, # DEPRECATED just to catch people who use the old dexy --reporters syntax
        reports=DEFAULT_PARAMS.reports, # reports to be run after dexy runs, enclose in quotes and separate with spaces
        reset=False, # whether to purge existing artifacts and logs before running Dexy
        run="", # specific document to run. if specified, this document + its dependencies will be all that is run
        setup=False, # DEPRECATED just to catch people who use the old dexy --setup syntax
        silent=False, # Whether to not print any output when running dexy
        strictinherit=False, # set to true if you want 'allinputs' to only reference items in same dir or a subdir
        uselocals=True, # use cached local copies of remote URLs, faster but might not be up to date, 304 from server will override this setting
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
    # catch deprecated arguments
    if h or help or version or reporters or filters:
        raise dexy.exceptions.UserFeedback("the command syntax has changed, please type 'dexy help' for help")

    ### @export "dexy-command-check-setup"
    if not check_setup(logsdir=logsdir, artifactsdir=artifactsdir):
        raise dexy.exceptions.UserFeedback("Please run '%s setup' first to create the directories dexy needs to work with" % PROG)

    ### @export "dexy-command-process-args"
    if reset:
        reset_command(logsdir=logsdir, artifactsdir=artifactsdir)

    if output:
        if not reports == DEFAULT_PARAMS.reports:
            raise dexy.exceptions.UserFeedback("if you pass --output you can't also modify reports! pick 1!")
        if allreports:
            raise dexy.exceptions.UserFeedback("if you pass --output you can't also pass --allreports!")
        reports = "Output"

    if allreports:
        if not reports == DEFAULT_PARAMS.reports:
            raise dexy.exceptions.UserFeedback("if you pass --allreports you can't also specify --reports")

    controller = run_dexy(locals())
    if not dryrun:
        if allreports:
            reports_command(
                allreports=True,
                artifactclass=artifactclass,
                controller=controller,
                hashfunction=hashfunction,
                logsdir=logsdir
            )
        else:
            reports_command(
                reports=reports,
                artifactclass=artifactclass,
                controller=controller,
                hashfunction=hashfunction,
                logsdir=logsdir
            )


def reports_command(args):
    pass

def run_dexy(args):
    # validate args and do any conversions required
    args['globals'] = dict([g.split("=") for g in args['globals'].split()])
    args['exclude'] = [x.strip("/") for x in args['exclude'].split()]
    controller = dexy.controller.Controller(args)
    controller.run()
    return controller

def check_setup(logsdir=DEFAULT_PARAMS.log_dir, artifactsdir=DEFAULT_PARAMS.artifacts_dir):
    return os.path.exists(logsdir) and os.path.exists(artifactsdir)


def help_command(on=False):
    args.help_command(PROG, MOD, Constants.DEFAULT_COMMAND, on)

def help_text(on=False):
    return args.help_text(PROG, MOD, Constants.DEFAULT_COMMAND, on)

def version_command():
    """Print the current version."""
    print "%s version %s" % (PROG, dexy.version())


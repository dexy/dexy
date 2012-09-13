from dexy.wrapper import Wrapper
from modargs import args
import dexy.exceptions
import dexy.plugin # so all built-in plugins are registered
import json
import os
import pkg_resources
import sys
import warnings

DEFAULT_COMMAND = 'dexy'
MOD = sys.modules[__name__]
PROG = 'dexy'
S = "   "

# Automatically register plugins in any python package named like dexy_plugin_*
for dist in pkg_resources.working_set:
    if dist.key.startswith("dexy-plugin"):
        import_pkg = dist.egg_name().split("-")[0]
        __import__(import_pkg)

def run():
    """
    Method that runs the command specified on the command line.

    Ensures that UserFeedback exceptions are handled nicely so end users don't see tracebacks.
    """
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

            if command_class.DEFAULT_COMMAND:
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
        artifactsdir=Wrapper.DEFAULT_ARTIFACTS_DIR, # location of directory in which to store artifacts
        conf=Wrapper.DEFAULT_CONFIG_FILE, # name to use for configuration file
        danger=False, # whether to allow running remote files
        dbalias=Wrapper.DEFAULT_DB_ALIAS, # type of database to use
        dbfile=Wrapper.DEFAULT_DB_FILE, # name of the database file (it lives in the logs dir)
#        directory=".", # the directory to process, you can just process a subdirectory of your project
        disabletests=False, # Whether to disable the dexy 'test' filter
        dryrun=Wrapper.DEFAULT_DRYRUN, # if True, just parse config and print batch info, don't run dexy
        exclude=Wrapper.DEFAULT_EXCLUDE, # directories to exclude from dexy processing
        globals=Wrapper.DEFAULT_GLOBALS, # global values to make available within dexy documents, should be KEY=VALUE pairs separated by spaces
        help=False, # for people who type -help out of habit
        h=False, # for people who type -h out of habit
        hashfunction=Wrapper.DEFAULT_HASHFUNCTION, # What hash function to use, set to crc32 or adler32 for more speed but less reliability
        ignore=Wrapper.DEFAULT_IGNORE_NONZERO_EXIT, # whether to ignore nonzero exit status or raise an error - may not be supported by all filters
        logfile=Wrapper.DEFAULT_LOG_FILE, # name of log file
        logformat=Wrapper.DEFAULT_LOG_FORMAT, # format of log entries
        loglevel=Wrapper.DEFAULT_LOG_LEVEL, # default log level (see Constants.LOGLEVELS.keys), can also be set per-document
        logsdir=Wrapper.DEFAULT_LOG_DIR, # location of directory in which to store logs
        nocache=Wrapper.DEFAULT_DONT_USE_CACHE, # whether to force artifacts to run even if there is a matching file in the cache
#        output=False, # Shortcut to mean "I just want the OutputReporter, nothing else"
        recurse=Wrapper.DEFAULT_RECURSE, # whether to recurse into subdirectories when running Dexy
        reports=Wrapper.DEFAULT_REPORTS, # reports to be run after dexy runs, enclose in quotes and separate with spaces
#        reset=False, # whether to purge existing artifacts and logs before running Dexy
#        run="", # specific document to run. if specified, this document + its dependencies will be all that is run
        silent=False, # Whether to not print any output when running dexy
#        uselocals=True, # use cached local copies of remote URLs, faster but might not be up to date, 304 from server will override this setting
        version=False # For people who type -version out of habit
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
    if h or help:
        help_command()
    elif version:
        version_command()
    else:
        wrapper = Wrapper(**locals())
        wrapper.load_config()
        wrapper.setup_log()
        wrapper.load_doc_config()
        wrapper.run()
        wrapper.report()

def reports_command(args):
    pass

def check_setup(logsdir=Wrapper.DEFAULT_LOG_DIR, artifactsdir=Wrapper.DEFAULT_ARTIFACTS_DIR):
    return os.path.exists(logsdir) and os.path.exists(artifactsdir)

def help_command(on=False):
    args.help_command(PROG, MOD, DEFAULT_COMMAND, on)

def help_text(on=False):
    return args.help_text(PROG, MOD, DEFAULT_COMMAND, on)

def version_command():
    """Print the current version."""
    print "%s version %s" % (PROG, dexy.__version__)

def reset_command():
    pass

def conf_command(
        conf=Wrapper.DEFAULT_CONFIG_FILE # Name of config file.
        ):
    """
    Write a dexy.conf file using defaults so you can modify it easily.
    """
    config = Wrapper.default_config()
    # No point specifying config file name in config file.
    del config['conf']

    with open(conf, "wb") as f:
        json.dump(config, f, sort_keys=True, indent=4)

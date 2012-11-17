from dexy.utils import getdoc
from dexy.utils import parse_json
from dexy.utils import parse_yaml
from dexy.version import DEXY_VERSION
from dexy.wrapper import Wrapper
from modargs import args
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
import dexy.exceptions
import dexy.plugins # so all built-in plugins are registered
import inspect
import json
import logging
import os
import sys
import warnings
import yaml

D = Wrapper.DEFAULTS

DEFAULT_COMMAND = 'dexy'
MOD = sys.modules[__name__]
PROG = 'dexy'
S = "   "

def parse_and_run_command(argv, module, default_command):
    try:
        args.parse_and_run_command(argv, module, default_command)
    except dexy.exceptions.UserFeedback as e:
        sys.stderr.write("Oops, there's a problem running your command. Here is the error message:" + os.linesep)
        sys.stderr.write(e.message)
        sys.stderr.write(os.linesep)
        sys.exit(1)

def run():
    """
    Method that runs the command specified on the command line.
    """
    if hasattr(logging, 'captureWarnings'):
        logging.captureWarnings(True)
    else:
        warnings.filterwarnings("ignore",category=Warning)

    if len(sys.argv) == 1 or (sys.argv[1] in args.available_commands(MOD)) or sys.argv[1].startswith("-"):
        parse_and_run_command(sys.argv[1:], MOD, default_command=DEFAULT_COMMAND)

    else:
        if ":" in sys.argv[1]:
            command, subcommand = sys.argv[1].split(":")
        else:
            command = sys.argv[1]
            subcommand = ""

        command_class = dexy.plugin.Command.aliases.get(command)

        if not command_class:
            args.parse_and_run_command(subcommand, dexy.commands)

        mod_name = command_class.__module__
        mod = args.load_module(mod_name)

        if command_class.DEFAULT_COMMAND:
            default_command = command_class.DEFAULT_COMMAND
        else:
            default_command = command_class.NAMESPACE

        parse_and_run_command([subcommand] + sys.argv[2:], mod, default_command=default_command)

def config_args(modargs):
    cliargs = modargs.get("__cli_options", {})
    kwargs = modargs.copy()

    config_file = modargs.get('conf', Wrapper.DEFAULTS['config_file'])

    # Update from config file
    if os.path.exists(config_file):
        with open(config_file, "rb") as f:
            if config_file.endswith(".conf"):
                try:
                    conf_args = parse_yaml(f.read())
                except dexy.exceptions.UserFeedback as yaml_exception:
                    try:
                        conf_args = parse_json(f.read())
                    except dexy.exceptions.UserFeedback as json_exception:
                        print "--------------------------------------------------"
                        print "Tried to parse YAML:"
                        print yaml_exception
                        print "--------------------------------------------------"
                        print "Tried to parse JSON:"
                        print json_exception
                        print "--------------------------------------------------"
                        raise dexy.exceptions.UserFeedback("Unable to parse config file '%s' as YAML or as JSON." % config_file)

            elif config_file.endswith(".yaml"):
                conf_args = parse_yaml(f.read())
            elif config_file.endswith(".json"):
                conf_args = parse_json(f.read())
            else:
                raise dexy.exceptions.UserFeedback("Don't know how to load config from '%s'" % config_file)

            kwargs.update(conf_args)

    if cliargs: # cliargs may be False
        for k in cliargs.keys(): kwargs[k] = modargs[k]

    # TODO allow updating from env variables, e.g. DEXY_ARTIFACTS_DIR

    return kwargs

RENAME_PARAMS = {
        'artifactsdir' : 'artifacts_dir',
        'conf' : 'config_file',
        'dbalias' : 'db_alias',
        'dbfile' : 'db_file',
        'disabletests' : 'disable_tests',
        'dryrun' : 'dry_run',
        'excludealso' : 'exclude_also',
        'ignore' : 'ignore_nonzero_exit',
        'logfile' : 'log_file',
        'logformat' : 'log_format',
        'loglevel' : 'log_level',
        'logdir' : 'log_dir',
        'nocache' : 'dont_use_cache'
        }

def rename_params(kwargs):
    renamed_args = {}
    for k, v in kwargs.iteritems():
        renamed_key = RENAME_PARAMS.get(k, k)
        renamed_args[renamed_key] = v
    return renamed_args

def skip_params(kwargs):
    ok_params = {}
    for k, v in kwargs.iteritems():
        if k in D.keys():
            ok_params[k] = v
    return ok_params

def init_wrapper(modargs):
    kwargs = config_args(modargs)
    kwargs = rename_params(kwargs)
    kwargs = skip_params(kwargs)
    return Wrapper(**kwargs)

def default_config():
    wrapper = Wrapper()
    conf = wrapper.__dict__.copy()

    for k in conf.keys():
        if not k in D.keys():
            del conf[k]

    reverse_rename = dict((v,k) for k, v in RENAME_PARAMS.iteritems())
    for k in conf.keys():
        renamed_key = reverse_rename.get(k, k)
        if renamed_key != k:
            conf[renamed_key] = conf[k]
            del conf[k]

    return conf

def dexy_command(
        __cli_options=False,
        artifactsdir=D['artifacts_dir'], # location of directory in which to store artifacts
        conf=D['config_file'], # name to use for configuration file
        danger=D['danger'], # whether to allow running remote files
        dbalias=D['db_alias'], # type of database to use
        dbfile=D['db_file'], # name of the database file (it lives in the logs dir)
        disabletests=D['disable_tests'], # Whether to disable the dexy 'test' filter
        dryrun=D['dry_run'], # if True, just parse config and print batch info, don't run dexy
        exclude=D['exclude'], # comma-separated list of directory names to exclude from dexy processing
        excludealso=D['exclude_also'], # comma-separated list of directory names to exclude from dexy processing
        globals=D['globals'], # global values to make available within dexy documents, should be KEY=VALUE pairs separated by spaces
        help=False, # for people who type -help out of habit
        h=False, # for people who type -h out of habit
        hashfunction=D['hashfunction'], # What hash function to use, set to crc32 or adler32 for more speed but less reliability
        ignore=D['ignore_nonzero_exit'], # whether to ignore nonzero exit status or raise an error - may not be supported by all filters
        logfile=D['log_file'], # name of log file
        logformat=D['log_format'], # format of log entries
        loglevel=D['log_level'], # log level
        logdir=D['log_dir'], # location of directory in which to store logs
        nocache=D['dont_use_cache'], # whether to force artifacts to run even if there is a matching file in the cache
        profile=D['profile'], # whether to run with cProfile
        recurse=D['recurse'], # whether to recurse into subdirectories when running Dexy
        r=False, # whether to clear cache before running dexy
        reset=False, # whether to clear cache before running dexy
        reports=D['reports'], # reports to be run after dexy runs, enclose in quotes and separate with spaces
        silent=D['silent'], # Whether to not print any output when running dexy
        uselocals=D['uselocals'], # use cached local copies of remote URLs, faster but might not be up to date, 304 from server will override this setting
        target=D['target'], # Which target to run. By default all targets are run, this allows you to run only 1 bundle (and its dependencies).
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
        wrapper_args = locals()

        if r or reset:
            print "Resetting dexy cache..."
            reset_command(artifactsdir=artifactsdir, logdir=logdir)

        wrapper = init_wrapper(wrapper_args)

        try:
            wrapper.check_dexy_dirs()
            wrapper.setup_config()
            if profile:
                import cProfile
                cProfile.runctx("wrapper.run()", None, locals(), "dexy.prof")
                import pstats
                s = pstats.Stats("dexy.prof")
                s.sort_stats("cumulative")
                s.print_stats(25)
            else:
                wrapper.run()

            wrapper.report()
            print "finished in %0.4f" % wrapper.batch_info['elapsed']

        except dexy.exceptions.UserFeedback as e:
            if hasattr(wrapper, 'log'):
                wrapper.log.error("A problem has occurred with one of your documents:")
                wrapper.log.error(e.message)
            wrapper.cleanup_partial_run()
            sys.stderr.write("Oops, there's a problem processing one of your documents. Here is the error message:" + os.linesep)
            sys.stderr.write(e.message)
            if not e.message.endswith(os.linesep) or e.message.endswith("\n"):
                sys.stderr.write(os.linesep)
            sys.stderr.write("Dexy is stopping. There might be more information at the end of the dexy log." + os.linesep)
            sys.exit(1)
        except Exception as e:
            if hasattr(wrapper, 'log'):
                wrapper.log.error("An error has occurred.")
                wrapper.log.error(e)
                wrapper.log.error(e.message)
            import traceback
            traceback.print_exc()

def reset_command(
        __cli_options=False,
        artifactsdir=D['artifacts_dir'], # location of directory in which to store artifacts
        logdir=D['log_dir']# location of directory in which to store logs
        ):
    """
    Empty the artifacts and logs directories.
    """
    wrapper = init_wrapper(locals())
    wrapper.remove_dexy_dirs()
    wrapper.setup_dexy_dirs()

def cleanup_command(
        __cli_options=False,
        artifactsdir=D['artifacts_dir'], # location of directory in which to store artifacts
        logdir=D['log_dir'], # location of directory in which to store logs
        reports=False # Also remove report generated dirs
        ):
    """
    Remove the artifacts and logs directories.
    """
    wrapper = init_wrapper(locals())
    wrapper.remove_dexy_dirs(reports)

def reports_command(args):
    pass

def setup_command(__cli_options=False, **kwargs):
    """
    Create the directories dexy needs to run. This helps make sure you mean to run dexy in this directory.
    """
    wrapper = init_wrapper(locals())
    wrapper.setup_dexy_dirs()

def help_command(on=False):
    args.help_command(PROG, MOD, DEFAULT_COMMAND, on)

def help_text(on=False):
    return args.help_text(PROG, MOD, DEFAULT_COMMAND, on)

def version_command():
    """Print the current version."""
    print "%s version %s" % (PROG, DEXY_VERSION)

def conf_command(
        conf=D['config_file'] # Name of config file.
        ):
    """
    Write a config file containing dexy's defaults.
    """
    if os.path.exists(conf):
        print "Config file %s already exists!" % conf
        sys.exit(1)

    config = default_config()

    # No point specifying config file name in config file.
    del config['conf']

    YAML_HELP = """# YAML config file for dexy.
# You can delete any lines you don't wish to customize.
# Options are same as command line options, for more info run 'dexy help -on dexy'.\n"""

    with open(conf, "wb") as f:
        if conf.endswith(".yaml") or conf.endswith(".conf"):

            f.write(YAML_HELP)
            f.write(yaml.dump(config, default_flow_style=False))
        elif conf.endswith(".json"):
            json.dump(config, f, sort_keys=True, indent=4)
        else:
            raise dexy.exceptions.UserFeedback("Don't know how to write config file '%s'" % conf)

    print "Config file has been written to '%s'" % conf

def filters_command(
        alias="", # If a filter alias is specified, more detailed help for that filter is printed.
        nocolor=False, # When source = True, whether to omit syntax highlighting
        showall=False, # Whether to show all filters, including those which need missing software, implies versions=True
        showmissing=False, # Whether to just show filters missing external software, implies versions=True
        space=False, # Whether to add extra spacing to the output for extra readability
        source=False, # Whether to include syntax-highlighted source code when displaying an indvidual filter
        versions=False # Whether to check the installed version of external software required by filters, slower
        ):
    print filters_text(**locals())

NODOC_FILTERS = []

def filters_text(
        alias="", # If a filter alias is specified, more detailed help for that filter is printed.
        nocolor=False, # When source = True, whether to omit syntax highlighting
        showall=False, # Whether to show all filters, including those which need missing software, implies versions=True
        showmissing=False, # Whether to just show filters missing external software, implies versions=True
        space=False, # Whether to add extra spacing to the output for extra readability
        source=False, # Whether to include syntax-highlighted source code when displaying an indvidual filter
        versions=False # Whether to check the installed version of external software required by filters, slower
        ):

    if len(alias) > 0:
        # We want help on a particular filter
        klass = dexy.filter.Filter.aliases[alias]
        text = []
        text.append(klass.__name__)
        text.append("")
        text.append("Aliases: %s" % ", ".join(klass.ALIASES))
        text.append("")
        text.append(inspect.getdoc(klass))
        text.append("")
        text.append("http://dexy.it/docs/filters/%s" % alias)
        if source:
            text.append("")
            source_code = inspect.getsource(klass)
            if nocolor:
                text.append(source_code)
            else:
                formatter = TerminalFormatter()
                lexer = PythonLexer()
                text.append(highlight(source_code, lexer, formatter))
        return "\n".join(text)

    else:
        def sort_key(k):
            return k.__name__

        filter_classes = sorted(set(f for f in dexy.filter.Filter.plugins), key=sort_key)

        text = []
        for klass in filter_classes:
            if not showall:
                skip = klass.__name__ in NODOC_FILTERS
            else:
                skip = False

            if (versions or showmissing or showall) and not skip:
                if hasattr(klass, 'version'):
                    version = klass.version()
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
                    version_message = "'%s' failed, filter may not be available." % klass.version_command()

            if not skip:
                name_and_aliases = "%s (%s) " % (klass.__name__, ", ".join(klass.ALIASES))
                filter_help = name_and_aliases + getdoc(klass)
                if (versions or showmissing or (showall and not version)):
                    filter_help += " %s" % version_message
                text.append(filter_help)

        if space:
            sep = "\n\n"
        else:
            sep = "\n"
        return sep.join(text)

def it_command(**kwargs):
    # so you can type 'dexy it' if you want to
    dexy_command(kwargs)

def grep_command(
        __cli_options=False,
        expr=None, # The expression to search for
        keyexpr="", # Only search for keys matching this expression, implies keys=True
        keys=False, # if True, try to list the keys in any found files
        recurse=False, # if True, recurse into keys to look for sub keys (implies keys=True)
        artifactsdir=D['artifacts_dir'], # location of directory in which to store artifacts
        logdir=D['log_dir'] # location of directory in which to store logs
        ):
    """
    Search for a Dexy document in the database matching the expression.

    For sqlite the expression will be wrapped in % for you.
    """
    wrapper = init_wrapper(locals())
    wrapper.setup_read()

    for row in wrapper.db.query_like("%%%s%%" % expr):
        print row['key']
#        if keys or len(keyexpr) > 0 or recurse:
#            artifact_classes = dexy.introspect.artifact_classes()
#            artifact_class = artifact_classes[artifactclass]
#            artifact = artifact_class.retrieve(row['hashstring'])
#            if artifact.ext in [".json", ".kch", ".sqlite3"]:
#                if len(keyexpr) > 0:
#                    rows = artifact.kv_storage().query("%%%s%%" % keyexpr)
#                else:
#                    rows = artifact.kv_storage().keys()
#
#                if rows:
#                    print "  key-value store keys:"
#                for k in rows:
#                    print "    %s" % k
#                    if recurse:
#                        v = artifact.retrieve_from_kv_storage(k)
#                        try:
#                            if not hasattr(v, "keys"):
#                                v = json.loads(v)
#                            if hasattr(v, "keys"):
#                                for kk in v.keys():
#                                    print "      %s" % kk
#                        except Exception as e:
#                            pass
#
#            if len(artifact.data_dict.keys()) > 1:
#                print "  data dict keys:"
#            for k in artifact.data_dict.keys():
#                if not k == '1':
#                    print "    %s" % k

def fcmds_command(alias=False):
    """
    Returns a list of available filter commands (fcmds) defined by the specified alias.

    These commands can then be run using the fcmd command.
    """

    def filter_class_commands(filter_alias):
        filter_class = dexy.filter.Filter.aliases[filter_alias]
        cmds = []
        for m in dir(filter_class):
            if m.startswith("docmd_"):
                cmds.append(m.replace("docmd_", ""))
        return sorted(cmds)

    filters_dict = dexy.filter.Filter.aliases
    if (not alias) or (not alias in filters_dict):
        print "Aliases with filter commands defined are:"
        for a in sorted(filters_dict):
            cmds = filter_class_commands(a)
            if len(cmds) > 0:
                print a
    else:
        print "Filter commands defined for %s:" % alias
        cmds = filter_class_commands(alias)
        print os.linesep.join(cmds)

def fcmd_command(
        alias=None, # The alias of the filter which defines the custom command
        cmd=None, # The name of the command to run
        help=False, # If true, just print docstring rather than running command
        **kwargs # Additional arguments to be passed to the command
        ):
    """
    Run a command defined in a dexy filter.
    """
    filter_class = dexy.filter.Filter.aliases.get(alias)

    if not filter_class:
        raise dexy.exceptions.UserFeedback("%s is not a valid alias" % alias)

    cmd_name = "docmd_%s" % cmd

    if not filter_class.__dict__.has_key(cmd_name):
        raise dexy.exceptions.UserFeedback("%s is not a valid command. There is no method %s defined in %s" % (cmd, cmd_name, filter_class.__name__))
    else:
        class_method = filter_class.__dict__[cmd_name]
        if type(class_method) == classmethod:
            if help:
                print inspect.getdoc(class_method.__func__)
            else:
                try:
                    class_method.__func__(filter_class, **kwargs)
                except TypeError as e:
                    print e.message
                    print inspect.getargspec(class_method.__func__)
                    print inspect.getdoc(class_method.__func__)
                    raise e

        else:
            raise dexy.exceptions.InternalDexyProblem("expected %s to be a classmethod of %s" % (cmd_name, filter_class.__name__))

def reporters_command(
        ):
    """
    List available reporters.
    """
    FMT = "%-10s %-20s %s"

    if dexy.reporter.Reporter.aliases:
        print FMT % ('ALIAS', 'DIRECTORY', 'INFO')

    for k in sorted(dexy.reporter.Reporter.aliases):
        reporter_class = dexy.reporter.Reporter.aliases[k]
        reports_dir = reporter_class.REPORTS_DIR or ''
        print FMT % (k, reports_dir, getdoc(reporter_class))

import dexy.template
DEFAULT_TEMPLATE = 'dexy:default'
def gen_command(
        d=None,  # The directory to place generated files in, must not exist.
        t=False, # Shorter alternative to --template.
        template=DEFAULT_TEMPLATE, # The alias of the template to use.
        **kwargs # Additional kwargs passed to template's run() method.
        ):
    """
    Generate a new dexy project in the specified directory, using the template.
    """
    if t and (template == DEFAULT_TEMPLATE):
        template = t
    elif t and template != DEFAULT_TEMPLATE:
        raise dexy.exceptions.UserFeedback("Only specify one of --t or --template, not both.")

    if not template in dexy.template.Template.aliases:
        print "Can't find a template named '%s'. Run 'dexy templates' for a list of templates." % template
        sys.exit(1)

    template_class = dexy.template.Template.aliases[template]
    template_class().run(d, **kwargs)

    # We run dexy setup. This will respect any dexy.conf file in the template
    # but passing command line options for 'setup' to 'gen' currently not supported.
    os.chdir(d)
    wrapper = init_wrapper({})
    wrapper.setup_dexy_dirs()
    print "Success! Your new dexy project has been created in directory '%s'" % d
    if os.path.exists("README"):
        with open("README", "r") as f:
            print f.read()
        print "\nThis information is in the 'README' file for future reference."

def templates_command(
        simple=False # Only print template names, without docstring or headers.
        ):
    """
    List templates that can be used to generate new projects.
    """
    aliases = sorted(dexy.template.Template.aliases)

    if simple:
        print "\n".join(aliases)
    else:
        FMT = "%-40s %s"
        print FMT % ("Alias", "Info")
        for alias in aliases:
            klass = dexy.template.Template.aliases[alias]
            print FMT % (alias, getdoc(klass))

        if len(aliases) == 1:
            print "Run '[sudo] pip install dexy-templates' to install some more templates."

        print "Run 'dexy help -on gen' for help on generating projects from templates."

import SimpleHTTPServer
import SocketServer
from dexy.plugins.website_reporters import WebsiteReporter
from dexy.plugins.output_reporters import OutputReporter
NO_OUTPUT_MSG = """Please run dexy first, or specify a directory to serve. \
For help run 'dexy help -on serve'"""

def serve_command(
        port=8085,
        directory=False
        ):
    """
    Runs a simple web server on dexy-generated files. Will look first to see if
    the Website Reporter has run, if so this content is served. If not the
    standard output/ directory contents are served. You can also specify
    another directory to be served. The port defaults to 8085, this can also be
    customized.

    """
    if not directory:
        if os.path.exists(WebsiteReporter.REPORTS_DIR):
            directory = WebsiteReporter.REPORTS_DIR
        elif os.path.exists(OutputReporter.REPORTS_DIR):
            directory = OutputReporter.REPORTS_DIR
        else:
            print NO_OUTPUT_MSG
            sys.exit(1)

    os.chdir(directory)

    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", port), Handler)
    print "serving contents of %s on http://localhost:%s" % (directory, port)
    httpd.serve_forever()

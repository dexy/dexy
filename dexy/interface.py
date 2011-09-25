from dexy.artifact import Artifact
from dexy.controller import Controller
from dexy.utils import profile_memory
from dexy.version import VERSION
from inspect import isclass
from logging.handlers import RotatingFileHandler
import cProfile
import logging
import os
import re
import shutil
import sys
import urllib

# Directories with this name should be excluded anywhere
EXCLUDE_DIRS_ALL_LEVELS = ['.bzr', '.hg', '.git', '.svn']

# Directories with these names should be excluded only at the project root
EXCLUDE_DIRS_ROOT = ['ignore', 'filters']

EXCLUDE_HELP = """Specify directory names to exclude from processing by dexy.
Directories with these names will be skipped anywhere in your project.
The following patterns are automatically excluded anywhere in your project: %s.
The directories designated for artifacts and logs are automatically excluded,
and the following directory names are also excluded if they appear at the root
level of your project: %s.
Any directory with a file named .nodexy will be skipped, and subdirectories of this will also be skipped.
""" % (", ".join(EXCLUDE_DIRS_ALL_LEVELS), ", ".join(EXCLUDE_DIRS_ROOT))


def artifact_class(artifact_class_name, log):
    artifact_classes = {}

    d = os.path.join(os.path.dirname(__file__), 'artifacts') # yes 'artifacts' not artifacts_dir
    for f in os.listdir(d):
        if f.endswith(".py") and f not in ["base.py", "__init__.py"]:
            log.debug("Loading artifacts in %s" % os.path.join(d, f))
            basename = f.replace(".py", "")
            module = "dexy.artifacts.%s" % basename
            try:
                __import__(module)
            except ImportError as e:
                log.warn("artifact defined in %s are not available: %s" % (module, e))

            if not sys.modules.has_key(module):
                continue

            mod = sys.modules[module]

            for k in dir(mod):
                klass = mod.__dict__[k]
                if isclass(klass) and not (klass == Artifact) and issubclass(klass, Artifact):
                    if artifact_classes.has_key(k):
                        raise Exception("duplicate artifact class name %s called from %s in %s" % (k, f, d))
                    artifact_classes[klass.__name__] = klass

    if not artifact_class_name in artifact_classes.keys():
        raise Exception("artifact class %s not available, maybe check dexy.log for clues" % artifact_class_name)
    return artifact_classes[artifact_class_name]


def setup_option_parser():
    project_base = os.path.abspath(os.curdir)
    os.chdir(project_base)

    def add_option(parser, *args, **kwargs):
        if hasattr(parser, 'add_option'):
            parser.add_option(*args, **kwargs)
        else:
            parser.add_argument(*args, **kwargs)

    try:
        # These are argparse-specific
        import argparse
        option_parser = 'argparse'
        parser = argparse.ArgumentParser()


        class GlobalsArgparseAction(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                value_dict = getattr(namespace, self.dest)
                if not value_dict:
                    value_dict = {}
                if not "=" in values:
                    raise Exception("args passed to %s should be in KEY=value format, no '=' found in %s" % (option_string, values))
                k, v = values.split("=")
                value_dict[k] = v
                setattr(namespace, self.dest, value_dict)

        parser.add_argument(
            '--global',
            help="""Use to set a global variable which will be available within dexy tasks,
            use KEY=value syntax and specify option multiple times if you need to specify more than 1 key value pair
            e.g. VERSION=0.0.1""",
            action=GlobalsArgparseAction,
            dest='globals'
        )

        parser.add_argument(
            'dir',
            help='directory of files to process with dexy',
            default='.', nargs='?'
        )

        parser.add_argument(
            '-x', '--exclude',
            help=EXCLUDE_HELP,
            nargs='+'
        )

        parser.add_argument(
            '--use-reporters', '--use-reporter',
            help="list reporters to be run",
            nargs='+'
        )

        parser.add_argument(
            '-v', '--version',
            action='version',
            version='%%(prog)s %s' % VERSION
        )

    except ImportError:
        # These are optparse-specific
        import optparse
        option_parser = 'optparse'
        parser = optparse.OptionParser(version="%%prog %s" % VERSION)
        parser.add_option(
            '-x', '--exclude',
            help=EXCLUDE_HELP + ' Separate multiple directories with commas.'
        )

        parser.add_option(
            "--use-reporters",
            help="list reporters to be used. separate multiple reproters with commas"
        )

    # Remaining options are the same for argparse and optparse
    add_option(parser,
        '-n', '--no-recurse',
        dest='recurse',
        default=True,
        action='store_false',
        help='do not recurse into subdirectories (default: recurse)'
    )

    add_option(parser,
        '--no-tests',
        dest='run_tests',
        default=True,
        action='store_false',
        help='do not run any dexy tests (using the test filter) - helpful for populating test content'
    )

    add_option(parser,
        '-u', '--utf8',
        default=False,
        action='store_true',
        help='switch encoding to UTF-8 (default: don\'t change encoding)'
    )

    add_option(parser,
        '-p', '--purge',
        default=False,
        action='store_true',
        help='purge all artifacts before running dexy'
    )

    add_option(parser,
        '--cleanup',
        default=False,
        action='store_true',
        help='delete all dexy-generated directories and files (does not run dexy)'
    )

    add_option(parser,
        '--filters',
        default=False,
        action='store_true',
        help='list all available filters (does not run dexy)'
    )

    add_option(parser,
        '--profile',
        default=False,
        action='store_true',
        help='run dexy with cProfile'
    )

    add_option(parser,
        '--reporters',
        default=False,
        action='store_true',
        help='list all available reporters (does not run dexy)'
    )

    add_option(parser,
        '--artifact-class',
        default='FileSystemJsonArtifact',
        help='name of artifact class to use (default: FileSystemJsonArtifact)'
    )

    add_option(parser,
        '-a', '--artifacts-dir',
        default='artifacts',
        help='location of artifacts directory (default: artifacts)'
    )

    add_option(parser,
        '-l', '--logs-dir',
        default='logs',
        help="""location of logs directory (default: logs)
               dexy will create a dexy.log file in this directory
               reporters may create reports in this directory"""
    )

    add_option(parser,
        '-c', '--cache-dir',
        default='cache',
        help='DEPRECATED - does not do anything anymore, will be removed soon'
    )

    add_option(parser,
        '--local',
        default=False,
        action='store_true',
        help='Use cached local copies of remote urls - faster but might not be up to date'
        )

    add_option(parser,
        '--ignore-errors',
        default=False,
        action='store_true',
        help="""Don't raise an error if scripts return nonzero exit status
               (depends on the filter being written to support this)"""
        )

    add_option(parser,
        '--setup',
        default=False,
        action='store_true',
        help='Create artifacts and logs directory and generic .dexy file'
        )

    add_option(parser,
        '--serve',
        default=False,
        action='store_true',
        help='Start a static server within the output directory, will be visible on port 8000. (similar to python -m SimpleHTTPServer)'
        )

    add_option(parser,
        '-g', '--config',
        default='.dexy',
        help='name of configuration file'
    )

    add_option(parser,
        '-d', '--dangerous',
        default=False,
        action='store_true',
        help='Allow running remote URLs which may execute dangerous code, use with care.'
     )

    add_option(parser,
        '--no-reports',
        default=False,
        action='store_true',
        help="""Don't run reports when finished running Dexy."""
     )

    if (option_parser == 'argparse'):
        args = parser.parse_args()
        dir_name = args.dir
        if args.exclude:
            additional_excludes = args.exclude
        else:
            additional_excludes = []

        if args.use_reporters:
            use_reporters = args.use_reporters
        else:
            use_reporters = None

    elif (option_parser == 'optparse'):
        (args, argv) = parser.parse_args()
        if len(argv) == 0:
            dir_name = '.'
        else:
            dir_name = argv[0]
        if args.exclude:
            additional_excludes = args.exclude.split(',')
        else:
            additional_excludes = []

        if args.use_reporters:
            use_reporters = args.use_reporters.split(',')
        else:
            use_reporters = None
    else:
        raise Exception("unexpected option_parser %s" % option_parser)

    args.run_dexy = True

    if args.utf8:
        if (sys.getdefaultencoding() == 'UTF-8'):
            print "encoding is already UTF-8"
        else:
            print "changing encoding from %s to UTF-8" % sys.getdefaultencoding()
            reload(sys)
            sys.setdefaultencoding("UTF-8")

    if not os.path.exists(dir_name):
        raise Exception("file %s not found!" % dir_name)

    if args.setup:
        if not os.path.exists(args.artifacts_dir):
            os.mkdir(args.artifacts_dir)
        if not os.path.exists(args.logs_dir):
            os.mkdir(args.logs_dir)
        if not os.path.exists(".dexy"):
            f = open(".dexy", "w")
            f.write("{\n}\n")
            f.close()

    if args.config.startswith("http"):
        print "fetching remote config file %s" % args.config
        filename = os.path.basename(args.config)
        print "writing to %s" % filename
        f = urllib.urlopen(args.config)
        config_file = open(filename, "w")
        config_file.write(f.read())
        config_file.close()
        f.close()
        args.config = filename


    if not os.path.exists(args.artifacts_dir):
        path_to_artifacts_dir = os.path.join(project_base, args.artifacts_dir)
        raise Exception(
            """artifacts directory not found at '%s',
            please call dexy with --setup if you want to use
            this location as a dexy project root""" % (args.artifacts_dir)
        )

    if not os.path.exists(args.logs_dir):
        path_to_logs_dir = os.path.join(project_base, args.logs_dir)
        raise Exception(
            """logs directory not found at %s,
            please call dexy with --setup if you want to use
            this location as a dexy project root""" % (path_to_logs_dir)
        )

    # Set up main dexy log
    dexy_log = logging.getLogger("dexy")
    dexy_log.setLevel(logging.DEBUG)

    logfile = os.path.join(args.logs_dir, 'dexy.log')
    handler = RotatingFileHandler(logfile)
    dexy_log.addHandler(handler)
    if args.setup:
        # This might be the first time someone has run Dexy,
        # let them know where the logfile is
        print "dexy will log debugging information to", logfile

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    args.artifact_class = artifact_class(args.artifact_class, dexy_log)

    if args.purge:
        dexy_log.warn("purging contents of %s" % args.artifacts_dir)
        shutil.rmtree(args.artifacts_dir)
        os.mkdir(args.artifacts_dir)

        # Each artifact class may need to do its own purging also
        if hasattr(args.artifact_class, 'purge'):
            args.artifact_class.purge()

    if args.cleanup:
        args.run_dexy = False
        print "purging contents of %s" % args.artifacts_dir
        shutil.rmtree(args.artifacts_dir)

        if os.path.exists(args.cache_dir):
            print "purging contents of %s" % args.cache_dir
            shutil.rmtree(args.cache_dir)

        if os.path.exists(args.logs_dir):
            print "purging contents of %s" % args.logs_dir
            shutil.rmtree(args.logs_dir)

        if os.path.exists('testdb') and False:
            os.remove('testdb')

        if os.path.exists('output-latest.tgz'):
            os.remove('output-latest.tgz')

        controller = Controller()
        controller.find_reporters()
        for d in controller.reports_dirs:
            if d and os.path.exists(d):
                print "purging contents of %s" % d
                shutil.rmtree(d)


        filters_dir = 'filters'
        # TODO improve this so it detects __init__.py customizations etc.
        if os.path.exists(filters_dir):
            if sorted(os.listdir(filters_dir)) == ['README', '__init__.py']:
                dexy_log.warn("purging contents of %s" % filters_dir)
                shutil.rmtree(filters_dir)
            else:
                print("Directory %s has been modified, not removing." % filters_dir)

    if args.reporters:
        args.run_dexy = False
        controller = Controller()
        reporters = controller.find_reporters()
        for r in reporters:
            print r.__name__
            if r.REPORTS_DIR:
                print "any generated reports will be saved in", r.REPORTS_DIR
            else:
                print "any generated reports will be saved in", args.logs_dir
            if r.__doc__:
                print r.__doc__
            else:
                print "no documentation available"
            print # finish with blank line
        print "Running reports can be disabled with the --no-reports option"

    if args.filters:
        args.run_dexy = False
        controller = Controller()
        filters = controller.find_filters()
        for k in sorted(filters.keys()):
            klass = filters[k]
            print
            print k, ":", klass.__name__
            if klass.executable():
                print "    calls", klass.executable()
            if klass.version_command():
                try:
                    raw_version = klass.version().strip()
                    if raw_version.find("\n") > 0:
                        # Clean up long version strings like R's
                        version = raw_version.split("\n")[0]
                    else:
                        version = raw_version

                    print "    version", version, "detected using",klass.version_command()
                except Exception: # TODO raise/catch specific Exception
                    print "    may not be installed, was unable to run", klass.version_command()
            if klass.__doc__:
                print "   ", klass.__doc__.strip()

    return args, dir_name, additional_excludes, dexy_log

def setup_controller():
    args, dir_name, additional_excludes, log = setup_option_parser()

    if not args.run_dexy:
        return None, args, log

    controller = Controller()
    controller.dir_name = dir_name
    controller.args = args
    controller.allow_remote = args.dangerous
    controller.artifact_class = args.artifact_class
    controller.artifacts_dir = args.artifacts_dir
    controller.logs_dir = args.logs_dir
    controller.log = log
    controller.config_file = args.config
    controller.use_local_files = args.local
    reporters = controller.find_reporters()
    if args.use_reporters:
        controller.reporters = [r for r in reporters if r.__name__ in args.use_reporters]
    else:
        controller.reporters = [r for r in reporters if r.DEFAULT]

    controller.additional_excludes = additional_excludes

    return controller, args, log

def dexy_command():
    controller, args, log = setup_controller()

    if not controller:
        return False

    if args.recurse:
        log.info("running dexy with recurse")
        for dirpath, dirnames, filenames in os.walk(controller.dir_name):
            process_dir = True

            if dirpath == ".":
                # We only exclude these dirs if they occur at project root level
                for x in EXCLUDE_DIRS_ROOT:
                    if x in dirnames:
                        log.debug("removing %s from list of child dirs %s of %s because it is in EXCLUDE_DIRS_ROOT" % (x, dirnames, dirpath))
                        dirnames.remove(x)

                for x in [controller.artifacts_dir, controller.logs_dir]:
                    if x in dirnames:
                        log.debug("removing %s from list of child dirs %s of %s because it is a dexy dir" % (x, dirnames, dirpath))
                        dirnames.remove(x)

                for x in controller.reports_dirs:
                    if x in dirnames:
                        log.debug("removing %s from list of child dirs %s of %s because it is a dexy report dir" % (x, dirnames, dirpath))
                        dirnames.remove(x)


            for x in EXCLUDE_DIRS_ALL_LEVELS:
                if x in dirnames:
                    log.debug("removing %s from list of child dirs %s of %s because it is in EXCLUDE_DIRS_ALL_LEVELS" % (x, dirnames, dirpath))
                    dirnames.remove(x)

            # If there is a file called .nodexy, this dir and all children are skipped.
            if os.path.isfile(os.path.join(dirpath, '.nodexy')):
                log.info("nodexy file found in %s" % dirpath)
                for d in dirnames:
                    # Remove all child dirs from processing.
                    dirnames.remove(d)
                process_dir = False

            # Now process any additional excludes specified on the command line
            for x in controller.additional_excludes:
                pattern = x
                m = re.match(pattern, dirpath)
                if not m:
                    pattern = "./%s" % x
                    m = re.match(pattern, dirpath)
                if m:
                    log.debug("removing %s because it matches pattern %s" % (dirpath, pattern))
                    for d in dirnames:
                        # Remove all child dirs from processing.
                        dirnames.remove(d)
                    process_dir = False
                else:
                    # check if children match pattern
                    for d in dirnames:
                        if x == d:
                            fullpath = os.path.join(dirpath, d)
                            log.debug("removing %s because it matches pattern %s" % (fullpath, pattern))
                            dirnames.remove(d)

            if not process_dir:
                log.warn("skipping dir %s" % dirpath)
            else:
                log.info("processing dir %s" % dirpath)
                controller.load_config(dirpath)
    else:
        log.info("not recursing")
        log.info("processing dir %s" % controller.dir_name)
        controller.load_config(controller.dir_name)

    if args.profile:
        cProfile.runctx("controller.setup_and_run()", globals(), locals(), "dexy.prof")
    else:
        controller.setup_and_run()

    if not args.no_reports:
        for reporter_klass in controller.reporters:
            reporter_klass(controller).run()
            profile_memory("report-%s-complete" % reporter_klass.__name__)
    else:
        print 'reports not run'

    if args.serve:
        import SimpleHTTPServer
        import SocketServer

        os.chdir('output')

        PORT = 8000
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

        httpd = SocketServer.TCPServer(("", PORT), Handler)

        print "serving at port", PORT
        httpd.serve_forever()


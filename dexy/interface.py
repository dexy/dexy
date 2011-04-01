from dexy.artifact import Artifact
from dexy.controller import Controller
from dexy.version import VERSION
from inspect import isclass
from logging.handlers import RotatingFileHandler
import logging
import os
import shutil
import sys
import urllib

EXCLUDED_DIRS = ['.bzr', '.hg', '.git', '.svn', 'ignore', 'filters']
EXCLUDE_DIR_HELP = """Exclude directories from processing by dexy, only relevant
if recursing. The directories designated for artifacts, logs and cache are
automatically excluded, as are %s.
""" % ", ".join(EXCLUDED_DIRS)

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

        parser.add_argument(
            'dir',
            help='directory of files to process with dexy',
            default='.', nargs='?'
        )

        parser.add_argument(
            '-x', '--exclude-dir',
            help=EXCLUDE_DIR_HELP,
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
            '-x', '--exclude-dir',
            help=EXCLUDE_DIR_HELP + ' Separate multiple directories with commas.'
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
        help='location of cache directory (default: cache)'
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
        if args.exclude_dir:
            exclude_dir = args.exclude_dir
        else:
            exclude_dir = []

    elif (option_parser == 'optparse'):
        (args, argv) = parser.parse_args()
        if len(argv) == 0:
            dir_name = '.'
        else:
            dir_name = argv[0]
        if args.exclude_dir:
            exclude_dir = args.exclude_dir.split(',')
        else:
            exclude_dir = []
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
            """artifacts directory not found at %s,
            please create a directory called %s if you want to use
            this location as a dexy project root""" % (path_to_artifacts_dir, args.artifacts_dir)
        )

    if not os.path.exists(args.logs_dir):
        path_to_logs_dir = os.path.join(project_base, args.logs_dir)
        raise Exception(
            """logs directory not found at %s,
            please create a directory called %s if you want to use
            this location as a dexy project root""" % (path_to_logs_dir, args.logs_dir)
        )

    # Set up main dexy log
    dexy_log = logging.getLogger("dexy")
    dexy_log.setLevel(logging.DEBUG)

    logfile = os.path.join(args.logs_dir, 'dexy.log')
    handler = RotatingFileHandler(logfile)
    dexy_log.addHandler(handler)

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
        handlers = controller.find_handlers()
        for k in sorted(handlers.keys()):
            klass = handlers[k]
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

    return args, dir_name, exclude_dir, dexy_log


def dexy_command():
    args, dir_name, exclude_dir, log = setup_option_parser()

    do_not_process_dirs = EXCLUDED_DIRS
    do_not_process_dirs += exclude_dir
    do_not_process_dirs.append(args.artifacts_dir)
    do_not_process_dirs.append(args.logs_dir)
    do_not_process_dirs.append(args.cache_dir)

    if not args.run_dexy:
        return

    log.info("running dexy with recurse")
    controller = Controller()
    controller.args = args
    controller.allow_remote = args.dangerous
    controller.artifact_class = args.artifact_class
    controller.artifacts_dir = args.artifacts_dir
    controller.cache_dir = args.cache_dir
    controller.logs_dir = args.logs_dir
    controller.log = log
    controller.config_file = args.config
    controller.use_local_files = args.local
    controller.find_reporters()
    for r in controller.reports_dirs:
        if r:
            do_not_process_dirs.append(r)

    log.info("skipping directories named %s" % ", ".join(do_not_process_dirs))
    if args.recurse:
        for root, dirs, files in os.walk(dir_name):
            process = True
            for x in do_not_process_dirs:
                if root.startswith(x) or root.startswith("./%s" % x):
                    process = False
                    break

            if not process:
                log.warn("skipping dir %s" % root)
            else:
                log.info("processing dir %s" % root)
                controller.load_config(root)
    else:
        log.info("not recursing")
        process = True
        for x in do_not_process_dirs:
            if dir_name.startswith(x) or dir_name.startswith("./%s" % x):
                process = False
                break

        if not process:
            log.warn("skipping dir %s" % dir_name)
        else:
            log.info("processing dir %s" % dir_name)
            controller.load_config(dir_name)

    controller.setup_and_run()
    if not args.no_reports:
        for reporter_klass in controller.reporters:
            reporter_klass(controller).run()
    else:
        print 'reports not run'


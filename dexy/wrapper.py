from dexy.utils import s
import dexy.batch
import dexy.database
import dexy.doc
import dexy.parser
import dexy.reporter
import logging
import logging.handlers
import os
import shutil

class Wrapper(object):
    """
    Class that assists in interacting with dexy, including running dexy.
    """
    DEFAULTS = {
        'artifacts_dir' : 'artifacts',
        'config_file' : 'dexy.conf',
        'danger' : False,
        'db_alias' : 'sqlite3',
        'db_file' : 'dexy.sqlite3',
        'disable_tests' : False,
        'dont_use_cache' : False,
        'dry_run' : False,
        'encoding' : 'utf-8',
        'exclude' : '.git, .svn, tmp, cache',
        'exclude_also' : '',
        'full' : False,
        'globals' : '',
        'hashfunction' : 'md5',
        'ignore_nonzero_exit' : False,
        'log_dir' : 'logs',
        'log_file' : 'dexy.log',
        'log_format' : "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        'log_level' : "DEBUG",
        'profile' : False,
        'recurse' : True,
        'reports' : '',
        'siblings' : False,
        'silent' : False,
        'target' : False,
        'uselocals' : False
    }
    LOG_LEVELS = {
        'DEBUG' : logging.DEBUG,
        'INFO' : logging.INFO,
        'WARN' : logging.WARN
    }

    def __init__(self, *args, **kwargs):
        self.args = args
        self.initialize_attribute_defaults()
        self.update_attributes_from_kwargs(kwargs)

    def initialize_attribute_defaults(self):
        for name, value in self.DEFAULTS.iteritems():
            setattr(self, name, value)

    def update_attributes_from_kwargs(self, kwargs):
        for key, value in kwargs.iteritems():
            if not key in self.DEFAULTS:
                raise Exception("invalid kwargs %s" % key)
            setattr(self, key, value)

    def setup(self, setup_dirs=False, log_config=True):
        if setup_dirs:
            self.setup_dexy_dirs()
        self.check_dexy_dirs()
        self.setup_log()
        self.setup_db()
        if log_config:
            self.log_dexy_config()

    def run(self):
        self.setup()

        self.batch = self.init_batch()
        self.batch.run(self.target)

        self.save_db()

    def log_dexy_config(self):
        self.log.debug("dexy has config:")
        for k in sorted(self.__dict__):
            if not k in ('ast', 'args', 'db', 'log', 'tasks'):
                self.log.debug("  %s: %s" % (k, self.__dict__[k]))

    def db_path(self):
        return os.path.join(self.artifacts_dir, self.db_file)

    def log_path(self):
        return os.path.join(self.log_dir, self.log_file)

    def setup_batch(self):
        """
        Shortcut method for calling init_batch and assigning to batch instance variable.
        """
        self.batch = self.init_batch()

    def init_batch(self):
        batch = dexy.batch.Batch(self)

        if len(self.args) > 0:
            batch.tree = self.docs_from_args()
            batch.create_lookup_table()
        else:
            ast = self.load_doc_config()
            batch.load_ast(ast)

        return batch

    def run_docs(self, *docs):
        self.args = docs
        self.run()

    def setup_read(self, batch_id=None):
        self.setup(log_config=False)

        if batch_id:
            self.batch_id = batch_id
        else:
            self.batch_id = self.db.max_batch_id()

    def check_dexy_dirs(self):
        if not (os.path.exists(self.artifacts_dir) and os.path.exists(self.log_dir)):
            raise dexy.exceptions.UserFeedback("You need to run 'dexy setup' in this directory first.")

    def setup_dexy_dirs(self):
        if not os.path.exists(self.artifacts_dir):
            os.mkdir(self.artifacts_dir)
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)

    def remove_dexy_dirs(self, reports=False):
        if os.path.exists(self.artifacts_dir):
            shutil.rmtree(self.artifacts_dir)
        if os.path.exists(self.log_dir):
            shutil.rmtree(self.log_dir)

        if reports:
            if isinstance(reports, bool):
                reports=dexy.reporter.Reporter.plugins

            for report in reports:
                report.remove_reports_dir()

    def logging_log_level(self):
        try:
            return self.LOG_LEVELS[self.log_level.upper()]
        except KeyError:
            msg = "'%s' is not a valid log level, check python logging module docs."
            raise dexy.exceptions.UserFeedback(msg % self.log_level)

    def setup_log(self):
        if not hasattr(self, 'log') or not self.log:
            self.log = logging.getLogger('dexy')
            self.log.setLevel(self.logging_log_level())

            handler = logging.handlers.RotatingFileHandler(
                    self.log_path(),
                    encoding="utf-8")

            formatter = logging.Formatter(self.log_format)
            handler.setFormatter(formatter)

            self.log.addHandler(handler)

    def setup_db(self):
        db_class = dexy.database.Database.aliases[self.db_alias]
        self.db = db_class(self)

    def docs_from_args(self):
        """
        Creates document objects from argument strings, returns array of newly created docs.
        """
        docs = []
        for arg in self.args:
            self.log.debug("Processing arg %s" % arg)
            doc = self.create_doc_from_arg(arg)
            if not doc:
                raise Exception("no doc created for %s" % arg)
            doc.wrapper = self
            docs.append(doc)
        return docs

    def create_doc_from_arg(self, arg, **kwargs):
        if isinstance(arg, dexy.task.Task):
            return arg

        elif isinstance(arg, list):
            if not isinstance(arg[0], basestring):
                msg = "First arg in %s should be a string" % arg
                raise dexy.exceptions.UserFeedback(msg)

            if not isinstance(arg[1], dict):
                msg = "Second arg in %s should be a dict" % arg
                raise dexy.exceptions.UserFeedback(msg)

            if kwargs:
                raise Exception("Shouldn't have kwargs if arg is a list")

            alias, pattern = dexy.parser.Parser.qualify_key(arg[0])
            return dexy.task.Task.create(alias, pattern, **arg[1])

        elif isinstance(arg, basestring):
            alias, pattern = dexy.parser.Parser.qualify_key(arg[0])
            return dexy.task.Task.create(alias, pattern, **kwargs)

        else:
            raise Exception("unknown arg type %s for arg %s" % (arg.__class__.__name__, arg))

    def save_db(self):
        self.db.save()

    def reports_dirs(self):
        return [c.REPORTS_DIR for c in dexy.reporter.Reporter.plugins]

    def report(self):
        if self.reports:
            self.log.debug("generating user-specified reports '%s'" % self.reports)
            reporters = []
            for alias in self.reports.split():
                reporter_class = dexy.reporter.Reporter.aliases[alias]
                self.log.debug("initializing reporter %s for alias %s" % (reporter_class.__name__, alias))
                reporters.append(reporter_class())
        else:
            self.log.debug("no reports specified, generating all reports for which ALLREPORTS is True")
            reporters = [c() for c in dexy.reporter.Reporter.plugins if c.ALLREPORTS]

        for reporter in reporters:
            self.log.debug("running reporter %s" % reporter.ALIASES[0])
            reporter.run(self)

    def is_valid_dexy_dir(self, dirpath, dirnames):
        nodexy_file = os.path.join(dirpath, '.nodexy')
        pip_delete_this_dir_file = os.path.join(dirpath, "pip-delete-this-directory.txt")
        if os.path.exists(nodexy_file):
            self.log.debug("  skipping directory '%s' and its children because .nodexy file found" % dirpath)
            dirnames[:] = []
            return False
        else:
            if os.path.exists(pip_delete_this_dir_file):
                print s("""WARNING pip left an old build/ file lying around!
                You probably want to cancel this dexy run (ctrl+c) and remove this directory first!
                Dexy will continue running unless you stop it...""")

            for x in self.exclude_dirs():
                if x in dirnames:
                    skipping_dir = os.path.join(dirpath, x)
                    self.log.debug("  skipping directory '%s' because it matches exclude '%s'" % (skipping_dir, x))
                    dirnames.remove(x)

            return True

    def load_doc_config(self):
        """
        Look for document config files in current working tree and load them.
        """
        ast = dexy.parser.AbstractSyntaxTree(self)

        config_files_used = []
        for dirpath, dirnames, filenames in os.walk("."):
            if self.is_valid_dexy_dir(dirpath, dirnames):
                check_for_double_config = []
                for alias in dexy.parser.Parser.aliases.keys():
                    path_to_config = os.path.join(dirpath, alias)

                    if os.path.exists(path_to_config):
                        self.log.debug("loading config from '%s'" % path_to_config)
                        with open(path_to_config, "r") as f:
                            config_text = f.read()

                        check_for_double_config.append(path_to_config)
                        config_files_used.append(path_to_config)

                        parser = dexy.parser.Parser.aliases[alias](self, ast)
                        parser.build_ast(dirpath, config_text)

                if len(check_for_double_config) > 1:
                    msg = "more than one config file found in dir %s: %s"
                    msg_args = (dirpath, ", ".join(check_for_double_config))
                    raise dexy.exceptions.UserFeedback(msg % msg_args)

        if len(config_files_used) == 0:
            msg = "WARNING: Didn't find any document config files (like %s)"
            print msg % (", ".join(dexy.parser.Parser.aliases.keys()))
        self.log.debug("AST completed:")
        ast.debug(self.log)

        return ast

    def setup_config(self):
        self.setup_dexy_dirs()
        self.setup_log()
        self.load_doc_config()

    def cleanup_partial_run(self):
        if hasattr(self, 'db'):
            # TODO remove any entries which don't have
            self.db.save()

    def exclude_dirs(self):
        exclude_str = self.exclude
        if self.exclude_also:
            exclude_str += ",%s" % self.exclude_also
        exclude = [d.strip() for d in exclude_str.split(",")]

        exclude.append(self.artifacts_dir)
        exclude.append(self.log_dir)
        exclude.extend(self.reports_dirs())

        return exclude

    def parse_globals(self):
        globals_dict = {}
        if len(self.globals) > 0:
            for pair in self.globals.split(","):
                x, y = pair.split("=")
                globals_dict[x] = y

        return globals_dict

    def walk(self, start, recurse=True):
        exclude = self.exclude_dirs()

        for dirpath, dirnames, filenames in os.walk(start):
            for x in exclude:
                if x in dirnames:
                    dirnames.remove(x)

            if not recurse:
                dirnames[:] = []

            nodexy_file = os.path.join(dirpath, '.nodexy')
            if os.path.exists(nodexy_file):
                dirnames[:] = []
            else:
                for filename in filenames:
                    yield(dirpath, filename)

from dexy.common import OrderedDict
import dexy.database
import dexy.doc
import dexy.parser
import dexy.reporter
import inspect
import json
import logging
import logging.handlers
import os
import shutil

class Wrapper(object):
    """
    Class that assists in interacting with Dexy, including running Dexy.
    """
    DEFAULT_ARTIFACTS_DIR = 'artifacts'
    DEFAULT_CONFIG_FILE = 'dexy.conf' # Specification of dexy-wide config options.
    DEFAULT_DANGER = False
    DEFAULT_DB_ALIAS = 'sqlite3'
    DEFAULT_DB_FILE = 'dexy.sqlite3'
    DEFAULT_DISABLE_TESTS = False
    DEFAULT_DONT_USE_CACHE = False
    DEFAULT_DRYRUN = False
    DEFAULT_EXCLUDE = ''
    DEFAULT_GLOBALS = ''
    DEFAULT_HASHFUNCTION = 'md5'
    DEFAULT_IGNORE_NONZERO_EXIT = False
    DEFAULT_LOG_DIR = 'logs'
    DEFAULT_LOG_FILE = 'dexy.log'
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_LOG_LEVEL = 'DEBUG'
    DEFAULT_RECURSE = True
    DEFAULT_REPORTS = 'output'
    DEFAULT_SILENT = False

    LOG_LEVELS = {
            'DEBUG' : logging.DEBUG,
            'INFO' : logging.INFO,
            'WARN' : logging.WARN
            }

    RENAME_PARAMS = {
            'artifactsdir' : 'artifacts_dir',
            'conf' : 'config_file',
            'dbalias' : 'db_alias',
            'dbfile' : 'db_file',
            'disabletests' : 'disable_tests',
            'dryrun' : 'dry_run',
            'ignore' : 'ignore_nonzero_exit',
            'logfile' : 'log_file',
            'logformat' : 'log_format',
            'loglevel' : 'log_level',
            'logsdir' : 'log_dir',
            'nocache' : 'dont_use_cache'
            }

    SKIP_KEYS = ['h', 'help', 'version']

    def __init__(self, *args, **kwargs):
        self.initialize_attribute_defaults()
        self.check_config_file_location(kwargs)
        self.load_config_file()
        self.update_attributes_from_config(kwargs)

        self.args = args
        self.docs_to_run = []
        self.tasks = OrderedDict()
        self.pre_attrs = {}

    def initialize_attribute_defaults(self):
        self.artifacts_dir = self.DEFAULT_ARTIFACTS_DIR
        self.config_file = self.DEFAULT_CONFIG_FILE
        self.danger = self.DEFAULT_DANGER
        self.db_alias = self.DEFAULT_DB_ALIAS
        self.db_file = self.DEFAULT_DB_FILE
        self.disable_tests = self.DEFAULT_DISABLE_TESTS
        self.dont_use_cache = self.DEFAULT_DONT_USE_CACHE
        self.dry_run = self.DEFAULT_DRYRUN
        self.exclude = self.DEFAULT_EXCLUDE
        self.globals = self.DEFAULT_GLOBALS
        self.hashfunction = self.DEFAULT_HASHFUNCTION
        self.ignore_nonzero_exit = self.DEFAULT_IGNORE_NONZERO_EXIT
        self.log_dir = self.DEFAULT_LOG_DIR
        self.log_file = self.DEFAULT_LOG_FILE
        self.log_format = self.DEFAULT_LOG_FORMAT
        self.log_level = self.DEFAULT_LOG_LEVEL
        self.recurse = self.DEFAULT_RECURSE
        self.reports = self.DEFAULT_REPORTS
        self.silent = self.DEFAULT_SILENT

    def check_config_file_location(self, kwargs):
        self.update_attributes_from_config(kwargs)

    def update_attributes_from_config(self, config):
        for key, value in config.iteritems():
            if not key in self.SKIP_KEYS:
                corrected_key = self.RENAME_PARAMS.get(key, key)
                if not hasattr(self, corrected_key):
                    raise Exception("no default for %s" % corrected_key)
                setattr(self, corrected_key, value)

    def load_config_file(self):
        """
        Look for a config file in current working dir and loads it.
        """
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                try:
                    conf = json.load(f)
                except ValueError as e:
                    msg = inspect.cleandoc("""Was unable to parse the json in your config file '%s'.
                    Here is information from the json parser:""" % self.config_file)
                    msg += "\n"
                    msg += str(e)
                    raise dexy.exceptions.UserFeedback(msg)

            self.update_attributes_from_config(conf)

    @classmethod
    def default_config(klass):
        conf = klass().__dict__.copy()

        # Remove any attributes that aren't config options
        del conf['args']
        del conf['docs_to_run']
        del conf['tasks']

        for cl_key, internal_key in klass.RENAME_PARAMS.iteritems():
            conf[cl_key] = conf[internal_key]
            del conf[internal_key]

        return conf

    def db_path(self):
        return os.path.join(self.artifacts_dir, self.db_file)

    def log_path(self):
        return os.path.join(self.log_dir, self.log_file)

    def run(self):
        self.setup_run()

        self.log.debug("batch id is %s" % self.batch_id)

        for doc in self.docs_to_run:
            for task in doc:
                task()

        self.save_db()
        self.setup_graph()

    def setup_run(self):
        self.check_dexy_dirs()
        self.setup_log()
        self.setup_db()

        self.batch_id = self.db.next_batch_id()

        if not self.docs_to_run:
            self.setup_docs()

    def setup_read(self, batch_id=None):
        self.check_dexy_dirs()
        self.setup_log()
        self.setup_db()

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

    def remove_dexy_dirs(self):
        shutil.rmtree(self.artifacts_dir)
        shutil.rmtree(self.log_dir)
        # TODO remove reports dirs

    def setup_log(self):
        try:
            loglevel = self.LOG_LEVELS[self.log_level.upper()]
        except KeyError:
            msg = "'%s' is not a valid log level, check python logging module docs."
            raise dexy.exceptions.UserFeedback(msg % self.log_level)

        self.log = logging.getLogger('dexy')
        self.log.setLevel(loglevel)

        handler = logging.handlers.RotatingFileHandler(
                self.log_path(),
                encoding="utf-8")

        formatter = logging.Formatter(self.log_format)
        handler.setFormatter(formatter)

        self.log.addHandler(handler)

    def setup_db(self):
        db_class = dexy.database.Database.aliases[self.db_alias]
        self.db = db_class(self)

    def setup_docs(self):
        for arg in self.args:
            self.log.debug("Processing arg %s" % arg)
            doc = self.create_doc_from_arg(arg)
            if not doc:
                raise Exception("no doc created for %s" % arg)
            doc.wrapper = self
            doc.setup()
            self.docs_to_run.append(doc)

    def create_doc_from_arg(self, arg, *children, **kwargs):
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

            if children:
                raise Exception("Shouldn't have children if arg is a list")

            alias, pattern = dexy.parser.AbstractSyntaxTree.qualify_key(arg[0])
            return dexy.task.Task.create(alias, pattern, **arg[1])

        elif isinstance(arg, basestring):
            alias, pattern = dexy.parser.AbstractSyntaxTree.qualify_key(arg[0])
            return dexy.task.Task.create(alias, pattern, *children, **kwargs)

        else:
            raise Exception("unknown arg type %s for arg %s" % (arg.__class__.__name__, arg))

    def save_db(self):
        self.db.save()

    ## DOCUMENTED above here..

    def run_docs(self, *docs):
        """
        Convenience method for testing to add docs and then run them.
        """
        self.setup_dexy_dirs()
        self.docs_to_run = docs
        self.run()

    def register(self, task):
        """
        Register a task with the wrapper
        """
        self.tasks[task.key_with_class()] = task

    def registered_docs(self):
        return [d for d in self.tasks.values() if isinstance(d, dexy.doc.Doc)]

    def registered_doc_names(self):
        return [d.name for d in self.registered_docs()]

    def reports_dirs(self):
        return [c.REPORTS_DIR for c in dexy.reporter.Reporter.plugins]

    def report(self, *reporters):
        """
        Runs reporters. Either runs reporters which have been passed in or, if
        none, then runs all available reporters which have ALLREPORTS set to
        true.
        """
        if not reporters:
            reporters = [c() for c in dexy.reporter.Reporter.plugins if c.ALLREPORTS]

        for reporter in reporters:
            self.log.debug("Running reporter %s" % reporter.ALIASES[0])
            reporter.run(self)

    def get_child_hashes_in_previous_batch(self, parent_hashstring):
        return self.db.get_child_hashes_in_previous_batch(self.batch_id, parent_hashstring)

    def load_doc_config(self):
        """
        Look for document config files in current working dir and load them.
        """
        parser_aliases = dexy.parser.Parser.aliases
        for k in parser_aliases.keys():
            if os.path.exists(k):
                self.log.debug("found doc config file '%s'" % k)

                parser = parser_aliases[k](self)

                with open(k, "r") as f:
                    self.doc_config = f.read()
                    parser.parse(self.doc_config)

                break

    def setup_config(self):
        self.setup_dexy_dirs()
        self.setup_log()
        self.load_doc_config()

    def cleanup_partial_run(self):
        if hasattr(self, 'db'):
            # TODO remove any entries which don't have
            self.db.save()

    def setup_graph(self):
        """
        Creates a dot representation of the tree.
        """
        graph = ["digraph G {"]

        for task in self.tasks.values():
            if hasattr(task, 'artifacts'):
                task_label = task.key_with_class().replace("|", "\|")
                label = """   "%s" [shape=record, label="%s\\n\\n""" % (task.key_with_class(), task_label)
                for child in task.artifacts:
                    label += "%s\l" % child.key_with_class().replace("|", "\|")

                label += "\"];"
                graph.append(label)

                for child in task.children:
                    if not child in task.artifacts:
                        graph.append("""   "%s" -> "%s";""" % (task.key_with_class(), child.key_with_class()))

            elif "Artifact" in task.__class__.__name__:
                pass
            else:
                graph.append("""   "%s" [shape=record];""" % task.key_with_class())
                for child in task.children:
                    graph.append("""   "%s" -> "%s";""" % (task.key_with_class(), child.key_with_class()))


        graph.append("}")

        self.graph = "\n".join(graph)

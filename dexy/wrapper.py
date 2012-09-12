from dexy.reporter import Reporter
import dexy.database
import dexy.doc
import json
import logging
import logging.handlers
import os

class Wrapper(object):
    """
    Class that assists in interacting with Dexy, including running Dexy.
    """
    DEFAULT_ARTIFACTS_DIR = 'artifacts'
    DEFAULT_CONFIG_FILE = 'dexy.conf' # Specification of dexy-wide config options.
    DEFAULT_DANGER = False
    DEFAULT_DB_ALIAS = 'sqlite3'
    DEFAULT_DB_FILE = 'dexy.sqlite3'
    DEFAULT_DOC_FILE = "dexy.docs" # Specification of which docs to process.
    DEFAULT_DISABLE_TESTS = False
    DEFAULT_DRYRUN = False
    DEFAULT_EXCLUDE = ''
    DEFAULT_GLOBALS = ''
    DEFAULT_HASHFUNCTION = 'md5'
    DEFAULT_IGNORE_NONZERO_EXIT = False
    DEFAULT_LOG_DIR = 'logs'
    DEFAULT_LOG_FILE = 'dexy.log'
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_LOG_LEVEL = 'DEBUG'
    DEFAULT_DONT_USE_CACHE = False
    DEFAULT_REPORTS = 'output'
    DEFAULT_RECURSE = True
    DEFAULT_SILENT = False

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

    def update_attributes_from_config(self, config):
        for key, value in config.iteritems():
            if not key in self.SKIP_KEYS:
                corrected_key = self.RENAME_PARAMS.get(key, key)
                if not hasattr(self, corrected_key):
                    raise Exception("no default for %s" % corrected_key)
                setattr(self, corrected_key, value)

    def __init__(self, *args, **kwargs):
        # Initialize attributes to their defaults
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


        self.update_attributes_from_config(kwargs)

        self.args = args
        self.db_path = os.path.join(self.artifacts_dir, self.db_file)
        self.log_path = os.path.join(self.log_dir, self.log_file)
        self.registered = []
        self.reports_dirs = [c.REPORTS_DIR for c in Reporter.plugins]

    @classmethod
    def default_config(klass):
        conf = klass().__dict__.copy()

        # Remove any attributes that aren't config options
        del conf['args']
        del conf['db_path']
        del conf['log_path']
        del conf['registered']
        del conf['reports_dirs']

        for cl_key, internal_key in klass.RENAME_PARAMS.iteritems():
            conf[cl_key] = conf[internal_key]
            del conf[internal_key]

        return conf

    def setup_run(self, setup_docs=True):
        self.setup_dexy_dirs()
        self.setup_log()
        self.setup_db()
        if setup_docs:
            self.setup_docs()

    def setup_read(self, batch_id=None):
        """
        Set up the  in 'read' mode for reviewing last batch.
        """
        self.setup_log()
        self.setup_db()

        if batch_id:
            self.batch_id = batch_id
        else:
            self.batch_id = self.db.max_batch_id()

    def setup_dexy_dirs(self):
        """
        Create the artifacts and logs directories if they don't exist already.
        """
        if not os.path.exists(self.artifacts_dir):
            os.mkdir(self.artifacts_dir)
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)

    def setup_log(self):
        self.log = logging.getLogger('dexy')
        self.log.setLevel(logging.DEBUG)

        handler = logging.handlers.RotatingFileHandler(
                self.log_path,
                encoding="UTF-8")

        formatter = logging.Formatter(self.log_format)
        handler.setFormatter(formatter)

        self.log.addHandler(handler)
        self.log.debug("================================================== Starting new dexy run.")

    def setup_docs(self):
        """
        Processes args which may be doc objects or filenames with wildcards.
        """
        if not hasattr(self, 'docs'):
            self.docs = []

        for arg in self.args:
            self.log.debug("Processing arg %s" % arg)
            if isinstance(arg, dexy.doc.Doc) or isinstance(arg, dexy.doc.PatternDoc):
                doc = arg

            elif isinstance(arg, list):
                if not isinstance(arg[0], basestring):
                    raise Exception("First arg %s should be a string" % arg[0])
                if not isinstance(arg[1], dict):
                    raise Exception("Second arg %s should be a dict" % arg[1])

                if not "*" in arg[0]:
                    doc = dexy.doc.Doc(arg[0], **arg[1])
                else:
                    # This is a pattern doc or real doc TODO better way to verify?
                    doc = dexy.doc.PatternDoc(arg[0], **arg[1])

            elif isinstance(arg, basestring):
                doc = dexy.doc.PatternDoc(arg)

            else:
                raise Exception("unknown arg type %s for arg %s" % (arg.__class__.__name__, arg))

            doc.wrapper = self
            doc.setup()

            self.docs.append(doc)

    def setup_db(self):
        db_class = dexy.database.Database.aliases[self.db_alias]
        self.db = db_class(self)
        self.batch_id = self.db.next_batch_id()

    def save_db(self):
        self.db.save()

    def run(self):
        self.setup_run()

        self.log.debug("batch id is %s" % self.batch_id)

        for doc in self.docs:
            for task in doc:
                task()

        self.save_db()

    def run_tasks(self, *tasks):
        for task in tasks:
            for t in task:
                t()

    def register(self, task):
        """
        Register a task with the wrapper
        """
        self.registered.append(task)

    def registered_docs(self):
        """
        Filter all registered tasks for just Doc instances.
        """
        return [t for t in self.registered if isinstance(t, dexy.doc.Doc)]

    def report(self, *reporters):
        """
        Runs reporters. Either runs reporters which have been passed in or, if
        none, then runs all available reporters which have ALLREPORTS set to
        true.
        """
        if len(reporters) == 0:
            reporters = [c() for c in Reporter.plugins if c.ALLREPORTS]

        for reporter in reporters:
            self.log.debug("Running reporter %s" % reporter.ALIASES[0])
            reporter.run(self)

    def get_child_hashes_in_previous_batch(self, parent_hashstring):
        return self.db.get_child_hashes_in_previous_batch(self.batch_id, parent_hashstring)

    def load_config(self):
        """
        Look for a config file in current working dir and loads it.
        """
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                conf = json.load(f)

            self.update_attributes_from_config(conf)

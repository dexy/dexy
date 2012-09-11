from dexy.reporter import Reporter
import dexy.doc
import dexy.database
import logging
import logging.handlers
import os

class Wrapper(object):
    """
    Class that assists in interacting with Dexy, including running Dexy.
    """
    def __init__(self, *args, **kwargs):
        # Default Values
        self.artifacts_dir = 'artifacts'
        self.config_file = '.dexy'
        self.db_alias = 'sqlite3'
        self.db_file = os.path.join(self.artifacts_dir, 'dexy.sqlite3')
        self.log_dir = 'logs'
        self.log_file = 'dexy.log'
        self.log_path = os.path.join(self.log_dir, self.log_file)
        self.log_level = 'DEBUG'
        self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.reports = ['output']

        for key, value in kwargs.iteritems():
            if not hasattr(self, key):
                raise Exception("no default for %s" % key)

            setattr(self, key, value)

        self.args = args
        self.reports_dirs = [c.REPORTS_DIR for c in Reporter.plugins]
        self.registered = []

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

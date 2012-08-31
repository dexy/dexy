from dexy.doc import Doc
from dexy.doc import PatternDoc
from dexy.params import RunParams
from dexy.reporter import Reporter
from ordereddict import OrderedDict
import logging
import os
import sqlite3

class Runner(object):
    """
    Class that manages a dexy run.
    """
    def __init__(self, params=RunParams(), args=[]):
        self.params = params
        self.args = args
        self.registered = []
        self.reports_dirs = [c.REPORTS_DIR for c in Reporter.plugins]

    def setup_dexy_dirs(self):
        """
        Create the artifacts and logs directories if they don't exist already.
        """
        if not os.path.exists(self.params.artifacts_dir):
            os.mkdir(self.params.artifacts_dir)
        if not os.path.exists(self.params.log_dir):
            os.mkdir(self.params.log_dir)

    def setup_log(self):
        self.log = logging.getLogger('dexy')
        self.log.setLevel(logging.DEBUG)

        handler = logging.handlers.RotatingFileHandler(
                self.params.log_path,
                encoding="UTF-8")

        formatter = logging.Formatter(self.params.log_format)
        handler.setFormatter(formatter)

        self.log.addHandler(handler)
        self.log.debug("================================================== Starting new dexy run.")

    def setup_docs(self):
        """
        Processes args which may be doc objects or filenames with wildcards.
        """
        self.docs = []
        for arg in self.args:
            self.log.debug("Processing arg %s" % arg)
            if isinstance(arg, Doc) or isinstance(arg, PatternDoc):
                doc = arg

            elif isinstance(arg, list):
                if not isinstance(arg[0], basestring):
                    raise Exception("First arg %s should be a string" % arg[0])
                if not isinstance(arg[1], dict):
                    raise Exception("Second arg %s should be a dict" % arg[1])

                if not "*" in arg[0]:
                    doc = Doc(arg[0], **arg[1])
                else:
                    # This is a pattern doc or real doc TODO better way to verify?
                    doc = PatternDoc(arg[0], **arg[1])

            elif isinstance(arg, basestring):
                doc = PatternDoc(arg)

            else:
                raise Exception("unknown arg type %s for arg %s" % (arg.__class__.__name__, arg))

            doc.runner = self
            doc.setup()

            self.docs.append(doc)

    def setup_db_conn(self):
        self.conn = sqlite3.connect(self.params.db_file)
        self.conn.row_factory = sqlite3.Row

    def save_db(self):
        self.conn.commit()
        self.conn.close()

    def run(self):
        self.setup_dexy_dirs()
        self.setup_log()
        self.setup_db_conn()
        self.setup_docs()

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
        Register a task with the runner.
        """
        self.registered.append(task)

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

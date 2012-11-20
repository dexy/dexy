from dexy.common import OrderedDict
from dexy.notify import Notify
import dexy.database
import dexy.doc
import dexy.parser
import dexy.reporter
import logging
import logging.handlers
import os
import shutil
import time

class Wrapper(object):
    """
    Class that assists in interacting with Dexy, including running Dexy.
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
            'exclude' : '.git, .svn, tmp, cache',
            'exclude_also' : '',
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
        self.initialize_attribute_defaults()
        self.update_attributes_from_kwargs(kwargs)

        self.args = args
        self.root_nodes = []
        self.tasks = OrderedDict()
        self.state = None

        self.notifier = Notify(self)

    def tasks_by_elapsed(self, n=10):
        return sorted(self.tasks.values(), key=lambda task: hasattr(task, 'doc') and task.elapsed or None, reverse=True)[0:n]

    def initialize_attribute_defaults(self):
        for name, value in self.DEFAULTS.iteritems():
            setattr(self, name, value)

    def update_attributes_from_kwargs(self, kwargs):
        for key, value in kwargs.iteritems():
            if not key in self.DEFAULTS:
                raise Exception("invalid kwargs %s" % key)
            setattr(self, key, value)

    def db_path(self):
        return os.path.join(self.artifacts_dir, self.db_file)

    def log_path(self):
        return os.path.join(self.log_dir, self.log_file)

    def ete_tree(self):
        try:
            from ete2 import Tree
            t = Tree()
        except ImportError:
            return None

        t.name = "%s" % self.batch_id

        def add_children(doc, doc_node):
            for child in doc.children:
                child_node = doc_node.add_child(name=child.key_with_class())
                add_children(child, child_node)

        for doc in self.root_nodes:
            doc_node = t.add_child(name=doc.key_with_class())
            add_children(doc, doc_node)

        return t

    def run(self):
        self.batch_info = {}
        self.batch_info['start_time'] = time.time()

        self.setup_run()
        self.log.debug("batch id is %s" % self.batch_id)

        self.log.debug("running dexy with config:")
        for k in sorted(self.__dict__):
            if not k in ('ast', 'args', 'db', 'log', 'root_nodes', 'tasks', 'notifier'):
                self.log.debug("  %s: %s" % (k, self.__dict__[k]))

        if self.target:
            self.log.debug("Limiting root nodes to %s" % self.target)
            docs = [doc for doc in self.root_nodes if doc.key.startswith(self.target)]
            self.log.debug("Processing nodes %s" % ", ".join(doc.key_with_class() for doc in docs))
        else:
            docs = self.root_nodes

        self.state = 'populating'

        for doc in docs:
            for task in doc:
                task()

        self.state = 'settingup'

        for doc in docs:
            for task in doc:
                task()

        self.state = 'running'

        for doc in docs:
            for task in doc:
                task()

        self.state = 'complete'

        self.save_db()
        self.setup_graph()

        self.batch_info['end_time'] = time.time()
        self.batch_info['elapsed'] = self.batch_info['end_time'] - self.batch_info['start_time']

    def setup_run(self):
        self.check_dexy_dirs()
        self.setup_log()
        self.setup_db()

        self.batch_id = self.db.next_batch_id()

        if not self.root_nodes:
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

    def setup_docs(self):
        for arg in self.args:
            self.log.debug("Processing arg %s" % arg)
            doc = self.create_doc_from_arg(arg)
            if not doc:
                raise Exception("no doc created for %s" % arg)
            doc.wrapper = self
            self.root_nodes.append(doc)

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

            alias, pattern = dexy.parser.Parser.qualify_key(arg[0])
            return dexy.task.Task.create(alias, pattern, **arg[1])

        elif isinstance(arg, basestring):
            alias, pattern = dexy.parser.Parser.qualify_key(arg[0])
            return dexy.task.Task.create(alias, pattern, *children, **kwargs)

        else:
            raise Exception("unknown arg type %s for arg %s" % (arg.__class__.__name__, arg))

    def save_db(self):
        self.db.save()

    def run_docs(self, *docs):
        """
        Convenience method for testing to add docs and then run them.
        """
        self.setup_dexy_dirs()
        self.root_nodes = docs
        self.run()

    def register(self, task):
        """
        Register a task with the wrapper
        """
        self.tasks[task.key_with_class()] = task
        self.notifier.subscribe("newchild", task.handle_newchild)

    def registered_docs(self):
        return [d for d in self.tasks.values() if isinstance(d, dexy.doc.Doc)]

    def registered_doc_names(self):
        return [d.name for d in self.registered_docs()]

    def reports_dirs(self):
        return [c.REPORTS_DIR for c in dexy.reporter.Reporter.plugins]

    def report(self):
        """
        Runs reporters. Either runs reporters which have been passed in or, if
        none, then runs all available reporters which have ALLREPORTS set to
        true.
        """
        if self.reports:
            self.log.debug("generating user-specified reports '%s'" % self.reports)
            reporters = []
            for alias in self.reports.split():
                reporter_class = dexy.reporter.Reporter.aliases[alias]
                self.log.debug("initializing reporter %s for alias %s" % (reporter_class.__name__, alias))
                reporters.append(reporter_class())
        else:
            self.log.debug("initializing all reporters where ALLREPORTS is True")
            reporters = [c() for c in dexy.reporter.Reporter.plugins if c.ALLREPORTS]

        for reporter in reporters:
            self.log.debug("running reporter %s" % reporter.ALIASES[0])
            reporter.run(self)

    def get_child_hashes_in_previous_batch(self, parent_hashstring):
        return self.db.get_child_hashes_in_previous_batch(self.batch_id, parent_hashstring)

    def load_doc_config(self):
        """
        Look for document config files in current working tree and load them.
        """
        exclude = self.exclude_dirs()
        self.ast = dexy.parser.AbstractSyntaxTree()
        self.ast.wrapper = self
        self.doc_config = OrderedDict()

        for dirpath, dirnames, filenames in os.walk("."):
            self.log.debug("looking for doc config files in '%s'" % dirpath)

            nodexy_file = os.path.join(dirpath, '.nodexy')
            if os.path.exists(nodexy_file):
                self.log.debug("  skipping directory '%s' and its children because .nodexy file found" % dirpath)
                dirnames[:] = []
            else:
                # no excludes or .nodexy file, this dir is ok to process
                for alias in dexy.parser.Parser.aliases.keys():
                    config_file_in_directory = os.path.join(dirpath, alias)
                    if os.path.exists(config_file_in_directory):
                        parser = dexy.parser.Parser.aliases[alias](self)
                        parser.ast = self.ast
                        with open(config_file_in_directory, "r") as f:
                            config_text = f.read()

                        self.log.debug("found doc config file '%s':\n%s" % (config_file_in_directory, config_text))
                        self.doc_config[dirpath] = config_text
                        parser.build_ast(dirpath, config_text)

                    self.log.debug("Removing any child directories of '%s' that match excludes..." % dirpath)
                    for x in exclude:
                        if x in dirnames:
                            skipping_dir = os.path.join(dirpath, x)
                            self.log.debug("  skipping directory '%s' because it matches exclude '%s'" % (skipping_dir, x))
                            dirnames.remove(x)

        self.log.debug("AST completed:")
        self.ast.debug(self.log)
        self.log.debug("walking AST:")
        self.root_nodes = self.ast.walk()

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
#        graph = self.ete_tree()
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

    def exclude_dirs(self):
        exclude_str = self.exclude
        if self.exclude_also:
            exclude_str += ",%s" % self.exclude_also
        exclude = [d.strip() for d in exclude_str.split(",")]

        exclude.append(self.artifacts_dir)
        exclude.append(self.log_dir)
        exclude.extend(self.reports_dirs())

        return exclude

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

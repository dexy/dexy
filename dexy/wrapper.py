from dexy.exceptions import DeprecatedException
from dexy.exceptions import InternalDexyProblem
from dexy.exceptions import UserFeedback
from dexy.utils import file_exists
from dexy.utils import s
import dexy.batch
import dexy.doc
import dexy.parser
import dexy.reporter
import dexy.utils
import logging
import logging.handlers
import os
import posixpath
import shutil
import time

class Wrapper(object):
    """
    Class that manages run configuration and state and provides utilities such
    as logging and setting up/tearing down workspace on file system.
    """
    _required_dirs = ['artifacts_dir', 'log_dir']

    def __init__(self, **kwargs):
        self.initialize_attribute_defaults()
        self.update_attributes_from_kwargs(kwargs)

        self.nodes = {}
        self.roots = []

        if self.dexy_dirs_exist():
            self.setup_log()
            self.project_root = os.path.abspath(os.getcwd())
            self.filemap = self.map_files()

    # Attributes
    def initialize_attribute_defaults(self):
        """
        Applies the values in defaults dict to this wrapper instance.
        """
        for name, value in dexy.utils.defaults.iteritems():
            setattr(self, name, value)

    def update_attributes_from_kwargs(self, kwargs):
        """
        Updates instance values from a dictionary of kwargs, checking that the
        attribute names are also present in defaults dict.
        """
        for key, value in kwargs.iteritems():
            if not key in dexy.utils.defaults:
                msg = "invalid kwarg '%s' being passed to wrapper, not defined in defaults dict" 
                raise InternalDexyProblem(msg % key)
            setattr(self, key, value)

    # Dexy Dirs
    def iter_dexy_dirs(self):
        """
        Iterate over the required dirs (e.g. artifacts, logs)
        """
        for d in self.__class__._required_dirs:
            dirpath = self.__dict__[d]
            safety_filepath = os.path.join(dirpath, self.safety_filename)
            try:
                stat = os.stat(dirpath)
            except OSError:
                stat = None

            if stat:
                if not file_exists(safety_filepath):
                    msg = s("""You need to manually delete the '%s' directory
                    and then run 'dexy setup' to create new directories. This
                    should just be a once-off issue due to a change in dexy to
                    prevent accidentally deleting directories which dexy does
                    not create.
                    """) % dirpath
                    raise UserFeedback(msg)

            yield (dirpath, safety_filepath, stat)

    def dexy_dirs_exist(self):
        """
        Returns a boolean indicating whether dexy dirs exist.
        """
        return all(file_exists(d[0]) for d in self.iter_dexy_dirs())

    def assert_dexy_dirs_exist(self):
        """
        Raise a UserFeedback error if user has tried to run dexy without
        setting up necessary directories first.
        """
        if not self.dexy_dirs_exist():
            msg = "You need to run 'dexy setup' in this directory first."
            raise UserFeedback(msg)

    def create_dexy_dirs(self):
        """
        Creates the directories needed for dexy to run. Does not complain if
        directories are already present.
        """
        for dirpath, safety_filepath, dirstat in self.iter_dexy_dirs():
            if not dirstat:
                os.mkdir(dirpath)
                with open(safety_filepath, 'w') as f:
                    f.write("This directory was created by dexy.")

    def remove_dexy_dirs(self, reports=False):
        """
        Removes directories created by dexy. If 'reports' argument is true,
        also removes directories created by dexy's reports.
        """
        for dirpath, safety_filepath, dirstat in self.iter_dexy_dirs():
            if dirstat:
                print "removing directory '%s'" % dirpath
                shutil.rmtree(dirpath)

        if reports:
            if isinstance(reports, bool):
                # return an iterator over all reporters
                reports=dexy.reporter.Reporter

            for report in reports:
                report.remove_reports_dir()

    def clean_dexy_dirs(self):
        """
        Cleans up files that aren't needed at the start of new runs, like prev
        run's temporary working directories.
        """
        # TODO make sure we are in project dir.
        dirs = [self.filter_ws()]
        for d in dirs:
            try:
                shutil.rmtree(d)
            except OSError:
                pass

    # Logging
    def log_path(self):
        """
        Returns path to logfile.
        """
        return os.path.join(self.log_dir, self.log_file)

    def filter_ws(self):
        return os.path.join(self.artifacts_dir, self.workspace)

    def setup_log(self):
        """
        Creates a logger and assigns it to 'log' attribute of wrapper.
        """
        formatter = logging.Formatter(self.log_format)
        log_level = dexy.utils.logging_log_level(self.log_level)

        handler = logging.handlers.RotatingFileHandler(
                self.log_path(),
                encoding="utf-8")

        handler.setFormatter(formatter)

        self.log = logging.getLogger('dexy')
        self.log.setLevel(log_level)
        self.log.addHandler(handler)

    # Project files
    def exclude_dirs(self):
        """
        Returns list of directory names which should be excluded from dexy processing.
        """
        exclude_str = self.exclude
        if self.exclude_also:
            exclude_str += ",%s" % self.exclude_also

        exclude = [d.strip() for d in exclude_str.split(",")]
        exclude += [d[0] for d in self.iter_dexy_dirs()]
        exclude += self.reports_dirs()

        return exclude

    def reports_dirs(self):
        """
        Returns list of directories which are written to by reporters.
        """
        dirs_and_nones = [i.setting('dir') for i in dexy.reporter.Reporter]
        return [d for d in dirs_and_nones if d]

    def map_files(self):
        """
        Generates a map of files present in the project directory.
        """
        exclude = self.exclude_dirs()
        filemap = {}

        for dirpath, dirnames, filenames in os.walk('.'):
            for x in exclude:
                if x in dirnames:
                    dirnames.remove(x)

            if '.nodexy' in filenames:
                dirnames[:] = []
            elif 'pip-delete-this-directory.txt' in filenames:
                msg = s("""pip left an old build/ file lying around,
                please remove this before running dexy""")
                raise UserFeedback(msg)
            else:
                for filename in filenames:
                    filepath = posixpath.normpath(posixpath.join(dirpath, filename))
                    filemap[filepath] = {}
                    filemap[filepath]['stat'] = os.stat(os.path.join(dirpath, filename))
                    filemap[filepath]['ospath'] = os.path.normpath(os.path.join(dirpath, filename))
                    filemap[filepath]['dir'] = os.path.normpath(dirpath)
        return filemap

    def file_available(self, filepath):
        """
        Does the file exist and is it available to dexy?
        """
        return filepath in self.filemap

    # Running Dexy
    def add_node(self, node):
        """
        Add new nodes which are not children of other nodes.
        """
        key = node.key_with_class()
        self.nodes[key] = node
        self.roots.append(node)

    def run(self, *docs):
        self.assert_dexy_dirs_exist()
        self.clean_dexy_dirs()

        self.batch = dexy.batch.Batch(self)
        self.batch.start_time = time.time()

        if docs:
            self.nodes = dict((d.key_with_class(), d) for d in docs)
            self.roots = list(docs)
            run_roots = self.roots

        else:
            if not self.nodes:
                ast = self.parse_configs()
                ast.walk()

            if self.target:
                run_roots = [n for n in self.roots if n.key == self.target]
                if not run_roots:
                    run_roots = [n for n in self.roots if n.key.startswith(self.target)]
                if not run_roots:
                    run_roots = [n for n in self.nodes.values() if n.key.startswith(self.target)]
            else:
                run_roots = self.roots

        for root_node in run_roots:
            for task in root_node:
                task()

        self.batch.end_time = time.time()
        self.batch.save_to_file()

    def qualify_key(self, key):
        """
        A full node key is of the form alias:pattern where alias indicates
        the type of node to be created. This method determines the alias if it
        is not specified explicitly, and returns the alias, pattern tuple.
        """
        if not key:
            msg = "trying to call qualify_key with key of '%s'!"
            raise DeprecatedException(msg % key)

        if ":" in key:
            # split qualified key into alias & pattern
            alias, pattern = key.split(":")
        else:
            # this is an unqualified key, figure out its alias
            pattern = key

            # Allow '.ext' instead of '*.ext', shorter + easier for YAML
            if pattern.startswith(".") and not pattern.startswith("./"):
                if not self.file_available(pattern):
                    pattern = "*%s" % pattern

            filepath = pattern.split("|")[0]
            if self.file_available(filepath):
                alias = 'doc'
            elif (not "." in pattern) and (not "|" in pattern):
                alias = 'bundle'
            elif "*" in pattern:
                alias = 'pattern'
            else:
                alias = 'doc'

        return alias, pattern

    def standardize_alias(self, alias):
        """
        Nodes can have multiple aliases, standardize on first one in list.
        """
        # TODO should we just make it so nodes only have 1 alias?
        node_class, _ = dexy.node.Node.plugins[alias]
        return node_class.aliases[0]

    def standardize_key(self, key):
        """
        Standardizes the key by making the alias explicit and standardized, so
        we don't create 2 entires in the AST for what turns out to be the same
        node/task.
        """
        alias, pattern = self.qualify_key(key)
        alias = self.standardize_alias(alias)
        return "%s:%s" % (alias, pattern)

    def join_dir(self, directory, key):
        if directory == ".":
            return key
        else:
            starts_with_dot = key.startswith(".") and not key.startswith("./")
            if starts_with_dot:
                path_to_key = os.path.join(directory, key)
                if not self.file_available(path_to_key):
                    key = "*%s" % key
            return posixpath.join(directory, key)

    def parse_configs(self):
        """
        Look for document config files in current working tree and load them.
        Return an Abstract Syntax Tree with information about nodes to be
        processed.
        """
        parser_aliases = sorted(dexy.parser.Parser.plugins.keys())

        # collect all doc config files in project dir
        config_files = []
        for alias in parser_aliases:
            for filepath, fileinfo in self.filemap.iteritems():
                if os.path.split(filepath)[1] == alias:
                    config_file_info = (fileinfo['ospath'], fileinfo['dir'], alias,)
                    config_files.append(config_file_info)

        # warn if we don't find any configs
        if len(config_files) == 0:
            msg = "didn't find any document config files (like %s)"
            print msg % (", ".join(parser_aliases))

        # parse each config file and add to ast
        ast = dexy.parser.AbstractSyntaxTree(self)

        for config_file, dirname, alias in config_files:
            with open(config_file, "r") as f:
                config_text = f.read()
            parser = dexy.parser.Parser.create_instance(alias, self, ast)
            parser.parse(dirname, config_text)

        return ast

    # Old
    def report(self):
        if self.reports:
            self.log.debug("generating user-specified reports '%s'" % self.reports)
            reporters = []
            for alias in self.reports.split():
                reporter = dexy.reporter.Reporter.create_instance(alias)
                reporters.append(reporter)
        else:
            self.log.debug("no reports specified, generating all reports for which 'default' setting is True")
            reporters = [i for i in dexy.reporter.Reporter if i.setting('default')]

        for reporter in reporters:
            self.log.debug("running reporter %s" % reporter.aliases[0])
            reporter.run(self)

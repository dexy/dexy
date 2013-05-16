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
import uuid

class Wrapper(object):
    """
    Class that manages run configuration and state and provides utilities such
    as logging and setting up/tearing down workspace on file system.
    """
    _required_dirs = ['artifacts_dir', 'log_dir']

    state_transitions = (
            (None, 'new'),
            ('new', 'valid'),
            ('valid', 'valid'),
            ('valid', 'walked'),
            ('walked', 'checked'),
            ('checked', 'running'),
            ('running', 'error'),
            ('running', 'ran'),
            )

    def validate_state(self, state=None):
        """
        Checks that the instance is in the expected state, and validates
        attributes for the state.
        """
        if state:
            assert self.state == state
        else:
            state = self.state

        if state == 'new':
            assert not self.state_history
            assert self.project_root
        elif state == 'valid':
            pass
        elif state == 'walked':
            assert self.batch
            assert self.nodes
            assert self.roots
            assert self.filemap
            for node in self.nodes.values():
                assert node.state == 'new'
        elif state == 'checked':
            for node in self.nodes.values():
                assert node.state in ('uncached', 'consolidated', 'inactive',), node.state
        elif state == 'ran':
            for node in self.nodes.values():
                assert node.state in ('ran', 'consolidated', 'inactive'), node.state
        else:
            raise dexy.exceptions.InternalDexyProblem(state)

    def __init__(self, **kwargs):
        self.initialize_attribute_defaults()
        self.update_attributes_from_kwargs(kwargs)
        self.project_root = os.path.abspath(os.getcwd())
        self.state = None
        self.transition('new')

    def transition(self, new_state):
        dexy.utils.transition(self, new_state)

    def setup_for_valid(self):
        self.setup_log()

    def to_valid(self):
        if not self.dexy_dirs_exist():
            msg = "Should not attempt to enter 'valid' state unless dexy dirs exist."
            raise dexy.exceptions.InternalDexyProblem(msg)
        self.setup_for_valid()
        self.transition('valid')

    def walk(self):
        self.nodes = {}
        self.roots = []
        self.batch = dexy.batch.Batch(self)
        self.filemap = self.map_files()
        self.ast = self.parse_configs()
        self.ast.walk()

    def to_walked(self):
        self.walk()
        self.transition('walked')

    def check(self):
        # Clean and reset working dirs.
        self.reset_work_cache_dir()
        if not os.path.exists(self.this_cache_dir()):
            self.create_cache_dir_with_sub_dirs(self.this_cache_dir())

        # Load information about arguments from previous batch.
        self.load_node_argstrings()

        self.check_cache()
        self.consolidate_cache()

        # Save information about this batch's arguments for next time.
        self.save_node_argstrings()

    def check_cache(self):
        """
        Check whether all required files are already cached from a previous run
        """
        for node in self.roots:
            node.check_is_cached()

    def consolidate_cache(self):
        """
        Move all cache files from last/ cache to this/ cache
        """
        for node in self.roots:
            node.consolidate_cache_files()

        self.trash(self.last_cache_dir())

    def to_checked(self):
        self.check()
        self.transition('checked')

    # Cache dirs
    def this_cache_dir(self):
        return os.path.join(self.artifacts_dir, "this")

    def last_cache_dir(self):
        return os.path.join(self.artifacts_dir, "last")

    def work_cache_dir(self):
        return os.path.join(self.artifacts_dir, "work")

    def trash_dir(self):
        return os.path.join(self.project_root, ".trash")

    def create_cache_dir_with_sub_dirs(self, cache_dir):
        os.mkdir(cache_dir)
        hexes = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
        for c in hexes:
            for d in hexes:
                os.mkdir(os.path.join(cache_dir, "%s%s" % (c,d)))

    def trash(self, d, d_exists=None):
        """
        Move the passed file path (if it exists) into the .trash directory.
        """
        if d_exists or os.path.exists(d):
            if not self.is_location_in_project_dir(d):
                msg = "trying to trash '%s', but this is not in project dir '%s"
                msgargs = (d, self.project_root)
                raise dexy.exceptions.InternalDexyProblem(msg % msgargs)

            trash_dir = self.trash_dir()

            if not os.path.exists(trash_dir):
                os.mkdir(trash_dir)

            move_to = os.path.join(trash_dir, str(uuid.uuid4()))
            shutil.move(d, move_to)

    def empty_trash(self):
        try:
            shutil.rmtree(self.trash_dir())
        except OSError as e:
            if not "No such file or directory" in str(e):
                raise e

    def reset_work_cache_dir(self):
        # remove work/ dir leftover from previous run (if any) and create a new
        # work/ dir for this run
        work_dir = self.work_cache_dir()
        self.trash(work_dir)
        self.create_cache_dir_with_sub_dirs(work_dir)

    def run(self):
        self.transition('running')

        self.batch.start_time = time.time()

        if self.target:
            matches = self.roots_matching_target()

        try:
            for node in self.roots:
                if self.target:
                    if not node in matches:
                        continue

                for task in node:
                    task()

        except UserFeedback as e:
            print e.message
            self.error = e
            self.transition('error')
            if self.debug:
                raise e
        except InternalDexyProblem as e:
            print e.message
            self.error = e
            self.transition('error')
            if self.debug:
                raise e
        except Exception as e:
            print e
            self.error = e
            self.transition('error')
            if self.debug:
                raise e
        else:
            self.transition('ran')
            self.batch.end_time = time.time()
            self.batch.save_to_file()
            shutil.move(self.this_cache_dir(), self.last_cache_dir())
            self.empty_trash()

    def roots_matching_target(self):
        matches = [n for n in self.roots if n.key == self.target]
        if not matches:
            matches = [n for n in self.roots if n.key.startswith(self.target)]
        if not matches:
            matches = [n for n in self.nodes.values() if n.key.startswith(self.target)]
        return matches

    def run_from_new(self):
        self.to_valid()
        self.to_walked()
        self.to_checked()
        if self.dry_run:
            print "dry run only"
        else:
            self.run()

    def run_docs(self, *docs):
        self.to_valid()

        # do a custom walk() method
        self.roots = docs
        self.nodes = dict((node.key_with_class(), node) for node in self.roots)
        self.filemap = self.map_files()
        self.batch = dexy.batch.Batch(self)
        self.transition('walked')

        self.to_checked()
        self.run()

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

    # Store Args
    def pickle_lib(self):
        return dexy.utils.pickle_lib(self)

    def node_argstrings_filename(self):
        return os.path.join(self.artifacts_dir, 'batch.args.pickle')

    def save_node_argstrings(self):
        """
        Save string representation of node args to check if they have changed.
        """
        arg_info = {}

        for node in self.nodes.values():
            arg_info[node.key_with_class()] = node.sorted_arg_string()

        with open(self.node_argstrings_filename(), 'wb') as f:
            pickle = self.pickle_lib()
            pickle.dump(arg_info, f)

    def load_node_argstrings(self):
        """
        Load saved node arg strings into a hash so nodes can check if their
        args have changed.
        """
        try:
            with open(self.node_argstrings_filename(), 'rb') as f:
                pickle = self.pickle_lib()
                self.saved_args = pickle.load(f)
        except IOError:
            self.saved_args = {}

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

    def remove_dexy_dirs(self):
        for dirpath, safety_filepath, dirstat in self.iter_dexy_dirs():
            if dirstat:
                self.trash(dirpath, True)
        self.empty_trash()

    def remove_reports_dirs(self, reports=True, keep_empty_dir=False):
        if reports:
            if isinstance(reports, bool):
                # return an iterator over all reporters
                reports=dexy.reporter.Reporter

            for report in reports:
                report.remove_reports_dir(keep_empty_dir)

    # Logging
    def log_path(self):
        """
        Returns path to logfile.
        """
        return os.path.join(self.log_dir, self.log_file)

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
        self.log.info("starting logging for dexy")

    # Project files
    def exclude_dirs(self):
        """
        Returns list of directory names which should be excluded from dexy processing.
        """
        exclude_str = self.exclude
        if self.exclude_also:
            exclude_str += ",%s" % self.exclude_also

        exclude = [d.strip() for d in exclude_str.split(",")]
        exclude += self.reports_dirs()

        for d in self.iter_dexy_dirs():
            exclude += [d[0], "%s-old" % d[0]]

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
                if x in dirnames and not x in self.include:
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

    def explicit_config_files(self):
        return [c.strip() for c in self.configs.split()]

    def is_explicit_config(self, filepath):
        return filepath in self.explicit_config_files()

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
                if fileinfo['dir'] == '.' or self.recurse or self.is_explicit_config(filepath):
                    if os.path.split(filepath)[1] == alias:
                        self.log.info("using config file '%s'" % filepath)
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

    def report(self):
        if self.reports:
            self.log.debug("generating user-specified reports '%s'" % self.reports)
            reporters = []
            for alias in self.reports.split():
                reporter = dexy.reporter.Reporter.create_instance(alias)
                reporters.append(reporter)
        else:
            msg = "no reports specified, running default reports"
            self.log.debug(msg)
            reporters = [i for i in dexy.reporter.Reporter if i.setting('default')]

        for reporter in reporters:
            if self.state in reporter.setting('run-for-wrapper-states'):
                self.log.debug("running reporter %s" % reporter.aliases[0])
                reporter.run(self)

    def is_location_in_project_dir(self, filepath):
        return os.path.abspath(self.project_root) in os.path.abspath(filepath)

from dexy.exceptions import DeprecatedException
from dexy.exceptions import InternalDexyProblem
from dexy.exceptions import UserFeedback
from dexy.utils import file_exists
from dexy.utils import s
import chardet
import dexy.batch
import dexy.doc
import dexy.parser
import dexy.reporter
import dexy.utils
import logging
import logging.handlers
import os
import pickle
import posixpath
import shutil
import sys
import textwrap
import time
import traceback
import uuid

class Wrapper(object):
    """
    Class that manages run configuration and state and provides utilities such
    as logging and setting up/tearing down workspace on file system.
    """
    _required_dirs = ['artifacts_dir']

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

    def printmsg(self, msg):
        if self.silent:
            self.log.warn(msg)
        else:
            print(msg)

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
        elif state == 'error':
            pass
        else:
            raise dexy.exceptions.InternalDexyProblem(state)

    def __init__(self, **kwargs):
        self.initialize_attribute_defaults()
        self.update_attributes_from_kwargs(kwargs)
        self.project_root = os.path.abspath(os.getcwd())
        self.project_root_ts = "%s%s" % (self.project_root, os.sep)
        self.state = None
        self.current_task = None
        self.lookup_nodes = {} # map of shortcuts/keys to all nodes which can match
        self.lookup_sections = {} # map of section names to nodes
        self.transition('new')

    def state_message(self):
        """
        A message to print at end of dexy run depending on the final wrapper state.
        """
        if self.state == 'error':
            return " WITH ERRORS"
        else:
            return ""

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

    def trash(self, d):
        """
        Move the passed file path (if it exists) into the .trash directory.
        """
        if not self.is_location_in_project_dir(d):
            msg = "trying to trash '%s', but this is not in project dir '%s"
            msgargs = (d, self.project_root)
            raise dexy.exceptions.InternalDexyProblem(msg % msgargs)

        trash_dir = self.trash_dir()

        try:
            os.mkdir(trash_dir)
        except OSError:
            pass

        move_to = os.path.join(trash_dir, str(uuid.uuid4()))

        try:
            shutil.move(d, move_to)
        except IOError:
            pass

    def empty_trash(self):
        for dirpath, dirnames, filenames in os.walk(self.trash_dir(), topdown=False):
            for f in filenames:
                filepath = os.path.join(dirpath, f)
                os.remove(filepath)

            try:
                os.rmdir(dirpath)
            except OSError as e:
                print("error removing dir")
                print(e)
                print(dirpath)
                print((os.listdir(dirpath)))
                print((os.stat(dirpath)))
                print((os.lstat(dirpath)))
                shutil.rmtree(dirpath)

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
        else:
            matches = self.roots

        try:
            for node in matches:
                for task in node:
                    task()

        except Exception as e:
            self.error = e
            self.transition('error')
            if self.debug:
                raise
            else:
                if self.current_task:
                    msg = "ERROR while running %s: %s\n" % (self.current_task.key, str(e))
                else:
                    msg = "ERROR: %s\n" % str(e)
                sys.stderr.write(msg)
                sys.stderr.write(traceback.format_exc())
                self.log.warn(msg)

        else:
            self.after_successful_run()

    def after_successful_run(self):
        self.transition('ran')
        self.batch.end_time = time.time()
        self.batch.save_to_file()
        shutil.move(self.this_cache_dir(), self.last_cache_dir())
        self.empty_trash()
        self.add_lookups()

    def add_lookups(self):
        for data in self.batch:
            data.add_to_lookup_sections()
            data.add_to_lookup_nodes()

    def bundle_docs(self):
        from dexy.node import BundleNode
        return [n for n in self.nodes.values() if isinstance(n, BundleNode)]

    def non_bundle_docs(self):
        from dexy.node import BundleNode
        return [n for n in self.nodes.values() if not isinstance(n, BundleNode)]

    def documents(self):
        from dexy.doc import Doc
        return [n for n in self.nodes.values() if isinstance(n, Doc)]

    def roots_matching_target(self):
        # First priority is to match any named bundles.
        matches = [n for n in self.bundle_docs() if n.key == self.target]
        if not matches:
            # Second priority is exact matches of any document key.
            matches = [n for n in self.non_bundle_docs() if n.key == self.target]
        if not matches:
            # Third priority is partial matches of any document key.
            matches = [n for n in self.nodes.values() if n.key.startswith(self.target)]

        if not matches:
            raise dexy.exceptions.UserFeedback("No matches found for '%s'" % self.target)

        self.log.debug("Documents matching target '%s' are: %s" % (self.target, ", ".join(m.key_with_class() for m in matches)))
        return matches

    def run_from_new(self):
        self.to_valid()
        self.to_walked()
        self.to_checked()
        if self.dry_run:
            self.printmsg("dry run only")
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
        for name, value in dexy.utils.defaults.items():
            setattr(self, name, value)

    def update_attributes_from_kwargs(self, kwargs):
        """
        Updates instance values from a dictionary of kwargs, checking that the
        attribute names are also present in defaults dict.
        """
        for key, value in kwargs.items():
            if not key in dexy.utils.defaults:
                msg = "invalid kwarg '%s' being passed to wrapper, not defined in defaults dict" 
                raise InternalDexyProblem(msg % key)
            setattr(self, key, value)

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
            pickle.dump(arg_info, f)

    def load_node_argstrings(self):
        """
        Load saved node arg strings into a hash so nodes can check if their
        args have changed.
        """
        try:
            with open(self.node_argstrings_filename(), 'rb') as f:
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
        self.detect_dot_dexy_files()
        self.update_cache_directory()

        if not self.dexy_dirs_exist():
            msg = "You need to run 'dexy setup' in this directory first."
            raise UserFeedback(msg)

        self.deprecate_logs_directory()

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

    def detect_dot_dexy_files(self):
        if os.path.exists(".dexy") and os.path.isfile(".dexy"):
            msg = """\
            You have a file named '.dexy' in your project, this format is no longer supported.
            See http://dexy.it/guide/getting-started.html for updated tutorials.
            Please rename or remove this file to proceed."""
            raise dexy.exceptions.UserFeedback(textwrap.dedent(msg))

    def update_cache_directory(self):
        """
        Move .cache directories to be .dexy directories.
        """
        old_cache_dir = ".cache"
        safety_file = os.path.join(old_cache_dir, self.safety_filename)

        if self.artifacts_dir == old_cache_dir:
            msg = """\
            You may have a dexy.conf file present in which you specify
            'artifactsdir: .cache'
            
            Dexy's defaults have changed and the .cache directory is being
            renamed to .dexy

            The easiest way to never see this message again is to remove this
            line from your dexy.conf file (You should remove any entries in
            dexy.conf which you don't specifically want to customize.)
            
            If you really want the artifacts directory to be at .cache then you
            can leave your config in place and this message will disappear in a
            future dexy version.
            """
            print((textwrap.dedent(msg)))

        elif os.path.exists(old_cache_dir) and os.path.isdir(old_cache_dir) and os.path.exists(safety_file):
            if os.path.exists(self.artifacts_dir):
                if os.path.isdir(self.artifacts_dir):
                    msg = "You have a dexy '%s' directory and a '%s' directory. Please remove '%s' or at least '%s'."
                    msgargs = (old_cache_dir, self.artifacts_dir, old_cache_dir, safety_file)
                    raise dexy.exceptions.UserFeedback(msg % msgargs)
                else:
                    msg = "'%s' is not a dir!" % (self.artifacts_dir,)
                    raise dexy.exceptions.InternalDexyProblem(msg)

            print(("Moving directory '%s' to new location '%s'" % (old_cache_dir, self.artifacts_dir)))
            shutil.move(old_cache_dir, self.artifacts_dir)

    def deprecate_logs_directory(self):
        log_dir = 'logs'
        if self.log_dir != self.artifacts_dir:
            # user has set a custom log dir
            log_dir = self.log_dir

        safety_file = os.path.join(log_dir, self.safety_filename)
        deprecation_notice_file = os.path.join(log_dir, "WHERE-ARE-THE-LOGS.txt")

        if os.path.exists(log_dir) and os.path.exists(safety_file) and not os.path.exists(deprecation_notice_file):
            deprecation_notice = """\
            Dexy no longer has a separate '{log_dir}' directory for the log file.
            The logfile can now be found at: {log_path}\n""".format(
                    log_path = self.log_path(),
                    log_dir = log_dir)
            
            deprecation_notice = "\n".join(l.strip() for l in deprecation_notice.splitlines())
            self.printmsg("Deprecating %s/ directory" % log_dir)
            self.printmsg(deprecation_notice)
            self.printmsg("You can remove the %s/ directory" % log_dir)

            with open(deprecation_notice_file, 'w') as f:
                f.write(deprecation_notice + "\n\nYou can remove this directory.\n")
            self.trash(os.path.join(log_dir, "dexy.log"))

    def remove_dexy_dirs(self):
        for dirpath, safety_filepath, dirstat in self.iter_dexy_dirs():
            if dirstat:
                self.trash(dirpath)
        self.empty_trash()

    def remove_reports_dirs(self, reports=True, keep_empty_dir=False):
        if reports:
            if isinstance(reports, bool):
                # return an iterator over all reporters
                reports=dexy.reporter.Reporter

            for report in reports:
                report.remove_reports_dir(self, keep_empty_dir)

    # Logging
    def log_path(self):
        """
        Returns path to logfile.
        """
        return os.path.join(self.artifacts_dir, self.log_file)

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
        self.log_handler = handler

    def flush_logs(self):
        self.log_handler.flush()

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

        for dirpath, dirnames, filenames in os.walk('.', followlinks=True):
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

    def add_data_to_lookup_nodes(self, key, data):
        if not key in self.lookup_nodes:
            self.lookup_nodes[key] = []
        if not data in self.lookup_nodes[key]:
            self.lookup_nodes[key].append(data)

    def add_data_to_lookup_sections(self, key, data):
        if not key in self.lookup_sections:
            self.lookup_sections[key] = []
        if not data in self.lookup_sections[key]:
            self.lookup_sections[key].append(data)

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
        ast = dexy.parser.AbstractSyntaxTree(self)

        processed_configs = []

        for alias in self.parsers.split():
            parser = dexy.parser.Parser.create_instance(alias, self, ast)

            for filepath, fileinfo in self.filemap.items():
                if fileinfo['dir'] == '.' or self.recurse or self.is_explicit_config(filepath):
                    if os.path.split(filepath)[1] == alias:
                        self.log.info("using config file '%s'" % filepath)

                        config_file = fileinfo['ospath']
                        dirname = fileinfo['dir']

                        with open(config_file, "r") as f:
                            config_text = f.read()

                        try:
                            processed_configs.append(filepath)
                            parser.parse(dirname, config_text)
                        except UserFeedback:
                            sys.stderr.write("Problem occurred while parsing %s\n" % config_file)
                            raise

        if len(processed_configs) == 0:
            msg = "didn't find any document config files (like %s)"
            self.printmsg(msg % self.parsers)

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
        return self.writeanywhere or (self.project_root_ts in os.path.abspath(filepath))

    def decode_encoded(self, text):
        if self.encoding == 'chardet':
            encoding = chardet.detect(text)['encoding']
            if not encoding:
                return text.decode("utf-8")
            else:
                return text.decode(encoding)
        else:
            return text.decode(self.encoding)


from dexy.plugin import PluginMeta
import copy
import dexy.doc
import dexy.exceptions
import os
import posixpath
import pprint

class AbstractSyntaxTree():
    def __init__(self, wrapper=None):
        self.lookup_table = {}
        self.tree = []
        self.root_nodes_ordered = False
        self.wrapper = wrapper
        self.default_args = []

    def default_args_for_directory(self, path):
        default_kwargs = {}
        dir_path = posixpath.dirname(posixpath.abspath(path))

        for d, args in self.default_args:
            if posixpath.abspath(d) in dir_path:
                self.wrapper.log.debug("applying default args for dir %s of %s" % (d, args))
                default_kwargs.update(args)
                self.wrapper.log.debug("after updating: %s" % default_kwargs)

        return default_kwargs

    def standardize_key(self, key):
        return Parser.standardize_key(key)

    def add_task_info(self, task_key, **kwargs):
        """
        Adds kw args to kwarg dict in lookup table dict for this task
        """
        task_key = self.standardize_key(task_key)
        self.wrapper.log.debug("adding task info for '%s'" % task_key)

        if not task_key in self.tree:
            self.tree.append(task_key)

        if self.lookup_table.has_key(task_key):
            self.lookup_table[task_key].update(kwargs)
        else:
            self.lookup_table[task_key] = kwargs
            if not kwargs.has_key('children'):
                self.lookup_table[task_key]['children'] = []

        self.clean_tree()

    def add_dependency(self, task_key, child_task_key):
        """
        Adds child to list of children in lookup table dict for this task.
        """
        task_key = self.standardize_key(task_key)
        child_task_key = self.standardize_key(child_task_key)
        self.wrapper.log.debug("adding dependency of '%s' on '%s'" % (child_task_key, task_key))

        if task_key == child_task_key:
            return

        if not task_key in self.tree:
            self.tree.append(task_key)

        if self.lookup_table.has_key(task_key):
            self.lookup_table[task_key]['children'].append(child_task_key)
        else:
            self.lookup_table[task_key] = { 'children' : [child_task_key] }

        if not self.lookup_table.has_key(child_task_key):
            self.lookup_table[child_task_key] = { 'children' : [] }

        self.clean_tree()

    def clean_tree(self):
        """
        Removes tasks which are already represented as children.
        """
        all_children = self.all_children()

        # make copy since can't iterate and remove from same tree
        treecopy = copy.deepcopy(self.tree)

        for task in treecopy:
            if task in all_children:
                self.tree.remove(task)

    def all_children(self):
        """
        Returns a set of all task keys identified as children of some other element.
        """
        all_children = set()
        for kwargs in self.lookup_table.values():
            all_children.update(kwargs['children'])
        return all_children

    def task_kwargs(self, task_key):
        """
        Returns the dict of kw args for a task
        """
        args = self.lookup_table[task_key].copy()
        del args['children']
        return args

    def task_children(self, parent_key):
        """
        Returns the list of children for a atsk
        """
        return self.lookup_table[parent_key]['children']

    def debug(self, log=None):
        text = []
        text.append('tree:')
        for item in self.tree:
            text.append("  %s" % item)
        if self.root_nodes_ordered:
            text.append("root notes ordered.")
        text.append('lookup table:')
        for k, v in self.lookup_table.iteritems():
            pformat_v = pprint.pformat(v).splitlines()
            if len(pformat_v) == 0:
                raise Exception("no lines in pformat_v!")
            elif len(pformat_v) == 1:
                text.append("    %s: %s" % (k, pformat_v[0]))
            else:
                text.append("    %s:" % k)
                for line in pformat_v:
                    text.append("      %s" % line)

        if log:
            log.debug("\n".join(text))
        else:
            for line in text:
                print line

    def walk(self):
        created_tasks = {}
        root_nodes = []

        def create_dexy_task(key, *child_tasks, **kwargs):
            if not key in created_tasks:
                msg = "creating task '%s' with children '%s' with original kwargs '%s'"
                self.wrapper.log.debug(msg % (key, child_tasks, kwargs))
                alias, pattern = Parser.qualify_key(key)
                
                kwargs_with_defaults = self.default_args_for_directory(pattern)
                kwargs_with_defaults.update(kwargs)

                task = dexy.task.Task.create(alias, pattern, *child_tasks, **kwargs_with_defaults)
                task.args_before_defaults = kwargs
                created_tasks[key] = task
            return created_tasks[key]

        def parse_item(key):
            children = self.task_children(key)
            kwargs = self.task_kwargs(key)
            kwargs['wrapper'] = self.wrapper
            if kwargs.get('inactive'):
                return

            child_tasks = [parse_item(child) for child in children if child]

            # filter out inactive children
            child_tasks = [child for child in child_tasks if child]

            return create_dexy_task(key, *child_tasks, **kwargs)

        for key in self.tree:
            task = parse_item(key)
            root_nodes.append(task)

        return root_nodes, created_tasks

class Parser:
    """
    Parse various types of config file.
    """
    ALIASES = []

    __metaclass__ = PluginMeta

    @classmethod
    def is_active(klass):
        return True

    @classmethod
    def qualify_key(klass, key):
        """
        Returns key split into pattern and alias, figuring out alias if not explict.
        """
        if not key:
            raise dexy.exceptions.InternalDexyProblem("Trying to call qualify_key with key of '%s'!" % key)

        if ":" in key:
            # split qualified key into alias & pattern
            alias, pattern = key.split(":")
        else:
            # this is an unqualified key, figure out its alias
            pattern = key

            # Allow '.ext' instead of '*.ext', shorter + easier for YAML
            if pattern.startswith(".") and not pattern.startswith("./"):
                if not os.path.exists(pattern):
                    pattern = "*%s" % pattern

            filepath = pattern.split("|")[0]
            if os.path.exists(filepath) and not os.path.isdir(filepath):
                alias = 'doc'
            elif (not "." in pattern) and (not "|" in pattern):
                alias = 'bundle'
            elif "*" in pattern:
                alias = 'pattern'
            else:
                alias = 'doc'

        alias = klass.standardize_alias(alias)
        return alias, pattern

    @classmethod
    def standardize_alias(klass, alias):
        return dexy.task.Task.aliases[alias].ALIASES[0]

    @classmethod
    def standardize_key(klass, key):
        """
        Only standardized keys should be used in the AST, so we don't create 2
        entries for what turns out to be the same task.
        """
        alias, pattern = klass.qualify_key(key)
        return "%s:%s" % (alias, pattern)

    def __init__(self, wrapper=None, ast=None):
        self.wrapper = wrapper
        self.ast = ast

    def parse(self, input_text, directory="."):
        """
        Method for testing, after this can call batch.run()
        """
        self.ast = AbstractSyntaxTree()
        self.ast.wrapper = self.wrapper
        self.build_ast(directory, input_text)

        self.wrapper.batch = dexy.batch.Batch(self.wrapper)
        self.wrapper.batch.load_ast(self.ast)

    def build_ast(self, directory, input_text):
        raise Exception("Implement in subclass.")

    def join_dir(self, directory, key):
        if directory == ".":
            return key
        else:
            starts_with_dot = key.startswith(".") and not key.startswith("./")
            does_not_exist = not os.path.exists(os.path.join(directory, key))
            if starts_with_dot and does_not_exist:
                key = "*%s" % key
            return posixpath.join(directory, key)

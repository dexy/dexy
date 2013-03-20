from dexy.utils import md5_hash
from dexy.utils import os_to_posix
import dexy.doc
import dexy.plugin
import fnmatch
import re
import os
import json
import inflection

class Node(dexy.plugin.Plugin):
    """
    base class for Nodes
    """
    aliases = []
    __metaclass__ = dexy.plugin.PluginMeta
    _settings = {}

    def __init__(self, pattern, wrapper, inputs=None, **kwargs):
        self.key = os_to_posix(pattern)
        self.wrapper = wrapper
        self.args = kwargs
        self.runtime_args = {}
        self.children = []
        self.state = 'new'

        if inputs:
            self.inputs = inputs
        else:
            self.inputs = []

        self.hashid = md5_hash(self.key)

        self.args_changed = self.check_args_changed()
        self.doc_changed = False

        # Class-specific setup.
        self.setup()

    def __repr__(self):
        return "%s(%s)" % ( self.__class__.__name__, self.key)

    def add_runtime_args(self, args):
        self.args.update(args)
        self.runtime_args.update(args)

    def arg_value(self, key, default=None):
        return self.args.get(key, default) or self.args.get(key.replace("-", "_"), default)

    def setup(self):
        pass

    def websafe_key(self):
        return self.key

    def title(self):
        return self.args.get('title', inflection.titleize(self.name))

    def walk_inputs(self):
        """
        Yield all direct inputs and their inputs.
        """
        def walk(inputs):
            for i in inputs:
                walk(i)
                for ii in i.inputs:
                    yield ii
                for c in i.children:
                    yield c
                yield i

        return walk(self.inputs)

    def walk_input_docs(self):
        """
        Yield all direct inputs and their inputs, if they are of class 'doc'
        """
        for node in self.walk_inputs():
            if node.__class__.__name__ == 'Doc':
                yield node

    def log_debug(self, message):
        self.wrapper.log.debug("%s: %s" % (self.key_with_class(), message))

    def log_info(self, message):
        self.wrapper.log.info("%s: %s" % (self.key_with_class(), message))

    def log_warn(self, message):
        self.wrapper.log.warn("%s: %s" % (self.key_with_class(), message))

    def key_with_class(self):
        return "%s:%s" % (self.__class__.aliases[0], self.key)

    def check_args_changed(self):
        """
        Checks if args have changed by comparing calculated hash against the
        archived calculated hash from last run.
        """
        saved_args = None
        try:
            with open(self.args_filename(), "r") as f:
                saved_args = f.read()
            return saved_args != self.sorted_arg_string()
        except IOError:
            return True

    def sorted_args(self, skip=['contents']):
        """
        Returns a list of args in sorted order.
        """
        if not skip:
            skip = []

        sorted_args = []
        for k in sorted(self.args):
            if not k in skip:
                sorted_args.append((k, self.args[k]))
        return sorted_args

    def sorted_arg_string(self):
        """
        Returns a string representation of args in consistent, sorted order.
        """
        return json.dumps(self.sorted_args())

    def args_filename(self):
        """
        Returns filename used to store arg hash to compare in next run.
        """
        return os.path.join(self.wrapper.artifacts_dir, "%s.args" % self.hashid)

    def runtime_args_filename(self):
        """
        Returns filename used to store runtime args.
        """
        return os.path.join(self.wrapper.artifacts_dir, "%s.runtimeargs" % self.hashid)

    def save_args(self):
        """
        Saves the args (for debugging, and to compare against next run).
        """
        with open(self.args_filename(), "w") as f:
            json.dump(self.sorted_args(), f)
    
    def save_runtime_args(self):
        with open(self.runtime_args_filename(), "w") as f:
            json.dump(self.runtime_args, f)

    def load_runtime_args(self):
        with open(self.runtime_args_filename(), "r") as f:
            runtime_args = json.load(f)
            self.add_runtime_args(runtime_args)

    def inputs_changed(self):
        return any(i.changed() for i in self.inputs)

    def changed(self):
        return self.doc_changed or self.args_changed or self.inputs_changed()

    def __iter__(self):
        def next_task():
            if self.state == 'new':
                self.state = 'running'
                yield self
                self.state = 'complete'

            elif self.state == 'running':
                raise dexy.exceptions.CircularDependency(self.key)

            elif self.state == 'complete':
                pass

            else:
                raise dexy.exceptions.UnexpectedState("%s in %s" % (self.state, self.key))

        return next_task()

    def __call__(self, *args, **kw):
        for inpt in self.inputs:
            for node in inpt:
                node(*args, **kw)
        self.call_run(*args, **kw)

    def call_run(self, *args, **kw):
        self.save_args()
        if self.changed():
            self.run(*args, **kw)
            self.save_runtime_args()
        else:
            self.load_runtime_args()

    def run(self, *args, **kw):
        for child in self.children:
            child.run()

class BundleNode(Node):
    """
    Node representing a bundle of other nodes.
    """
    aliases = ['bundle']

class ScriptNode(BundleNode):
    """
    Node representing a bundle of other nodes which must always run in a set
    order, so if any of the bundle siblings change, the whole bundle should be
    re-run.
    """
    aliases = ['script']

    def setup(self):
        self.script_storage = {}

        # iterate over inputs and make sure each has all other docs as inputs?

class PatternNode(Node):
    """
    A node which takes a file matching pattern and creates individual Doc
    objects for all files that match the pattern.
    """
    aliases = ['pattern']

    def setup(self):
        file_pattern = self.key.split("|")[0]
        filter_aliases = self.key.split("|")[1:]

        for filepath, fileinfo in self.wrapper.filemap.iteritems():
            if fnmatch.fnmatch(filepath, file_pattern):
                except_p = self.args.get('except')
                if except_p and re.search(except_p, filepath):
                    self.log_debug("skipping file '%s' because it matches except '%s'" % (filepath, except_p))
                else:
                    if len(filter_aliases) > 0:
                        doc_key = "%s|%s" % (filepath, "|".join(filter_aliases))
                    else:
                        doc_key = filepath

                    self.log_debug("creating child of patterndoc %s: %s" % (self.key, doc_key))
                    doc = dexy.doc.Doc(doc_key, self.wrapper, [], **self.args)
                    doc.parent = self
                    self.children.append(doc)
                    self.wrapper.add_node(doc)

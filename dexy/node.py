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
        self.additional_docs = []

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

    # TODO get additional doc info + reconstitute...

    def arg_value(self, key, default=None):
        return self.args.get(key, default) or self.args.get(key.replace("-", "_"), default)

    def setup(self):
        pass

    def websafe_key(self):
        return self.key

    def title(self):
        title_from_name = inflection.titleize(self.output_data().baserootname())
        return self.args.get('title', title_from_name)

    def walk_inputs(self):
        """
        Yield all direct inputs and their inputs.
        """
        children = []
        def walk(inputs):
            for inpt in inputs:
                children.extend(inpt.children)
                children.append(inpt)
                walk(inpt.inputs)

        if self.inputs:
            walk(self.inputs)
        elif hasattr(self, 'parent'):
            children = self.parent.walk_inputs()

        return children

    def walk_input_docs(self):
        """
        Yield all direct inputs and their inputs, if they are of class 'doc'
        """
        for node in list(self.walk_inputs()):
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
        runtime_args_cached = os.path.exists(self.runtime_args_filename())
        try:
            with open(self.args_filename(), "r") as f:
                saved_args = f.read()
            return not runtime_args_cached or (saved_args != self.sorted_arg_string())
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
        return os.path.join(self.wrapper.artifacts_dir, self.hashid[0:2], "%s.args" % self.hashid)

    def runtime_args_filename(self):
        """
        Returns filename used to store runtime args.
        """
        return os.path.join(self.wrapper.artifacts_dir, self.hashid[0:2], "%s.runtimeargs" % self.hashid)

    def additional_docs_filename(self):
        return os.path.join(self.wrapper.artifacts_dir, self.hashid[0:2], "%s.additionaldocs" % self.hashid)

    def save_args(self):
        """
        Saves the args (for debugging, and to compare against next run).
        """
        # TODO make all two letter a0 a1 a2 dirs automatically, remove this
        try:
            os.makedirs(os.path.dirname(self.args_filename()))
        except OSError:
            pass
        with open(self.args_filename(), "w") as f:
            json.dump(self.sorted_args(), f)
    
    def save_runtime_args(self):
        with open(self.runtime_args_filename(), "w") as f:
            json.dump(self.runtime_args, f)

    def load_runtime_args(self):
        with open(self.runtime_args_filename(), "r") as f:
            runtime_args = json.load(f)
            self.add_runtime_args(runtime_args)

    def save_additional_docs(self):
        additional_doc_info = []
        for doc in self.additional_docs:
            info = (doc.key, doc.hashid)
            additional_doc_info.append(info)

        with open(self.additional_docs_filename(), "w") as f:
            json.dump(additional_doc_info, f)

    def load_additional_docs(self):
        with open(self.additional_docs_filename(), "r") as f:
            additional_doc_info = json.load(f)

        for doc_key, hashid in additional_doc_info:
            new_doc = dexy.doc.Doc(doc_key, self.wrapper, [], contents='dummy contents')
            new_doc.contents = None
            assert new_doc.hashid == hashid
            new_doc.initial_data.load_data()
            new_doc.output_data().load_data()
            self.add_additional_doc(new_doc)

    def add_additional_doc(self, doc):
        self.log_debug("adding additional doc '%s'" % doc.key)
        self.children.append(doc)
        self.wrapper.add_node(doc)
        self.additional_docs.append(doc)

    def inputs_changed(self):
        return any(i.changed() for i in self.inputs)

    def changed(self):
        #print "checking if %s is changed" % self.key
        #print "  doc changed %s" % self.doc_changed
        #print "  args changed %s" % self.args_changed
        #print "  inputs changed %s" % self.inputs_changed()
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
        for inpt in self.walk_inputs():
            for node in inpt:
                node(*args, **kw)

        import time
        self.run_start_time = time.time()
        self.call_run(*args, **kw)
        self.run_finish_time = time.time()

        self.append_to_batch()

    def append_to_batch(self):
        pass

    def call_run(self, *args, **kw):
        self.save_args()
        if self.changed():
            self.log_info("running")
            self.run(*args, **kw)
            self.save_runtime_args()
            if self.additional_docs:
                self.save_additional_docs()
        else:
            self.log_info("node is cached, not running")
            self.load_runtime_args()
            if os.path.exists(self.additional_docs_filename()):
                self.log_debug("loading additional docs")
                self.load_additional_docs()

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

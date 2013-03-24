from dexy.utils import md5_hash
from dexy.utils import os_to_posix
import dexy.doc
import dexy.plugin
import fnmatch
import re
import os
import json

class Node(dexy.plugin.Plugin):
    """
    base class for Nodes
    """
    aliases = ['node']
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
        self.doc_changed = None
        self.is_cached = None
        self.was_run = None

        # Class-specific setup.
        self.setup()

        assert_msg = "custom setup method for %s must set doc_changed"
        assert self.doc_changed is not None, assert_msg % self.key_with_class()

    def setup(self):
        self.doc_changed = self.check_doc_changed()
   
    def check_doc_changed(self):
        return False

    def __repr__(self):
        return "%s(%s)" % ( self.__class__.__name__, self.key)

    def add_runtime_args(self, args):
        self.args.update(args)
        self.runtime_args.update(args)

    def arg_value(self, key, default=None):
        return self.args.get(key, default) or self.args.get(key.replace("-", "_"), default)

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
        saved_args = self.wrapper.saved_args.get(self.key_with_class())
        if not saved_args:
            self.log_debug("no saved args")
            return True
        else:
            self.log_debug("saved args '%s' (%s)" % (saved_args, saved_args.__class__))
            self.log_debug("sorted args '%s' (%s)" % (self.sorted_arg_string(), self.sorted_arg_string().__class__))
            self.log_debug("unequal: %s" % (saved_args != self.sorted_arg_string()))
            return saved_args != self.sorted_arg_string()

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
        Returns a string representation of args in sorted order.
        """
        return unicode(json.dumps(self.sorted_args()))

    def runtime_args_filename(self):
        """
        filename used to store runtime args
        """
        return os.path.join(self.wrapper.artifacts_dir, self.hashid[0:2], "%s.runtimeargs.json" % self.hashid)

    def additional_docs_filename(self):
        """
        filename used to store additional doc information
        """
        return os.path.join(self.wrapper.artifacts_dir, self.hashid[0:2], "%s.additionaldocs.json" % self.hashid)

    def save_runtime_args(self):
        if self.runtime_args:
            with open(self.runtime_args_filename(), "w") as f:
                json.dump(self.runtime_args, f)

    def load_runtime_args(self):
        if os.path.exists(self.runtime_args_filename()):
            with open(self.runtime_args_filename(), "r") as f:
                runtime_args = json.load(f)
                self.add_runtime_args(runtime_args)

    def save_additional_docs(self):
        if self.additional_docs:
            additional_doc_info = []
            for doc in self.additional_docs:
                info = (doc.key, doc.hashid)
                additional_doc_info.append(info)

            with open(self.additional_docs_filename(), "w") as f:
                json.dump(additional_doc_info, f)

    def load_additional_docs(self):
        if os.path.exists(self.additional_docs_filename()):
            with open(self.additional_docs_filename(), "r") as f:
                additional_doc_info = json.load(f)
    
            for doc_key, hashid in additional_doc_info:
                new_doc = dexy.doc.Doc(doc_key, self.wrapper, [], contents='dummy contents')
                new_doc.contents = None
                new_doc.args_changed = False
                assert new_doc.hashid == hashid
                new_doc.initial_data.load_data()
                new_doc.output_data().load_data()
                self.add_additional_doc(new_doc)

    def add_additional_doc(self, doc):
        self.log_debug("adding additional doc '%s'" % doc.key)
        self.children.append(doc)
        self.wrapper.add_node(doc)
        self.additional_docs.append(doc)

    def calculate_is_cached(self):
        if self.is_cached == None:
            self.log_debug("checking if %s is changed" % self.key)
            self.log_debug("  doc changed %s" % self.doc_changed)
            self.log_debug("  args changed %s" % self.args_changed)
            self.is_cached = not self.doc_changed and not self.args_changed
            # TODO check that all storage files are present.

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
        any_inputs_ran = False
        for inpt in self.walk_inputs():
            for node in inpt:
                node(*args, **kw)
            if inpt.was_run:
                any_inputs_ran = True
            assert inpt.is_cached, "%s not cached!" % inpt.key_with_class()

        import time
        self.run_start_time = time.time()
        self.call_run(any_inputs_ran)
        self.run_finish_time = time.time()

        if hasattr(self, 'batch_info'):
            self.wrapper.batch.add_doc(self)

    def is_cached_and_present(self):
        if self.is_cached and hasattr(self, 'output_data'):
            return self.output_data().is_cached()
        else:
            return self.is_cached

    def call_run(self, any_inputs_ran):
        self.calculate_is_cached()

        if self.is_cached_and_present() and not any_inputs_ran:
            self.log_info("cached, not running")
            self.load_runtime_args()
            self.load_additional_docs()
            if self.was_run == None:
                self.was_run = False

        else:
            self.log_info("running")
            self.run()
            self.save_runtime_args()
            self.save_additional_docs()
            if self.was_run == None:
                self.was_run = True

        assert self.is_cached or self.was_run
        self.is_cached = True
        assert self.is_cached_and_present()

    def run(self):
        for child in self.children:
            child()
            if child.was_run:
                self.was_run = True

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

    def check_doc_changed(self):
        return any(i.doc_changed for i in self.inputs)

    def setup(self):
        self.script_storage = {}

        siblings = []
        for doc in self.inputs:
            doc.inputs = list(doc.inputs) + siblings
            siblings.append(doc)

        self.doc_changed = self.check_doc_changed()

        for doc in self.inputs:
            if not self.doc_changed:
                assert not doc.doc_changed
            doc.doc_changed = self.doc_changed

class PatternNode(Node):
    """
    A node which takes a file matching pattern and creates individual Doc
    objects for all files that match the pattern.
    """
    aliases = ['pattern']

    def check_doc_changed(self):
        return any(child.doc_changed for child in self.children)

    def setup(self):
        file_pattern = self.key.split("|")[0]
        filter_aliases = self.key.split("|")[1:]

        for filepath, fileinfo in self.wrapper.filemap.iteritems():
            if fnmatch.fnmatch(filepath, file_pattern):
                except_p = self.args.get('except')
                if except_p and re.search(except_p, filepath):
                    msg = "not creating child of patterndoc for file '%s' because it matches except '%s'"
                    msgargs = (filepath, except_p)
                    self.log_debug(msg % msgargs)
                else:
                    if len(filter_aliases) > 0:
                        doc_key = "%s|%s" % (filepath, "|".join(filter_aliases))
                    else:
                        doc_key = filepath

                    msg = "creating child of patterndoc %s: %s"
                    msgargs = (self.key, doc_key)
                    self.log_debug(msg % msgargs)
                    doc = dexy.doc.Doc(doc_key, self.wrapper, [], **self.args)
                    doc.parent = self
                    self.children.append(doc)
                    self.wrapper.add_node(doc)

        self.doc_changed = self.check_doc_changed()

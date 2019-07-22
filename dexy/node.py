from dexy.utils import md5_hash
from dexy.utils import os_to_posix
import dexy.doc
import dexy.plugin
import fnmatch
import json
import re

class Node(dexy.plugin.Plugin, metaclass=dexy.plugin.PluginMeta):
    """
    base class for Nodes
    """
    _settings = {}
    aliases = ['node']
    state_transitions = (
            ('new', 'cached'),
            ('cached', 'consolidated'),
            ('new', 'uncached'),
            ('uncached', 'running'),
            ('running', 'ran'),
            )

    def __init__(self, pattern, wrapper, inputs=None, **kwargs):
        self.key = os_to_posix(pattern)
        self.wrapper = wrapper
        self.args = kwargs
        if inputs:
            self.inputs = list(inputs)
        else:
            self.inputs = []

        self.initialize_settings(**kwargs)

        self.start_time = 0
        self.finish_time = 0
        self.elapsed_time = 0

        self.runtime_args = {}
        self.children = []
        self.additional_docs = []

        self.hashid = md5_hash(self.key)

        self.state = 'new'

        # Class-specific setup.
        self.setup()

    def setup(self):
        pass
   
    def check_doc_changed(self):
        return False

    def __repr__(self):
        return "%s(%s)" % ( self.__class__.__name__, self.key)

    def transition(self, new_state):
        dexy.utils.transition(self, new_state)

    def update_all_settings(self, new_args):
        pass

    def add_runtime_args(self, args):
        self.update_all_settings(args)
        self.runtime_args.update(args)
        self.wrapper.batch.update_doc_info(self)

    def arg_value(self, key, default=None):
        return self.args.get(key, default) or self.args.get(key.replace("-", "_"), default)

    def walk_inputs(self):
        """
        Yield all direct inputs and their inputs.
        """
        children = []
        def walk(inputs):
            for inpt in inputs:
                children.append(inpt)
                walk(inpt.inputs + inpt.children)

        if self.inputs:
            walk(self.inputs)
        elif hasattr(self, 'parent'):
            children = self.parent.walk_inputs()

        return children

    def walk_input_docs(self):
        """
        Yield all direct inputs and their inputs, if they are of class 'doc'
        """
        for node in self.walk_inputs():
            if node.__class__.__name__ == 'Doc':
                yield node

    def log_debug(self, message):
        self.wrapper.log.debug("(state:%s) %s %s: %s" % (self.wrapper.state, self.hashid, self.key_with_class(), message))

    def log_info(self, message):
        self.wrapper.log.info("(state:%s) %s %s: %s" % (self.wrapper.state, self.hashid, self.key_with_class(), message))

    def log_warn(self, message):
        self.wrapper.log.warn("(state:%s) %s %s: %s" % (self.wrapper.state, self.hashid, self.key_with_class(), message))

    def key_with_class(self):
        return "%s:%s" % (self.__class__.aliases[0], self.key)

    def check_args_changed(self):
        """
        Checks if args have changed by comparing calculated hash against the
        archived calculated hash from last run.
        """
        saved_args = self.wrapper.saved_args.get(self.key_with_class())
        if not saved_args:
            self.log_debug("no saved args, will return True for args_changed")
            return True
        else:
            self.log_debug("    saved args '%s' (%s)" % (saved_args, saved_args.__class__))
            self.log_debug("    sorted args '%s' (%s)" % (self.sorted_arg_string(), self.sorted_arg_string().__class__))
            self.log_debug("  args unequal: %s" % (saved_args != self.sorted_arg_string()))
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
        return str(json.dumps(self.sorted_args()))

    def additional_doc_info(self):
        additional_doc_info = []
        for doc in self.additional_docs:
            info = (doc.key, doc.hashid, doc.setting_values())
            additional_doc_info.append(info)
        return additional_doc_info

    def load_additional_docs(self, additional_doc_info):
        for doc_key, hashid, doc_settings in additional_doc_info:
            new_doc = dexy.doc.Doc(doc_key,
                    self.wrapper,
                    [],
                    **doc_settings
                    )
            new_doc.contents = None
            new_doc.args_changed = False
            new_doc.state = 'cached'
            assert new_doc.hashid == hashid

            new_doc.check_is_cached()
            new_doc.consolidate_cache_files()

            new_doc.initial_data.load_data()
            new_doc.output_data().load_data()
            self.add_additional_doc(new_doc)

    def add_additional_doc(self, doc):
        self.log_debug("adding additional doc '%s'" % doc.key)
        doc.created_by_doc = self
        self.children.append(doc)
        self.wrapper.add_node(doc)
        self.wrapper.batch.add_doc(doc)
        self.additional_docs.append(doc)

    def check_cache_elements_present(self):
        """
        Verify that all expected cache files are in fact present.
        """
        return True

    def input_nodes(self, with_parent_inputs = False):
        input_nodes = self.inputs + self.children
        if with_parent_inputs and hasattr(self, 'parent'):
            if not self in self.parent.inputs:
                input_nodes.extend(self.parent.inputs)
        return input_nodes

    def check_is_cached(self):
        if self.state == 'new':
            self.log_debug("checking if %s is changed" % self.key)

            any_inputs_not_cached = False
            for node in self.input_nodes(True):
                node.check_is_cached()
                if not node.state == 'cached':
                    self.log_debug("    input node %s is not cached" % node.key_with_class())
                    any_inputs_not_cached = True

            self.args_changed = self.check_args_changed()
            self.doc_changed = self.check_doc_changed()
            cache_elements_present = self.check_cache_elements_present()
                
            self.log_debug("  doc changed %s" % self.doc_changed)
            self.log_debug("  args changed %s" % self.args_changed)
            self.log_debug("  any inputs not cached %s" % any_inputs_not_cached)
            # log the 'not' so we can search for 'True' in logs to find uncached items
            self.log_debug("  cache elements missing %s" % (not cache_elements_present))

            is_cached = not self.doc_changed and not self.args_changed and not any_inputs_not_cached

            if is_cached and cache_elements_present:
                self.transition('cached')
            else:
                self.transition('uncached')

            # do housekeeping stuff we need to do for every node
            self.wrapper.add_node(self)
            self.wrapper.batch.add_doc(self)

    def load_runtime_info(self):
        pass

    def consolidate_cache_files(self):
        for node in self.input_nodes():
            node.consolidate_cache_files()

        if self.state == 'cached':
            self.transition('consolidated')

    def __lt__(self, other):
        return self.key < other.key

    def __iter__(self):
        def next_task():
            if self.state == 'uncached':
                self.transition('running')
                self.log_info("running...")
                yield self
                self.transition('ran')

            elif self.state in ('consolidated',):
                self.log_info("using cache for self and any children")

            elif self.state in ('ran',):
                self.log_info("already ran in this batch")

            elif self.state == 'running':
                raise dexy.exceptions.CircularDependency(self.key)

            else:
                raise dexy.exceptions.UnexpectedState("%s in %s" % (self.state, self.key))

        return next_task()

    def __call__(self, *args, **kw):
        for inpt in self.inputs:
            for task in inpt:
                task()
        self.wrapper.current_task = self
        self.run()
        self.wrapper.current_task = None

    def run(self):
        """
        Method which processes node's content if not cached, also responsible
        for calling child nodes.
        """
        for child in self.children:
            for task in child:
                task()

class BundleNode(Node):
    """
    Acts as a wrapper for other nodes.
    """
    aliases = ['bundle']

class ScriptNode(BundleNode):
    """
    Represents a bundle of nodes which need to run in order.

    If any of the bundle siblings change, the whole bundle should be re-run.
    """
    aliases = ['script']

    def check_doc_changed(self):
        return any(i.doc_changed for i in self.inputs)

    def setup(self):
        self.script_storage = {}

        siblings = []
        for doc in self.inputs:
            doc.parent = self
            doc.inputs = doc.inputs + siblings
            siblings.append(doc)

#        self.doc_changed = self.check_doc_changed()
#
#        for doc in self.inputs:
#            if not self.doc_changed:
#                assert not doc.doc_changed
#            doc.doc_changed = self.doc_changed

class PatternNode(Node):
    """
    Represents a file matching pattern.

    Creates child Doc objects for each file which matches the pattern.
    """
    aliases = ['pattern']

    def check_doc_changed(self):
        return any(child.doc_changed for child in self.children)

    def setup(self):
        file_pattern = self.key.split("|")[0]
        filter_aliases = self.key.split("|")[1:]

        for filepath, fileinfo in self.wrapper.filemap.items():
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
                    self.wrapper.batch.add_doc(doc)

import dexy.doc
import dexy.task
import fnmatch
import re

class Node(dexy.task.Task):
    """
    base class for Nodes
    """
    ALIASES = ['node']

    def __init__(self, key, **kwargs):
        super(Node, self).__init__(key, **kwargs)
        self.inputs = list(kwargs.get('inputs', []))

    def calculate_hashstring(self):
        return self.metadata.compute_hash()

    def walk_inputs(self):
        """
        Returns a generator which recursively yields all inputs and their inputs.
        """
        def walk(node, level=0):
            for inpt in node.inputs:
                for t in walk(inpt,level+1):
                    yield t
            if level > 0:
                yield node

        return walk(self)        

    def walk_input_docs(self):
        for node in self.walk_inputs():
            for child in node.children:
                yield child

    def call_after_setup(self):
        print "in call_after_setup for %s" % self.key_with_class()
        self.after_setup()
        for inpt in self.inputs:
            inpt.call_after_setup()

    def after_setup(self):
        print "in after_setup for %s, doing nothing" % self.key_with_class()
        pass

class DocNode(Node):
    """
    Node representing a single doc.
    """
    ALIASES = ['doc']

    def populate(self):
        doc = dexy.doc.Doc(self.key, **self.args)
        if not hasattr(doc, 'wrapper') or not doc.wrapper:
            doc.wrapper = self.wrapper
        doc.node = self
        self.children.append(doc)
        doc.populate()
        doc.transition('populated')

    def after_setup(self):
        self.set_hashstring()

        # Now update child hashstrings for inputs.
        for doc in self.children:
            for i, artifact in enumerate(doc.children):
                if i == 0:
                    artifact.set_hashstring()
                    artifact.setup_output_data()
                else:
                    artifact.metadata.hash_info['inputs'][self.key_with_class()] = self.hashstring
                    artifact.set_hashstring()
                    artifact.input_data = artifact.prior.output_data
                    artifact.setup_output_data()

        # Now update node's hashstring for children, won't affect children but
        # will affect other docs using this node as an input.
        for doc in self.children:
            self.metadata.hash_info['children'][doc.key_with_class()] = doc.final_artifact.hashstring_without_inputs
        self.set_hashstring_with_children()

class AdditionalDocNode(Node):
    """
    Node containing an additional doc created from a document.
    """
    ALIASES = ['additional']
    pass

class BundleNode(Node):
    """
    Node representing a bundle of other nodes.
    """
    ALIASES = ['bundle']

class ScriptNode(BundleNode):
    """
    Node representing a bundle of other nodes which must always run in a set
    order, so if any of the bundle siblings change, the whole bundle should be
    re-run.
    """
    ALIASES = ['script']

    def setup(self):
        self.set_log()

        # Create a shared key-value store that children can access.
        self.script_storage = {}

    def after_setup(self):
        for i in self.inputs:
            i.set_hashstring()
        self.metadata.input_hashstrings = ",".join(i.hashstring for i in self.inputs)
        self.set_hashstring()

class PatternNode(Node):
    """
    A node which takes a file matching pattern and creates individual Doc
    objects for all files that match the pattern.
    """
    ALIASES = ['pattern']

    def populate(self):
        self.set_log()

        file_pattern = self.key.split("|")[0]
        filter_aliases = self.key.split("|")[1:]

        for filepath, fileinfo in self.wrapper.filemap.iteritems():
            if fnmatch.fnmatch(filepath, file_pattern):
                except_p = self.args.get('except')
                if except_p and re.search(except_p, filepath):
                    self.log.debug("skipping file '%s' because it matches except '%s'" % (filepath, except_p))
                else:
                    if len(filter_aliases) > 0:
                        doc_key = "%s|%s" % (filepath, "|".join(filter_aliases))
                    else:
                        doc_key = filepath

                    if hasattr(self.wrapper.batch, 'ast'):
                        doc_args = self.wrapper.batch.ast.default_args_for_directory(filepath)
                    else:
                        doc_args = {}

                    doc_args.update(self.args_before_defaults)
                    doc_args['wrapper'] = self.wrapper

                    self.log.debug("creating child of patterndoc %s: %s" % (self.key, doc_key))
                    self.log.debug("with args %s" % doc_args)
                    doc = dexy.doc.Doc(doc_key, **doc_args)
                    doc.node = self
                    self.children.append(doc)
                    doc.populate()
                    doc.transition('populated')

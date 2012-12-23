from dexy.doc import Doc
import dexy.task
import fnmatch
import os
import re

class Node(dexy.task.Task):
    """
    base class for Nodes
    """
    ALIASES = ['node']

    def __init__(self, key, **kwargs):
        super(Node, self).__init__(key, **kwargs)
        self.inputs = kwargs.get('inputs', {})

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
                assert child.__class__.__name__ == "Doc"
                yield child

    def setup(self):
        """
        Setup method for bsae Node class. All nodes should generate a
        hashstring based on their inputs and their children so that doc
        children only need to look at the node's hash.
        """
        self.metadata = dexy.metadata.Md5()
        self.metadata.input_hashes = ",".join([inpt.hashstring for inpt in self.inputs])
        self.metadata.child_hashes = ",".join([chld.hashstring for chld in self.children])
        self.hashstring = self.metadata.compute_hash()

class DocNode(Node):
    """
    Node representing a single doc.
    """
    ALIASES = ['doc']

    def populate(self):
        doc = Doc(self.key, **self.args)
        if not hasattr(doc, 'wrapper') or not doc.wrapper:
            doc.wrapper = self.wrapper
        doc.node = self
        self.children.append(doc)
        doc.populate()
        doc.transition('populated')

class BundleNode(Node):
    """
    Node representing a bundle of other nodes.
    """
    ALIASES = ['bundle']

    def populate(self):
        pass

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

        recurse = self.args.get('recurse', True)
        for dirpath, filename in self.wrapper.walk(".", recurse):
            raw_filepath = os.path.join(dirpath, filename)
            filepath = os.path.normpath(raw_filepath)

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

                    # TODO implement 'depends'
                    #if doc_args.has_key('depends'):
                    #    if doc_args.get('depends'):
                    #        doc_children = self.wrapper.registered_docs()
                    #    else:
                    #        doc_children = []
                    #    del doc_args['depends']

                    self.log.debug("creating child of patterndoc %s: %s" % (self.key, doc_key))
                    self.log.debug("with args %s" % doc_args)
                    doc = Doc(doc_key, **doc_args)
                    doc.node = self
                    self.children.append(doc)
                    doc.populate()
                    doc.transition('populated')


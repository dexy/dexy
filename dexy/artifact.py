from dexy.common import OrderedDict
from dexy.task import Task
import dexy.data
import dexy.doc
import dexy.exceptions
import dexy.filter
import dexy.metadata
import inspect
import json
import os
import shutil
import stat

class Artifact(Task):
    def setup(self):
        self.set_log()
        self.metadata = dexy.metadata.Md5()
        self.after_setup()

    def set_and_save_hash(self):
        self.append_children_hashstrings()
        self.set_hashstring()

    def append_children_hashstrings(self):
        child_hashes = []
        for child in self.doc.completed_children.values():
            if isinstance(child, dexy.doc.Doc):
                child_hash = child.final_artifact.hashstring
                child_hashes.append("%s: %s" % (child.key, child_hash))

        self.metadata.child_hashes = ", ".join(child_hashes)

    def set_hashstring(self):
        self.hashstring = self.metadata.compute_hash()
        self.log.debug("hashstring for %s is %s" % (self.key, self.hashstring))

    def tmp_dir(self):
        return os.path.join(self.wrapper.artifacts_dir, self.hashstring)

    def create_working_dir(self, populate=False):
        tmpdir = self.tmp_dir()
        shutil.rmtree(tmpdir, ignore_errors=True)
        os.mkdir(tmpdir)

        if populate:
            for doc in self.doc.completed_children.values():
                if isinstance(doc, dexy.doc.Doc):
                    filename = os.path.join(tmpdir, doc.output().name)
                    parent_dir = os.path.dirname(filename)
                    if not os.path.exists(parent_dir):
                        os.makedirs(parent_dir)
                    doc.output().output_to_file(filename)

            input_filepath = os.path.join(tmpdir, self.prior.output_data.name)

        parent_dir = os.path.dirname(input_filepath)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        self.input_data.output_to_file(input_filepath)
        return parent_dir

    def data_class_alias(self):
        return 'generic'

    def setup_output_data(self):
        data_class = dexy.data.Data.aliases[self.data_class_alias()]
        self.output_data_type = data_class.ALIASES[0]
        self.output_data = data_class(self.key, self.ext, self.hashstring, self.wrapper)

class InitialArtifact(Artifact):
    def append_children_hashstrings(self):
        # Children don't matter for initial artifact which just copies data
        # from file and doesn't take any other doc inputs.
        pass

    def set_metadata_attrs(self):
        self.metadata.key = self.key

        stat_info = os.stat(self.name)
        self.metadata.mtime = stat_info[stat.ST_MTIME]
        self.metadata.size = stat_info[stat.ST_SIZE]

    def set_output_data(self):
        self.output_data.copy_from_file(self.name)

    def run(self, *args, **kw):
        self.set_log()

        self.ext = os.path.splitext(self.name)[1]

        self.set_metadata_attrs()
        self.set_and_save_hash()
        self.setup_output_data()

        if not self.output_data.is_cached():
            self.set_output_data()

class InitialVirtualArtifact(InitialArtifact):
    def get_contents(self):
        contents = self.args.get('contents')
        if not contents:
            raise Exception("no contents found for %s" % self.key)
        return contents

    def data_class_alias(self):
        data_class_alias = self.args.get('data_class')

        if data_class_alias:
            return data_class_alias
        else:
            contents = self.get_contents()
            if isinstance(contents, OrderedDict):
                return 'sectioned'
            elif isinstance(contents, dict):
                return 'keyvalue'
            else:
                return 'generic'

    def set_metadata_attrs(self):
        self.metadata.key = self.key
        self.metadata.contents = self.get_contents()

    def set_output_data(self):
        self.output_data.set_data(self.get_contents())

class FilterArtifact(Artifact):
    def data_class_alias(self):
        return self.filter_class.data_class_alias()

    def run(self, *args, **kw):
        self.input_data = self.prior.output_data

        self.set_extension()
        self.set_metadata_hash()
        self.setup_output_data()

        if not self.output_data.is_cached():
            self.generate()
            self.source = 'generated'
        else:
            self.reconstitute_cached_children()
            self.source = 'cached'

    def reconstitute_cached_children(self):
        """
        Look for artifacts which were created as side effects of this filter
        running, re-run these docs (which should be present in cache).
        """
        rows = self.wrapper.get_child_hashes_in_previous_batch(self.hashstring)
        for row in rows:
            self.log.debug("Fetched row %s for parent doc %s" % (row['key'], self.key))
            if 'Initial' in row['class_name']:
                doc_args = json.loads(row['args'])
                doc = dexy.doc.Doc(row['doc_key'], **doc_args)
                self.add_doc(doc)
                assert doc.artifacts[0].hashstring == row['hashstring'], "Unexpected hashstring for %s" % doc.artifacts[0].key

    def set_metadata_hash(self):
        self.metadata.ext = self.ext
        self.metadata.key = self.key
        self.metadata.next_filter_name = self.next_filter_name
        self.metadata.prior_hash = self.prior.hashstring

        self.metadata.pre_method_source = inspect.getsource(self.pre)
        self.metadata.post_method_source = inspect.getsource(self.post)

        strargs = []
        for k in sorted(self.args):
            if not k in ['wrapper']: # excepted items don't affect outcome
                v = str(self.args[k])
                strargs.append("%s: %s" % (k, v))
        self.metadata.argstr = ", ".join(strargs)

        self.metadata.dexy_version = dexy.__version__

        # filter source code
        sources = []
        klass = self.filter_class
        while klass != dexy.filter.Filter:
            sources.append(dexy.filter.Filter.source[klass.__name__])
            klass = klass.__base__
        sources.append(dexy.filter.Filter.source[klass.__name__])
        self.metadata.filter_source = "\n".join(sources)

        if hasattr(self.filter_class, 'version'):
            version = self.filter_class.version()
            self.metadata.software_version = version

        self.set_and_save_hash()

    def add_doc(self, doc):
        self.log.debug("Adding additional doc %s" % doc.key)
        doc.created_by_doc = self.hashstring
        doc.wrapper = self.wrapper
        doc.setup()

        for task in (doc,):
            for t in task:
                t()

        self.doc.children.append(doc)

    def set_extension(self):
        this_filter_outputs = self.filter_class.OUTPUT_EXTENSIONS
        this_filter_accepts = self.filter_class.INPUT_EXTENSIONS

        # Check that we can handle input extension
        if set([self.prior.ext, ".*"]).isdisjoint(set(this_filter_accepts)):
            msg = "Filter '%s' in '%s' can't handle file extension %s, supported extensions are %s"
            params = (self.filter_alias, self.key, self.prior.ext, ", ".join(this_filter_accepts))
            raise dexy.exceptions.UserFeedback(msg % params)

        # Figure out output extension
        ext = self.filter_args().get('ext')
        if ext:
            # User has specified desired extension
            if not ext.startswith('.'):
                ext = '.%s' % ext

            # Make sure it's a valid one
            if not ext in this_filter_outputs:
                msg = "You have requested file extension %s in %s but filter %s can't generate that."
                raise dexy.exceptions.UserFeedback(msg % (ext, self.key, self.filter_alias))

            self.ext = ext

        elif ".*" in this_filter_outputs:
            self.ext = self.prior.ext

        else:
            # User has not specified desired extension, and we don't output wildcards,
            # figure out extension based on next filter in sequence, if any.
            if self.next_filter_class:
                next_filter_accepts = self.next_filter_class.INPUT_EXTENSIONS

                if ".*" in next_filter_accepts:
                    self.ext = this_filter_outputs[0]
                else:
                    if set(this_filter_outputs).isdisjoint(set(next_filter_accepts)):
                        msg = "Filter %s can't go after filter %s, no file extensions in common."
                        raise dexy.exceptions.UserFeedback(msg % (self.next_filter_alias, self.filter_alias))

                    for e in this_filter_outputs:
                        if e in next_filter_accepts:
                            self.ext = e

                    if not self.ext:
                        msg = "no file extension found but checked already for disjointed, should not be here"
                        raise dexy.exceptions.InternalDexyProblem(msg)
            else:
                self.ext = this_filter_outputs[0]

    def generate(self, *args, **kw):
        self.filter_instance = self.filter_class()
        self.filter_instance.artifact = self
        self.filter_instance.log = self.log
        if not self.input_data.has_data():
            raise Exception("no data!")
        self.filter_instance.process()

    def filter_args(self):
        """
        Arguments that are passed by the user which are specifically for the
        filter that will be run by this artifact.
        """
        return self.args.get(self.filter_alias, {})

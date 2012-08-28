from dexy.task import Task
from ordereddict import OrderedDict
import dexy.data
import dexy.exceptions
import dexy.filter
import dexy.metadata
import inspect
import os
import shutil
import stat

### @export "artifact-class"
class Artifact(Task):
    def setup(self):
        self.set_log()
        self.metadata = dexy.metadata.Sqlite3(self.run_params)

    ### @export "set-and-save-hash"
    def set_and_save_hash(self):
        self.set_hashstring()
        self.metadata.create_record()
        self.metadata.persist()

    ### @export "artifact-set-hashstring"
    def set_hashstring(self):
        self.metadata.hashstring = self.metadata.compute_hash()

    def parent_dir(self):
        return os.path.dirname(self.name)

    def long_name(self):
        return "%s%s" % (self.key.replace("|", "-"), self.ext)

    def web_safe_document_key(self):
        return self.long_name().replace("/", "--")

    def relative_refs(self, relative_to_file):
        doc_dir = os.path.dirname(relative_to_file)
        return [
                os.path.relpath(self.key, doc_dir),
                os.path.relpath(self.long_name(), doc_dir),
                "/%s" % self.key,
                "/%s" % self.long_name()
        ]

    def tmp_dir(self):
        return os.path.join(self.run_params.artifacts_dir, self.metadata.hashstring)

    def create_working_dir(self, populate=False):
        tmpdir = self.tmp_dir()
        shutil.rmtree(tmpdir, ignore_errors=True)
        os.mkdir(tmpdir)

        if populate:
            for key, doc in self.runner.completed.iteritems():
                if isinstance(doc, dexy.doc.Doc):
                    filename = os.path.join(tmpdir, doc.final_artifact.name)
                    parent_dir = os.path.dirname(filename)
                    if not os.path.exists(parent_dir):
                        os.makedirs(parent_dir)
                    doc.output().output_to_file(filename)

            input_filepath = os.path.join(tmpdir, self.prior.name)

        parent_dir = os.path.dirname(input_filepath)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        self.input_data.output_to_file(input_filepath)
        return parent_dir

class InitialVirtualArtifact(Artifact):
    def get_contents(self):
        return self.args.get('contents')

    def run(self, runner):
        contents = self.get_contents()
        if not contents:
            raise Exception("no contents found for %s" % self.key)

        self.runner = runner
        self.ext = os.path.splitext(self.name)[1]
        self.metadata.key = self.key
        self.metadata.contents = contents
        self.set_and_save_hash()

        hashstring = self.metadata.hashstring

        data_class_alias = self.args.get('data_class')
        if not data_class_alias:
            if isinstance(contents, OrderedDict):
                data_class_alias = 'sectioned'
            elif isinstance(contents, dict):
                data_class_alias = 'keyvalue'
            else:
                data_class_alias = 'generic'

        data_class = dexy.data.Data.aliases[data_class_alias]
        self.output_data = data_class(hashstring, self.ext, self.run_params)

        if self.output_data.is_cached():
            self.log.debug("Data for %s is already cached in %s" % (self.key, self.output_data.storage.data_file()))

        else:
            self.output_data.set_data(contents)

### @export "initial-artifact-class"
class InitialArtifact(Artifact):
    def run(self, runner):
        self.runner = runner
        self.ext = os.path.splitext(self.name)[1]

        ### @export "initial-artifact-set-hashstring"
        self.metadata.key = self.key

        stat_info = os.stat(self.name)
        self.metadata.mtime = stat_info[stat.ST_MTIME]
        self.metadata.size = stat_info[stat.ST_SIZE]

        self.set_and_save_hash()

        ### @export "initial-artifact-output-data"
        self.output_data = dexy.data.Data.aliases['generic'](self.metadata.hashstring, self.ext, self.run_params)

        if os.path.exists(self.name):
            if not self.output_data.is_cached():
                self.output_data.copy_from_file(self.name)

            assert self.output_data.is_cached()

        else:
            raise Exception("No file %s found!" % self.name)

### @export "filter-artifact-run"
class FilterArtifact(Artifact):
    def run(self, runner):
        self.runner = runner
        self.input_data = self.prior.output_data

        self.set_extension()
        self.set_name()
        self.set_metadata_hash()
        self.set_output_data()
        ### @end

        ### @export "artifact-output-data"
        if not self.output_data.is_cached():
            self.log.debug("Running filter %s" % self.filter_class.__name__)
            self.generate()
        else:
            # TODO load additional artifacts that are in cache
            pass

        self.runner.append(self)
        ### @end

    def set_output_data(self):
        output_data_class = self.filter_class.output_data_class()
        self.output_data = output_data_class(self.metadata.hashstring, self.ext, self.runner)

    def set_metadata_hash(self):
        self.metadata.ext = self.ext
        self.metadata.key = self.key
        self.metadata.next_filter_name = self.next_filter_name
        self.metadata.prior_hash = self.prior.metadata.hashstring

        strargs = []
        for k in sorted(self.args):
            v = str(self.args[k])
            strargs.append("%s: %s" % (k, v))
        self.metadata.argstr = ", ".join(strargs)

        tree_hash = []
        for key, task in self.runner.completed.iteritems():
            if hasattr(task, 'metadata'):
                tree_hash.append("%s: %s" % (key, task.metadata.hashstring))
        self.metadata.tree_hash = ", ".join(tree_hash)

        self.metadata.dexy_version = dexy.__version__
        self.metadata.pre_method_source = inspect.getsource(self.pre)
        self.metadata.post_method_source = inspect.getsource(self.post)

        sources = []
        klass = self.filter_class
        while klass != dexy.filter.Filter:
            sources.append(dexy.filter.Filter.source[klass.__name__])
            klass = klass.__base__
        sources.append(dexy.filter.Filter.source[klass.__name__])
        self.metadata.filter_source = "\n".join(sources)

        # TODO add filter software version

        self.set_and_save_hash()

    def add_doc(self, doc):
        doc.parent_hash = self.metadata.hashstring
        self.doc.children.append(doc)

    ### @export "set-extension"
    def set_extension(self):
        """
        Determine the file extension that should be output by this artifact.
        """

        # Extensions can be specified in filter args
        ext = self.filter_args().get('ext')
        if ext:
            if not ext.startswith('.'):
                ext = '.%s' % ext
            self.ext = ext

        # Or else calculate them based on what next filter can accept
        else:
            if self.next_filter_class:
                next_inputs = self.next_filter_class.INPUT_EXTENSIONS
            else:
                next_inputs= None

            self.ext = self.filter_class.output_file_extension(
                    self.prior.ext,
                    self.key,
                    next_inputs)

    def set_name(self):
        self.name_without_ext = os.path.splitext(self.doc_filepath)[0]
        self.name = "%s%s" % (self.name_without_ext, self.ext)

    ### @export "generate"
    def generate(self, *args, **kw):
        filter_instance = self.filter_class()
        filter_instance.artifact = self
        filter_instance.log = self.log
        filter_instance.process()

    ### @export "filter-args"
    def filter_args(self):
        """
        Arguments that are passed by the user which are specifically for the
        filter that will be run by this artifact.
        """
        return self.args.get(self.filter_alias, {})

from dexy.constants import Constants
from dexy.sizeof import asizeof
from dexy.version import Version
from ordereddict import OrderedDict
import dexy.introspect
import glob
import hashlib
import inspect
import logging
import os
import shutil
import stat
import sys
import time
import traceback

class Artifact(object):
    HASH_WHITELIST = Constants.ARTIFACT_HASH_WHITELIST
    META_ATTRS = [
        'additional',
        'binary_input',
        'binary_output',
        'created_by',
        'document_key',
        'elapsed',
        'ext',
        'final',
        'initial',
        'is_last',
        'key',
        'name',
        'output_hash',
        'state',
        'stdout'
    ]


    BINARY_EXTENSIONS = [
        '.gif',
        '.jpg',
        '.png',
        '.pdf',
        '.zip',
        '.tgz',
        '.gz',
        '.eot',
        '.ttf',
        '.woff',
        '.swf'
    ]

    @classmethod
    def artifacts(self):
        """Lists available artifact classes."""
        pass

    def __init__(self):
        if not hasattr(self.__class__, 'FILTERS'):
            self.__class__.FILTERS = dexy.introspect.filters(Constants.NULL_LOGGER)
        if not hasattr(self.__class__, 'SOURCE_CODE'):
            artifact_class_source = inspect.getsource(self.__class__)
            artifact_py_source = inspect.getsource(Artifact)
            self.__class__.SOURCE_CODE = hashlib.md5(artifact_class_source + artifact_py_source).hexdigest()

        self._inputs = {}
        self.additional = None
        self.args = {}
        self.args['globals'] = {}
        self.created_by = None
        self.controller_args = {}
        self.controller_args['globals'] = {}
        self.ext = None
        self.name = None
        self.source = None
        self.start_time = None
        self.finish_time = None
        self.elapsed = None

        self.is_last = False
        self.artifact_class_source = self.__class__.SOURCE_CODE
        self.artifacts_dir = 'artifacts' # TODO don't hard code
        self.batch_id = None
        self.batch_order = None
        self.binary_input = None
        self.binary_output = None
        self.ctime = None
        self.data_dict = OrderedDict()
        self.dexy_version = Version.VERSION
        self.dirty = False
        self.document_key = None
        self.elapsed = 0
        self.final = None
        self.initial = None
        self.inode = None
        self.input_data_dict = OrderedDict()
        self.key = None
        self.log = logging.getLogger()
        self.mtime = None
        self.state = 'new'
        self.stdout = None

    def is_complete(self):
        return str(self.state) == 'complete'

    @classmethod
    def retrieve(klass, hashstring):
        if not hasattr(klass, 'retrieved_artifacts'):
            klass.retrieved_artifacts = {}
        if klass.retrieved_artifacts.has_key(hashstring):
            return klass.retrieved_artifacts[hashstring]
        else:
            artifact = klass()
            artifact.hashstring = hashstring
            artifact.load()
            klass.retrieved_artifacts[hashstring] = artifact
            return artifact

    def load(self):
        self.load_meta()
        self.load_input()
        if self.is_complete() and not self.is_loaded():
            self.load_output()

    def load_inputs(self):
        for a in self.inputs():
            a.load()

    def save(self):
        if self.is_abstract():
            pass # For testing.
        elif not self.hashstring:
            raise Exception("can't persist an artifact without a hashstring!")
        else:
            self.save_meta()
            if self.is_complete() and not self.is_output_cached():
                try:
                    self.save_output()
                except IOError as e:
                    print "An error occured while saving %s" % self.key
                    raise e

    def is_abstract(self):
        return not hasattr(self, 'save_meta')

    def setup_initial(self):
        """
        Set up an initial artifact (the first artifact in a document's filter chain).
        """
        self._inputs = self.doc.input_artifacts()
        self.binary_input = (self.doc.ext in self.BINARY_EXTENSIONS)
        self.binary_output = self.binary_input
        self.ext = self.doc.ext
        self.initial = True

        if self.args.has_key('final'):
            self.final = self.args['final']
        elif os.path.basename(self.name).startswith("_"):
            self.final = False

        if not self.doc.virtual:
            stat_info = os.stat(self.name)
            self.ctime = stat_info[stat.ST_CTIME]
            self.mtime = stat_info[stat.ST_MTIME]
            self.inode = stat_info[stat.ST_INO]

        self.set_data(self.doc.initial_artifact_data())

        # TODO remove?
        if not self.data_dict:
            raise Exception("no data dict!")
        elif len(self.data_dict) == 0:
            raise Exception("data dict has len 0!")

        self.state = 'complete'

    def setup_from_filter_class(self):
        # cache filter class source code so it only has to be calculated once
        if not hasattr(self.filter_class, 'SOURCE_CODE'):
            filter_class_source = inspect.getsource(self.filter_class)
            self.filter_class.SOURCE_CODE = hashlib.md5(filter_class_source).hexdigest()

        self.filter_name = self.filter_class.__name__
        self.filter_source = self.filter_class.SOURCE_CODE
        self.filter_version = self.filter_class.version(self.log)

        if self.final is None:
            self.final = self.filter_class.FINAL

    def setup_from_previous_artifact(self, previous_artifact):
        for a in ['final', 'mtime', 'ctime', 'inode']:
                setattr(self, a, getattr(previous_artifact, a))

        self._inputs.update(previous_artifact.inputs())
        # Need to loop over each artifact's inputs in case extra ones have been
        # added anywhere.
        for k, a in previous_artifact.inputs().iteritems():
            self._inputs.update(a.inputs())

        self.binary_input = previous_artifact.binary_output
        self.input_data_dict = previous_artifact.data_dict
        self.input_ext = previous_artifact.ext
        self.previous_artifact_filename = previous_artifact.filename()
        self.previous_artifact_filepath = previous_artifact.filepath()
        self.previous_canonical_filename = previous_artifact.canonical_filename(True)

        # The JSON output of previous artifact
        if not previous_artifact.binary_output:
            self.previous_cached_output_filepath = previous_artifact.cached_output_filepath()

        # Determine file extension of output
        if hasattr(self, 'next_filter_class'):
            next_inputs = self.next_filter_class.INPUT_EXTENSIONS
        else:
            next_inputs = None

        self.ext = self.filter_class.output_file_extension(
                previous_artifact.ext,
                self.name,
                next_inputs)

        self.binary_output = self.filter_class.BINARY
        if self.binary_output is None:
            self.set_binary_from_ext()

        self.state = 'setup'

    @classmethod
    def setup(klass, doc, artifact_key, filter_class = None, previous_artifact = None):
        """
        Create an Artifact instance and load all information needed to
        calculate its hashstring.
        """
        artifact = klass()
        artifact.key = artifact_key
        artifact.filter_class = filter_class

        # Add references for convenience
        artifact.artifacts_dir = doc.artifacts_dir
        artifact.controller_args = doc.controller.args
        artifact.db = doc.db
        artifact.doc = doc
        artifact.log = doc.log

        # These attributes are the same for all artifacts pertaining to a document
        artifact.args = doc.args
        artifact.batch_id = doc.batch_id
        artifact.document_key = doc.key()
        artifact.name = doc.name

        # Set batch order to next in sequence
        artifact.batch_order = artifact.db.next_batch_order(artifact.batch_id)

        next_filter_class = doc.next_filter_class()
        if next_filter_class:
            artifact.next_filter_name = next_filter_class.__name__
            artifact.next_filter_class = next_filter_class

        if previous_artifact:
            artifact.setup_from_previous_artifact(previous_artifact)
            artifact.setup_from_filter_class()
        else:
            artifact.setup_initial()

        artifact.set_hashstring()

        return artifact

    def run(self):
        self.start_time = time.time()

        if self.doc.profmem:
            print "  size of artifact", asizeof(self)
            tot = 0
            for x in sorted(self.__dict__.keys()):
                y = self.__dict__[x]
                tot += asizeof(y)
                print "  ", x, asizeof(y)
            print "  tot", tot

        if self.controller_args['nocache'] or not self.is_complete():
            # We have to actually run things...
            if not self.filter_class:
                self.filter_class = dexy.introspect.get_filter_by_name(self.filter_name, self.doc.__class__.filter_list)

            # Set up instance of filter.
            filter_instance = self.filter_class()
            filter_instance.artifact = self
            filter_instance.log = self.log

            try:
                filter_instance.process()
            except Exception as e:
                print "Error occurred while running", self.key
                x, y, tb = sys.exc_info()
                print "Original traceback:"
                traceback.print_tb(tb)
                pattern = os.path.join(self.artifacts_dir, self.hashstring)
                files_matching = glob.glob(pattern)
                if len(files_matching) > 0:
                    print "Here are working files which might have clues about this error:"
                    for f in files_matching:
                        print f
                raise e

            h = hashlib.sha512()

            if self.data_dict and len(self.data_dict) > 0:
                h.update(self.output_text())

            elif self.is_canonical_output_cached:
                self.state = 'complete'
                self.save()

                f = open(self.filepath(), "rb")
                while True:
                    data = f.read(h.block_size)
                    if not data:
                        break
                    h.update(data)

            else:
                raise Exception("data neither in memory nor on disk")

            self.output_hash = h.hexdigest()

            self.state = 'complete'
            self.finish_time = time.time()
            self.elapsed = self.finish_time - self.start_time
            self.source = 'run'
            self.save()
        else:
            self.source = 'cache'
            self.log.debug("using cached artifact for %s" % self.key)

            # make sure additional artifacts are added to db
            for a in self.inputs().values():
                if a.created_by == self.key:
                    if not a.additional:
                        raise Exception("created_by should only apply to additional artifacts")
                    # TODO Should this be done in Artifact.retrieve?
                    a.batch_id = self.batch_id
                    self.db.append_artifact(a)

        self.db.update_artifact(self)

    def add_additional_artifact(self, key_with_ext, ext):
        """create an 'additional' artifact with random hashstring"""
        new_artifact = self.__class__()
        new_artifact.key = key_with_ext
        if ext.startswith("."):
            new_artifact.ext = ext
        else:
            new_artifact.ext = ".%s" % ext
        new_artifact.final = True
        new_artifact.additional = True
        new_artifact.set_binary_from_ext()
        new_artifact.artifacts_dir = self.artifacts_dir
        new_artifact.inode = self.hashstring
        new_artifact.created_by = self.document_key
        # TODO filter class source?

        # TODO this is duplicated in setup_from_previous_artifact, should reorganize
        for at in ['batch_id', 'document_key', 'mtime', 'ctime']:
                val = getattr(self, at)
                setattr(new_artifact, at, val)

        new_artifact.set_hashstring()
        self.add_input(key_with_ext, new_artifact)
        self.db.append_artifact(new_artifact) # append to db because not part of doc.artifacts
        return new_artifact

    def add_input(self, key, artifact):
        self._inputs[key] = artifact

    def inputs(self):
        return self._inputs

    def set_binary_from_ext(self):
        # TODO list more binary extensions or find better way to do this
        if self.ext in self.BINARY_EXTENSIONS:
            self.binary_output = True
        else:
            self.binary_output = False

    def set_data(self, data):
        self.data_dict['1'] = data

    def set_data_from_artifact(self):
        f = open(self.filepath())
        self.data_dict['1'] = f.read()

    def is_loaded(self):
        return hasattr(self, 'data_dict') and len(self.data_dict) > 0

    def hash_dict(self):
        """Return the elements for calculating the hashstring."""
        if self.dirty:
            self.dirty_string = time.gmtime()

        hash_dict = OrderedDict()

        hash_dict['inputs'] = OrderedDict()
        sorted_input_keys = sorted(self.inputs().keys())
        for k in sorted_input_keys:
            hash_dict['inputs'][str(k)] = str(self.inputs()[k].hashstring)

        for k in self.HASH_WHITELIST:
            if self.__dict__.has_key(k):
                v = self.__dict__[k]
                if hasattr(v, 'items'):
                    hash_v = OrderedDict()
                    for k1 in sorted(v.keys()):
                        v1 = v[k1]
                        hash_v[str(k1)] = hashlib.md5(str(v1)).hexdigest()
                else:
                    hash_v = str(v)
                hash_dict[str(k)] = hash_v

        return hash_dict

    def set_hashstring(self):
        hash_data = str(self.hash_dict())
        self.hashstring = hashlib.md5(hash_data).hexdigest()

        debug_me = False
        if debug_me:
            for k, v in self.hash_dict().iteritems():
                if hasattr(v, 'items'):
                    print k, ":"
                    for k1, v1 in v.items():
                        print "  ", k1, ":", v1
                else:
                    print k, ":", v
            print hash_data
            print ">>>>>", self.hashstring

        try:
            original_document_key = self.document_key
            if not self.is_loaded():
                self.load()
            self.document_key = original_document_key
        except AttributeError as e:
            if not self.is_abstract():
                raise e
        except IOError as e:
            self.save_meta()

    def command_line_args(self):
        """
        Allow specifying command line arguments which are passed to the filter
        with the given key. Note that this does not currently allow
        differentiating between 2 calls to the same filter in a single document.
        """
        if self.args.has_key('args'):
            args = self.args['args']
            last_key = self.key.rpartition("|")[-1]
            if args.has_key(last_key):
                return args[last_key]

    def input_text(self):
        return "".join([v for k, v in self.input_data_dict.items()])

    def output_text(self):
        return "".join([v for k, v in self.data_dict.items()])

    def relative_refs(self, relative_to_file):
        """How to refer to this artifact, relative to another."""

        doc_dir = os.path.dirname(relative_to_file)
        return [
                os.path.relpath(self.key, doc_dir),
                os.path.relpath(self.long_canonical_filename(), doc_dir),
                "/%s" % self.key,
                "/%s" % self.long_canonical_filename()
        ]

    def use_canonical_filename(self):
        """Returns the canonical filename after saving contents under this name
        in the artifacts directory."""
        self.write_to_file(os.path.join(self.artifacts_dir,
                                        self.canonical_filename()))
        return self.canonical_filename()

    def write_to_file(self, filename):
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname) and not dirname == '':
            os.makedirs(dirname)
        shutil.copyfile(self.filepath(), filename)

    def work_filename(self):
        return "%s.work%s" % (self.hashstring, self.input_ext)

    def generate_workfile(self, work_filename = None):
        if not work_filename:
            work_filename = self.work_filename()
        work_path = os.path.join(self.artifacts_dir, work_filename)
        work_file = open(work_path, "w")
        work_file.write(self.input_text())
        work_file.close()

    def temp_filename(self, ext):
        return "%s.work%s" % (self.hashstring, ext)

    def open_tempfile(self, ext):
        tempfile_path = os.path.join(self.artifacts_dir, self.temp_filename(ext))
        open(tempfile_path, "w")

    def temp_dir(self):
        return os.path.join(self.artifacts_dir, self.hashstring)

    def create_temp_dir(self, populate=False):
        tempdir = self.temp_dir()
        shutil.rmtree(tempdir, ignore_errors=True)
        os.mkdir(tempdir)

        if populate:
            # write all inputs to this directory, under their canonical names
            for input_artifact in self._inputs.values():
                filename = os.path.join(tempdir, input_artifact.canonical_filename())
                input_artifact.write_to_file(filename)

            # write the workfile to this directory under its canonical name
            previous = self.previous_artifact_filepath
            workfile = os.path.join(tempdir, self.previous_canonical_filename)
            if not os.path.exists(os.path.dirname(workfile)):
                os.makedirs(os.path.dirname(workfile))
            shutil.copyfile(previous, workfile)

    def canonical_basename(self):
        return os.path.basename(self.canonical_filename())

    def canonical_filename(self, ignore_args = False):
        fn = os.path.splitext(self.key.split("|")[0])[0]

        if self.args.has_key('canonical-name') and not ignore_args:
            parent_dir = os.path.dirname(fn)
            return os.path.join(parent_dir, self.args['canonical-name'])
        elif self.args.has_key('postfix') and not ignore_args:
            return "%s%s%s" % (fn, self.ext, self.args['postfix'])
        else:
            return "%s%s" % (fn, self.ext)

    def long_canonical_filename(self):
        return "%s%s" % (self.key.replace("|", "-"), self.ext)

    def filename(self):
        """
        The filename where artifact content is stored, based on the hashstring.
        """
        if not hasattr(self, 'ext'):
            raise Exception("artifact %s has no ext" % self.key)
        return "%s%s" % (self.hashstring, self.ext)

    def filepath(self):
        """
        Full path (including artifacts dir location) to location where artifact content is stored.
        """
        return os.path.join(self.artifacts_dir, self.filename())

    def breadcrumbs(self):
        """A list of parent dirs, plus the filename if it's not 'index.html'."""
        parent_dirs = os.path.dirname(self.canonical_filename()).split("/")

        if self.canonical_basename() == "index.html":
            result = parent_dirs
        else:
            result = parent_dirs.append(self.canonical_basename())

        if not result:
            result = []

        return result

    def titleized_name(self):
        if self.canonical_basename() == "index.html":
            return self.breadcrumbs()[-1].title()
        else:
            return os.path.splitext(self.canonical_basename())[0].title()

    def unique_key(self):
        return "%s:%s:%s" % (self.batch_id, self.document_key, self.key)

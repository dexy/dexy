from dexy.constants import Constants
from dexy.sizeof import asizeof
from dexy.version import Version
from ordereddict import OrderedDict
import dexy.introspect
import glob
import hashlib
import inspect
import json
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
        self.db = [] # accepts 'append'
        self.args = {}
        self.args['globals'] = {}

        self.is_last = False
        self.artifact_class_source = self.__class__.SOURCE_CODE
        self.artifacts_dir = 'artifacts' # TODO don't hard code
        self.batch_id = None
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
                self.save_output()

    def is_abstract(self):
        return not hasattr(self, 'save_meta')

    def setup_from_filter_class(self, filter_class):
        if not hasattr(filter_class, 'SOURCE_CODE'):
            filter_class_source = inspect.getsource(filter_class)
            filter_class.SOURCE_CODE = hashlib.md5(filter_class_source).hexdigest()

        if self.final is None and filter_class.FINAL is not None:
            self.final = filter_class.FINAL

        self.filter_class = filter_class
        self.filter_name = filter_class.__name__
        self.filter_source = filter_class.SOURCE_CODE
        self.filter_version = filter_class.version(self.log)

    def setup_from_previous_artifact(self, previous_artifact):
        assert self.filter_class
        if self.final is None:
            self.final = previous_artifact.final

        self.binary_input = previous_artifact.binary_output
        self.input_ext = previous_artifact.ext
        self.input_data_dict = previous_artifact.data_dict
        for at in ['batch_id', 'document_key', 'mtime', 'ctime', 'inode']:
                val = getattr(previous_artifact, at)
                setattr(self, at, val)

        # The 'canonical' output of previous artifact
        self.previous_artifact_filename = previous_artifact.filename()
        self.previous_artifact_filepath = previous_artifact.filepath()
        self.previous_canonical_filename = previous_artifact.canonical_filename()
        # The JSON output of previous artifact
        if not previous_artifact.binary_output:
            self.previous_cached_output_filepath = previous_artifact.cached_output_filepath()

        self._inputs.update(previous_artifact.inputs())
        # Need to loop over each artifact's inputs in case extra ones have been
        # added anywhere.
        for k, a in previous_artifact.inputs().iteritems():
            self._inputs.update(a.inputs())

        if hasattr(self, 'next_filter_class'):
            next_inputs = self.next_filter_class.INPUT_EXTENSIONS
        else:
            next_inputs = None

        self.ext = self.filter_class.output_file_extension(
                previous_artifact.ext,
                self.name,
                next_inputs
                )
        self.binary_output = self.filter_class.BINARY
        self.state = 'setup'

    @classmethod
    def setup(klass, doc, artifact_key, filter_class = None, previous_artifact = None):
        """Set up a new artifact."""
        artifact = klass()

        artifact.doc = doc
        artifact.controller_args = doc.controller.args
        artifact.db = doc.db

        artifact.args = doc.args
        artifact.artifacts_dir = doc.artifacts_dir
        artifact.key = artifact_key
        artifact.log = doc.log
        artifact.batch_id = doc.batch_id
        artifact.name = doc.name
        artifact.filters = doc.filters
        artifact.document_key = doc.key()

        if artifact.args.has_key('final'):
            # TODO move this into initial setup? Should only be needed once...
            artifact.final = artifact.args['final']
        elif hasattr(previous_artifact, 'final') and previous_artifact.final is not None:
            artifact.final = previous_artifact.final

        if filter_class:
            artifact.setup_from_filter_class(filter_class)

        if doc.next_filter_class():
            artifact.next_filter_name = doc.next_filter_class().__name__
            artifact.next_filter_class = doc.next_filter_class()

        if previous_artifact:
            artifact.setup_from_previous_artifact(previous_artifact)
        else:
            # This is an initial artifact
            artifact.initial = True
            artifact._inputs = doc.input_artifacts()
            artifact.ext = os.path.splitext(doc.name)[1]

            if not doc.virtual:
                stat_info = os.stat(doc.name)
                artifact.ctime = stat_info[stat.ST_CTIME]
                artifact.mtime = stat_info[stat.ST_MTIME]
                artifact.inode = stat_info[stat.ST_INO]

            artifact.binary_input = (doc.ext in artifact.BINARY_EXTENSIONS)
            artifact.set_data(doc.initial_artifact_data())
            if not artifact.data_dict:
                raise Exception("no data dict!")
            elif len(artifact.data_dict) == 0:
                raise Exception("data dict has len 0!")

            if os.path.basename(doc.name).startswith("_"):
                artifact.final = False
            artifact.state = 'complete'

        if artifact.binary_output is None:
            artifact.set_binary_from_ext()

        artifact.set_hashstring()

        artifact.db.append(artifact)
        return artifact

    def run(self):
        start_time = time.time()

        if self.doc.profmem:
            print "  size of artifact", asizeof(self)
            tot = 0
            for x in sorted(self.__dict__.keys()):
                y = self.__dict__[x]
                tot += asizeof(y)
                print "  ", x, asizeof(y)
            print "  tot", tot

        if not self.is_complete():
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
            finish_time = time.time()
            self.elapsed = finish_time - start_time
            self.save()
        else:
            self.log.debug("using cached art %s" % self.key)


    def add_additional_artifact(self, key_with_ext, ext):
        """create an 'additional' artifact with random hashstring"""
        new_artifact = self.__class__()
        new_artifact.key = key_with_ext
        new_artifact.ext = ".%s" % ext
        new_artifact.final = True
        new_artifact.additional = True
        new_artifact.set_binary_from_ext()
        new_artifact.artifacts_dir = self.artifacts_dir
        new_artifact.inode = self.hashstring

        # TODO this is duplicated in setup_from_previous_artifact, should reorganize
        for at in ['batch_id', 'document_key', 'mtime', 'ctime']:
                val = getattr(self, at)
                setattr(new_artifact, at, val)

        new_artifact.set_hashstring()
        self.add_input(key_with_ext, new_artifact)
        self.db.append(new_artifact)
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
            if not self.is_loaded():
                self.load()
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
                os.path.relpath(self.canonical_filename(), doc_dir),
                os.path.relpath(self.long_canonical_filename(), doc_dir),
                "/%s" % self.key,
                "/%s" % self.canonical_filename(),
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

    def create_temp_dir(self):
        shutil.rmtree(self.temp_dir(), ignore_errors=True)
        os.mkdir(self.temp_dir())

    def canonical_basename(self):
        return os.path.basename(self.canonical_filename())

    def canonical_filename(self):
        fn = os.path.splitext(self.key.split("|")[0])[0]
        return "%s%s" % (fn, self.ext)

    def long_canonical_filename(self):
        return "%s%s" % (self.key.replace("|", "-"), self.ext)

    def filename(self):
        if not hasattr(self, 'ext'):
            raise Exception("artifact %s has no ext" % self.key)
        return "%s%s" % (self.hashstring, self.ext)

    def filepath(self):
        return os.path.join(self.artifacts_dir, self.filename())

    def unique_key(self):
        return "%s:%s:%s" % (self.batch_id, self.document_key, self.key)

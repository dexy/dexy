from dexy.constants import Constants
from dexy.version import Version
from ordereddict import OrderedDict
import codecs
import dexy.introspect
import json
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
import zlib

class Artifact(object):
    HASH_WHITELIST = Constants.ARTIFACT_HASH_WHITELIST
    MAX_DATA_DICT_DECIMALS = 5
    MAX_DATA_DICT_LENGTH = 10 ** MAX_DATA_DICT_DECIMALS
    META_ATTRS = [
        'additional',
        'binary_input',
        'binary_output',
        'created_by',
        'document_key',
        'ext',
        'final',
        'hashfunction',
        'initial',
        'is_last',
        'logstream',
        'key',
        'name',
        'output_hash',
        'state',
        'stdout',
        'virtual'
    ]

    BINARY_EXTENSIONS = [
         '.docx',
        '.epub',
        '.gif',
        '.jpg',
        '.png',
        '.pdf',
        '.zip',
        '.tgz',
        '.gz',
        '.eot',
        '.ttf',
        '.odt',
        '.rtf',
        '.woff',
        '.sqlite',
        '.sqlite3',
        '.swf'
    ]

    def __init__(self):
        if not hasattr(self.__class__, 'FILTERS'):
            self.__class__.FILTERS = dexy.introspect.filters(Constants.NULL_LOGGER)

        self._inputs = {}
        self.additional = None
        self.args = {}
        self.args['globals'] = {}
        self.artifacts_dir = 'artifacts' # TODO don't hard code
        self.batch_id = None
        self.batch_order = None
        self.binary_input = None
        self.binary_output = None
        self.controller_args = {}
        self.controller_args['globals'] = {}
        self.created_by = None
        self.ctime = None
        self.data_dict = OrderedDict()
        self.dexy_version = Version.VERSION
        self.dirty = False
        self.document_key = None
        self.elapsed = 0
        self.ext = None
        self.final = None
        self.finish_time = None
        self.hashfunction = 'md5'
        self.initial = None
        self.inode = None
        self.input_data_dict = OrderedDict()
        self.is_last = False
        self.key = None
        self.log = logging.getLogger()
        self.logstream = ""
        self.mtime = None
        self.name = None
        self.source = None
        self.start_time = None
        self.state = 'new'
        self.stdout = None

    def is_complete(self):
        return str(self.state) == 'complete'

    @classmethod
    def retrieve(klass, hashstring, hashfunction='md5'):
        if not hasattr(klass, 'retrieved_artifacts'):
            klass.retrieved_artifacts = {}
        if klass.retrieved_artifacts.has_key(hashstring):
            return klass.retrieved_artifacts[hashstring]
        else:
            artifact = klass()
            artifact.hashstring = hashstring
            artifact.hashfunction = hashfunction
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
        self._inputs = {}
        self.binary_input = (self.doc.ext in self.BINARY_EXTENSIONS)
        self.binary_output = self.binary_input
        self.ext = self.doc.ext
        self.initial = True
        self.virtual = self.doc.virtual
        self.virtual_docs = self.doc.virtual_docs

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
            # get source code of this filter class + all parent filter classes.
            source = ""
            klass = self.filter_class

            # get source code from filter class and all parent classes
            while klass != dexy.dexy_filter.DexyFilter:
                source += inspect.getsource(klass)
                klass = klass.__base__

            # and then get source code of DexyFilter class
            source += inspect.getsource(dexy.dexy_filter.DexyFilter)

            filter_class_source = source
            self.filter_class.SOURCE_CODE = self.compute_hash(filter_class_source)

        if not hasattr(self.filter_class, 'VERSION'):
            filter_version = self.filter_class.version(self.log)
            self.filter_class.VERSION = filter_version

        self.filter_name = self.filter_class.__name__
        self.filter_source = self.filter_class.SOURCE_CODE
        self.filter_version = self.filter_class.VERSION

        if self.final is None:
            self.final = self.filter_class.FINAL

    def setup_from_previous_artifact(self, previous_artifact):
        for a in ['final', 'mtime', 'ctime', 'inode', 'virtual', 'virtual_docs']:
                setattr(self, a, getattr(previous_artifact, a))

        # Look for additional inputs in previous artifacts or previous
        # artifacts' inputs.
        for k, a in previous_artifact.inputs().iteritems():

            if a.additional and not k in self._inputs:
                self.log.debug("(%s) Adding additional artifact %s from %s" % (self.key, k, a.key))
                self.add_input(k, a)
            elif not k in self._inputs:
                # We should have all other inputs already. Validate this.
                raise Exception("Missing input %s" % k)

            for kk, aa in a.inputs().iteritems():
                if aa.additional and not kk in self._inputs:
                    self.log.debug("(%s) Adding additional artifact %s from %s" % (self.key, kk, k))
                    self.add_input(kk, aa)

        self.binary_input = previous_artifact.binary_output
        self.input_data_dict = previous_artifact.data_dict
        self.input_ext = previous_artifact.ext
        self.previous_artifact_filename = previous_artifact.filename()
        self.previous_artifact_filepath = previous_artifact.filepath()
        self.previous_canonical_filename = previous_artifact.canonical_filename(True)
        self.previous_long_canonical_filename = previous_artifact.long_canonical_filename()
        self.previous_websafe_key = previous_artifact.websafe_key()

        # The JSON output of previous artifact
        if not previous_artifact.binary_output:
            self.previous_cached_output_filepath = previous_artifact.cached_output_filepath()

        # Determine file extension of output
        if hasattr(self, 'next_filter_class'):
            next_inputs = self.next_filter_class.INPUT_EXTENSIONS
        else:
            next_inputs = None

        if self.args.has_key('ext'):
            ext = self.args['ext']
            if not ext.startswith("."):
                ext = ".%s" % ext
            self.ext = ext
        else:
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
        artifact.hashfunction = doc.controller.args['hashfunction']
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

        # Set inputs from original document inputs.
        artifact._inputs.update(artifact.doc.input_artifacts())
        artifact.log.debug("add inputs from document %s: %s" % (artifact.doc.key(), ", ".join(artifact.doc.input_artifacts().keys())))

        for k, a in artifact.doc.input_artifacts().iteritems():
            if a.additional and not k in artifact._inputs:
                artifact.add_input(k, a)

            for kk, aa in a.inputs().iteritems():
                if aa.additional and not kk in artifact._inputs:
                    artifact.add_input(kk, aa)

        if previous_artifact:
            artifact.setup_from_previous_artifact(previous_artifact)
            artifact.setup_from_filter_class()
        else:
            artifact.setup_initial()

        artifact.set_hashstring()

        return artifact

    def run(self):

        start = time.time()

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
                # TODO Clean this up, should all go to stderr probably.
                print "Error occurred while running", self.key
                x, y, tb = sys.exc_info()
                print "Original traceback:"
                traceback.print_tb(tb, sys.stdout)
                pattern = os.path.join(self.artifacts_dir, self.hashstring)
                files_matching = glob.glob(pattern)
                if len(files_matching) > 0:
                    print "Here are working files which might have clues about this error:"
                    for f in files_matching:
                        print f
                raise e

            if self.data_dict and len(self.data_dict) > 0:
                pass

            elif self.is_canonical_output_cached:
                self.state = 'complete'
                self.save()

            else:
                raise Exception("data neither in memory nor on disk")

            self.logstream = self.doc.logstream.getvalue()
            self.state = 'complete'
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

        self.elapsed = time.time() - start
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
        new_artifact.hashfunction = self.hashfunction
        new_artifact.additional = True
        new_artifact.set_binary_from_ext()
        new_artifact.artifacts_dir = self.artifacts_dir
        new_artifact.inode = self.hashstring
        new_artifact.created_by = self.document_key
        new_artifact.virtual = True
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
        f = codecs.open(self.filepath(), "r", encoding="utf-8")
        self.data_dict['1'] = f.read()

    def is_loaded(self):
        return hasattr(self, 'data_dict') and len(self.data_dict) > 0

    def compute_hash(self, text):
        unicode_text = None

        if type(text) == unicode:
            unicode_text = text
        elif type(text) in [dict, list]:
            unicode_text = json.dumps(text)
        elif self.binary_input:
            pass
        else:
            unicode_text = unicode(text, encoding="utf-8")

        if unicode_text:
            text = unicode_text.encode("utf-8")

        if self.hashfunction == 'md5':
            h = hashlib.md5(text).hexdigest()

        elif self.hashfunction == 'sha1':
            h = hashlib.sha1(text).hexdigest()

        elif self.hashfunction == 'sha224':
            h = hashlib.sha224(text).hexdigest()

        elif self.hashfunction == 'sha256':
            h = hashlib.sha256(text).hexdigest()

        elif self.hashfunction == 'sha384':
            h = hashlib.sha384(text).hexdigest()

        elif self.hashfunction == 'sha512':
            h = hashlib.sha512(text).hexdigest()

        elif self.hashfunction == 'crc32':
            h = str(zlib.crc32(text) & 0xffffffff)

        elif self.hashfunction == 'adler32':
            h = str(zlib.adler32(text) & 0xffffffff)

        else:
            raise Exception("unexpected hash function %s" % self.hashfunction)

        return h

    def input_hashes(self):
        """
        Returns an OrderedDict of key, hashstring for each input artifact, sorted by key.
        """
        return OrderedDict((k, str(self.inputs()[k].hashstring)) for k in sorted(self.inputs()))

    def hash_dict(self):
        """
        Calculate and cache the elements used to compute the hashstring
        """
        if not hasattr(self.__class__, 'SOURCE_CODE'):
            artifact_class_source = inspect.getsource(self.__class__)
            artifact_py_source = inspect.getsource(Artifact)
            self.__class__.SOURCE_CODE = self.compute_hash(artifact_class_source + artifact_py_source)

        self.artifact_class_source = self.__class__.SOURCE_CODE

        if self.dirty:
            self.dirty_string = time.gmtime()

        hash_dict = OrderedDict()

        hash_dict['inputs'] = self.input_hashes()

        for k in self.HASH_WHITELIST:
            if self.__dict__.has_key(k):
                v = self.__dict__[k]
                if hasattr(v, 'items'):
                    hash_v = OrderedDict()
                    for k1 in sorted(v.keys()):
                        v1 = v[k1]
                        try:
                            if len(str(v1)) > 50:
                                raise Exception()
                            json.dumps(v1)
                            hash_v[str(k1)] = v1
                        except Exception:
                            # Use a hash if we will have problems saving to JSON
                            # or if the data is large (don't want to clutter up the DB,
                            # makes it harder to spot differences)
                            hash_v[str(k1)] = self.compute_hash(v1)
                else:
                    hash_v = str(v)
                hash_dict[str(k)] = hash_v
        return hash_dict

    def set_hashstring(self):
        if hasattr(self, 'hashstring'):
            raise Exception("setting hashstring twice")

        hash_data = str(self.hash_dict())
        self.hashstring = self.compute_hash(hash_data)

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


    def convert_if_not_unicode(self, s):
        if type(s) == unicode:
            return s
        elif s == None:
            return u""
        else:
            try:
                ut = unicode(s, encoding="utf-8")
                return ut
            except Exception as e:
                print "error occurred trying to convert text to unicode in", self.key
                raise e


    def input_text(self):
        return u"".join([self.convert_if_not_unicode(v) for k, v in self.input_data_dict.items()])

    def output_text(self):
        return u"".join([self.convert_if_not_unicode(v) for k, v in self.data_dict.items()])

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
        work_file = codecs.open(work_path, "w", encoding="utf-8")
        work_file.write(self.input_text())
        work_file.close()

    def temp_filename(self, ext):
        return "%s.work%s" % (self.hashstring, ext)

    def open_tempfile(self, ext):
        tempfile_path = os.path.join(self.artifacts_dir, self.temp_filename(ext))
        codecs.open(tempfile_path, "w", encoding="utf-8")

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
                if os.path.exists(input_artifact.filepath()):
                    input_artifact.write_to_file(filename)
                    self.log.debug("Populating temp dir for %s with %s" % (self.key, filename))
                else:
                    self.log.warn("Skipping file %s for temp dir for %s, file does not exist (yet)" % (filename, self.key))

            # write the workfile to this directory under its canonical name
            previous = self.previous_artifact_filepath
            workfile = os.path.join(tempdir, self.previous_canonical_filename)
            if not os.path.exists(os.path.dirname(workfile)):
                os.makedirs(os.path.dirname(workfile))
            shutil.copyfile(previous, workfile)

    def alias(self):
        """
        Whether this artifact includes an alias.
        """
        aliases = [k for k in self.key.split("|") if k.startswith("-")]
        if len(aliases) > 0:
            return aliases[0]

    def canonical_dir(self, ignore_args = False):
        return os.path.dirname(self.name)

    def canonical_basename(self, ignore_args = False):
        return os.path.basename(self.canonical_filename(ignore_args))

    def canonical_filename(self, ignore_args = False):
        fn = os.path.splitext(self.key.split("|")[0])[0]

        if self.args.has_key('canonical-name') and not ignore_args:
            parent_dir = os.path.dirname(fn)
            return os.path.join(parent_dir, self.args['canonical-name'])
        elif self.args.has_key('postfix') and not ignore_args:
            return "%s%s%s" % (fn, self.ext, self.args['postfix'])
        elif self.alias():
            return "%s%s%s" % (fn, self.alias(), self.ext)
        else:
            return "%s%s" % (fn, self.ext)

    def long_canonical_filename(self):
        if not "|" in self.key:
            return self.key.replace("|", "-")
        else:
            return "%s%s" % (self.key.replace("|", "-"), self.ext)

    def websafe_key(self):
        return self.long_canonical_filename().replace("/", "--")

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

    def abs_filepath(self):
        return os.path.abspath(self.filepath())

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
            return self.breadcrumbs()[-1].replace("-"," ").title()
        else:
            return os.path.splitext(self.canonical_basename())[0].replace("-"," ").title()

    def unique_key(self):
        return "%s:%s:%s" % (self.batch_id, self.document_key, self.key)

    def web_safe_document_key(self):
        # TODO this might not be unique
        return self.document_key.replace("/","-").replace("|", "-")

    def url(self):
        # TODO test for final
        return "/%s" % self.canonical_filename()

    def hyperlink(self, link_text = None):
        # TODO test for final
        if not link_text:
            link_text = self.canonical_basename()

        return """<a href="%s">%s</a>""" % (self.url(), link_text)

    def iframe(self, link_text = None, width = "600px", height = "300px"):
        # TODO test for final
        args = {
                'url' : self.url(),
                'hyperlink' : self.hyperlink(link_text),
                'width' : width,
                'height' : height
        }

        return """
<iframe src="%(url)s" width="%(width)s" height="%(height)s" style="border: thin solid gray;">
%(hyperlink)s
</iframe>
        """ % args

    def img(self):
        # TODO test for final
        return """<img src="/%s" alt="Image generated by dexy %s" />""" % (self.canonical_filename(), self.key)

    def has_sections(self):
        return (self.data_dict.keys() != ['1'])

    def relative_path_to_input(self, input_artifact):
        my_dir = os.path.dirname(self.name)
        input_dir = os.path.dirname(input_artifact.name)
        if my_dir == input_dir:
            relpath = ""
        else:
            relpath = os.path.relpath(input_dir, my_dir)
        return relpath

    def relative_key_for_input(self, input_artifact):
        relpath = self.relative_path_to_input(input_artifact)
        return os.path.join(relpath, os.path.basename(input_artifact.key))

    def convert_numbered_dict_to_ordered_dict(self, numbered_dict):
        ordered_dict = OrderedDict()
        for x in sorted(numbered_dict.keys()):
            k = x.split(":", 1)[1]
            ordered_dict[k] = numbered_dict[x]
        return ordered_dict

    def convert_data_dict_to_numbered_dict(self):
        if len(self.data_dict) >= self.MAX_DATA_DICT_LENGTH:
            exception_msg = """Your data dict has %s items, which is greater than the arbitrary limit of %s items.
            You can increase this limit by changing MAX_DATA_DICT_DECIMALS."""
            raise Exception(exception_msg % (len(self.data_dict), self.MAX_DATA_DICT_LENGTH))

        data_dict = {}
        i = -1
        for k, v in self.data_dict.iteritems():
            i += 1
            fmt = "%%0%sd:%%s" % self.MAX_DATA_DICT_DECIMALS
            data_dict[fmt % (i, k)] = v
        return data_dict

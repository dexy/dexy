try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from dexy.logger import log
from dexy.version import VERSION
import hashlib
import inspect
import json
import os
import re
import shutil
import sys
import time
import uuid

### @export "setup"
class Artifact(object):
    """
    This is the Artifact class ... just testing docstrings... 
    """
    @classmethod
    def setup(klass, doc, key, handler, previous_artifact = None):
        art = klass()
        art.doc = doc
        art.key = key
        art.data_dict = OrderedDict()
        art.dirty = False
        art.auto_write_artifact = True
        art.additional_inputs = {}
        art.artifacts_dir = art.doc.controller.artifacts_dir
        if previous_artifact:
            art.input_ext = previous_artifact.ext
            art.input_data_dict = previous_artifact.data_dict
            art.input_artifacts = previous_artifact.input_artifacts
            art.additional_inputs = previous_artifact.additional_inputs
            art.previous_artifact_filename = previous_artifact.filename()
        art.dexy_version = VERSION
        if handler:
            art.handler_source = inspect.getsource(handler.__class__)
            art.handler_version = handler.version()
        return art

### @export "set-hashstring"
    def set_hashstring(self):
        if self.dirty:
            self.dirty_string = time.gmtime()

        hash_dict = self.__dict__.copy()
        hash_dict['args'] = self.doc.args

        # Remove any items which should not be included in hash calculations.
        del hash_dict['doc']

        self.hashstring = hashlib.md5(hash_dict.__str__()).hexdigest()

### @export "command-line-args"
    def command_line_args(self):
        """
        Allow specifying command line arguments which are passed to the filter
        with the given key. Note that this does not currently allow
        differentiating between 2 calls to the same filter in a single document.
        """
        if self.doc.args.has_key('args'):
            args = self.doc.args['args']
            last_key = self.key.rpartition("|")[-1]
            if args.has_key(last_key):
                return args[last_key]

### @export "filename"
    def filename(self, rel_to_artifacts_dir = True):
        filename = "%s%s" % (self.hashstring, self.ext)
        if rel_to_artifacts_dir:
            filename = os.path.join(self.artifacts_dir, filename)
        return filename

### @export "dj"
    def dj_filename(self):
        if not self.hashstring:
            raise Exception("hashstring is none")
        return os.path.join(self.artifacts_dir, "%s.dexy.json" % self.hashstring)

    def dj_file_exists(self):
        return os.path.isfile(self.dj_filename())

    def persist_dict(self):
        self.data = self.output_text() 
        self.fn = self.filename(False)

        # Whitelist data to be serialized.
        attrs = ['data_dict', 'data', 'fn', 'input_artifacts',
                 'additional_inputs', 'stdout', 'short_output_name',
                 'output_name']

        persist_dict = {}
        for a in attrs:
            if hasattr(self, a):
                at = getattr(self, a)
                if inspect.ismethod(at):
                    persist_dict[a.replace('_','-')] = at()
                else:
                    persist_dict[a] = at
        return persist_dict

    def write_dj(self):
        dj_file = open(self.dj_filename(), "w")
        try:
            json.dump(self.persist_dict(), dj_file)
        except UnicodeDecodeError as e:
            # TODO re-raise this error??
            log.warn("Unable to persist json dict")
            log.warn(e)

    def load_dj(self):
        dj_file = open(self.dj_filename(), "r")
        def load_ordered_dict(x):
            return OrderedDict(x)

        if sys.version_info < (2, 7):
            for k, v in json.load(dj_file).items():
                # This will return elements in the wrong order..
                setattr(self, k, v)
        else:
            for k, v in json.load(dj_file, object_pairs_hook=load_ordered_dict).items():
                setattr(self, k, v)


### @export "input-text"
    def input_text(self):
        text = ""
        for k, v in self.input_data_dict.items():
            text += v
        return text

### @export "output-text"
    def output_text(self):
        text = ""
        for k, v in self.data_dict.items():
            text += v
        return text

### @export "write-artifact"
    def write_artifact(self):
        artifact_file = open(self.filename(), "w")
        for k, v in self.data_dict.items():
            artifact_file.write(v)
        artifact_file.close

### @export "generate"
    def generate(self):
        self.write_dj()
        if self.auto_write_artifact:
            self.write_artifact()

### @export "work-files"
    def work_filename(self, rel_to_artifacts_dir = True):
        filename = "%s.work%s" % (self.hashstring, self.input_ext)
        if rel_to_artifacts_dir:
            filename = os.path.join(self.artifacts_dir, filename)
        return filename

    def generate_workfile(self):
        work_file = open(self.work_filename(), "w")
        work_file.write(self.input_text())
        work_file.close()

### @export "temp-files"
    def temp_filename(self, ext, rel_to_artifacts_dir = True):
        temp_filename = "%s.work%s" % (self.hashstring, ext)
        if rel_to_artifacts_dir:
            temp_filename = os.path.join(self.artifacts_dir, temp_filename)
        return temp_filename

    def tempfile(self, ext, rel_to_artifacts_dir = True):
        open(self.temp_filename(ext, rel_to_artifacts_dir), "w")

    def temp_dir(self):
        return os.path.join(self.artifacts_dir, self.hashstring)

    def create_temp_dir(self):
        shutil.rmtree(self.temp_dir(), ignore_errors=True)
        os.mkdir(self.temp_dir())

### @export "create-input-file"
    def create_input_file(self, key, ext, rel_to_artifacts_dir = False):
        print "the create_input_file method is deprecated, please use the FilenameHandler instead in", self.key
        if key in self.additional_inputs.keys():
            filename = self.additional_inputs[key]
            log.debug("existing key %s in artifact %s links to file %s" % (key, self.key, filename))
        else:
            filename = "%s.%s" % (uuid.uuid4(), ext)
            self.additional_inputs[key] = filename
            log.debug("added key %s to artifact %s ; links to file %s" % (key, self.key, filename))

        full_filename = os.path.join(self.artifacts_dir, filename)

        if rel_to_artifacts_dir:
            return full_filename
        else:
            return filename

### @export "load-input-artifacts"
    def load_input_artifacts(self):
        # TODO for now this just loads data_dict into a hash... should be a pickled artifact object?
        self.input_artifacts_dict = {}
        for k, v in self.input_artifacts.items():
            self.input_artifacts_dict[k] = json.load(open(v, "r"))

### @export "stdout-name"
    def stdout_name(self, rel_to_path):
        """A canonical filename for any stdout text generated."""
        rel_path = os.path.relpath(self.key.replace("|", "-"), rel_to_path)
        return "%s-stdout.txt" % (rel_path)

    def write_stdout_file(self):
        f = open(self.stdout_name(self.artifacts_dir), "w")
        f.write(self.stdout)
        f.close()

### @export "stderr-name"
    def stderr_name(self, rel_to_path):
        """A canonical filename for any stderr text generated."""
        rel_path = os.path.relpath(self.key.replace("|", "-"), rel_to_path)
        return "%s-stderr.txt" % (rel_path)

### @export "output-name"
    def output_name(self, use_short_format = False):
        """A canonical filename derived by taking input filename and replacing extension with
        final extension."""
        if use_short_format or not re.search("\|", self.key):
            name = "%s%s" % (os.path.splitext(self.doc.name)[0], self.ext)
        else:
            name = "%s%s" % (self.key.replace("|", "-"), self.ext)
        return os.path.relpath(name, ".")

    def short_output_name(self):
        return self.output_name(True)

### @export "write-cache-output-file"
    def write_cache_output_file(self, cache_dir, use_short_format):
        output_filename = os.path.join(cache_dir, self.output_name(use_short_format))
        dirname = os.path.dirname(output_filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        shutil.copyfile(self.filename(), output_filename)


from collections import OrderedDict
import hashlib
import inspect
import os
import shutil
import simplejson as json
import time
import uuid

### @export "setup"
class Artifact(object):
    @classmethod
    def setup(klass, doc, key, handler, previous_artifact = None):
        art = klass()
        art.doc = doc
        art.key = key
        art.data_dict = OrderedDict()
        art.dirty = False
        art.auto_write_artifact = True
        art.additional_inputs = {}
        if previous_artifact:
            art.input_ext = previous_artifact.ext
            art.input_data_dict = previous_artifact.data_dict
            art.input_artifacts = previous_artifact.input_artifacts
            art.additional_inputs = previous_artifact.additional_inputs
            art.previous_artifact_filename = previous_artifact.filename()
        art.artifact_version = 1 # Change this if non-backwards-compatible change.
        if handler:
            art.handler_source = inspect.getsource(handler.__class__)
        return art

### @export "set-hashstring"
    def set_hashstring(self):
        if self.dirty:
            self.dirty_string = time.gmtime()

        hash_dict = self.__dict__.copy()

        # Remove any items which should not be included in hash calculations.
        del hash_dict['doc']

        hash_json = json.dumps(hash_dict)
        self.hashstring = hashlib.md5(hash_json).hexdigest()

### @export "filename"
    def filename(self, rel_to_artifacts_dir = True):
        filename = "%s%s" % (self.hashstring, self.ext)
        if rel_to_artifacts_dir:
            filename = os.path.join('artifacts', filename)
        return filename

### @export "dj"
    def dj_filename(self):
        if not self.hashstring:
            raise Exception("hashstring is none")
        return os.path.join('artifacts', "%s.dexy.json" % self.hashstring)

    def dj_file_exists(self):
        return os.path.isfile(self.dj_filename())

    def persist_dict(self):
        self.data = self.output_text() 
        self.fn = self.filename(False)

        # Whitelist data to be serialized.
        attrs = ['data_dict', 'data', 'fn', 'input_artifacts', 'additional_inputs', 'stdout']

        persist_dict = {}
        for a in attrs:
            if hasattr(self, a):
                persist_dict[a] = getattr(self, a)
        return persist_dict

    def write_dj(self):
        dj_file = open(self.dj_filename(), "w")
        json.dump(self.persist_dict(), dj_file)

    def load_dj(self):
        dj_file = open(self.dj_filename(), "r")
        for k, v in json.load(dj_file).items():
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
            filename = os.path.join('artifacts', filename)
        return filename

    def generate_workfile(self):
        work_file = open(self.work_filename(), "w")
        work_file.write(self.input_text())
        work_file.close()

### @export "temp-files"
    def temp_filename(self, ext, rel_to_artifacts_dir = True):
        temp_filename = "%s.work%s" % (self.hashstring, ext)
        if rel_to_artifacts_dir:
            temp_filename = os.path.join('artifacts', temp_filename)
        return temp_filename

    def tempfile(self, ext, rel_to_artifacts_dir = True):
        open(self.temp_filename(ext, rel_to_artifacts_dir), "w")

### @export "create-input-file"
    def create_input_file(self, key, ext, rel_to_artifacts_dir = True):
        if key in self.additional_inputs.keys():
            raise Exception("already have a key %s" % key)
        
        filename = "%s.%s" % (uuid.uuid4(), ext)
        full_filename = os.path.join("artifacts", filename)
        self.additional_inputs[key] = full_filename

        print "added key", key, "to artifact", self.key, "links to file", full_filename

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

### @export "output-name"
    def output_name(self, rel_to_path):
        """A canonical filename derived by taking input filename and replacing extension with
        final extension."""
        rel_path = os.path.relpath(self.key.replace("|", "-"), rel_to_path)
        return "%s%s" % (rel_path, self.ext)

### @export "stdout-name"
    def stdout_name(self, rel_to_path):
        """A canonical filename for any stdout text generated."""
        rel_path = os.path.relpath(self.key.replace("|", "-"), rel_to_path)
        return "%s-stdout.txt" % (rel_path)

    def write_stdout_file(self):
        f = open(self.stdout_name("artifacts"), "w")

### @export "stderr-name"
    def stderr_name(self, rel_to_path):
        """A canonical filename for any stderr text generated."""
        rel_path = os.path.relpath(self.key.replace("|", "-"), rel_to_path)
        return "%s-stderr.txt" % (rel_path)

### @export "write-cache-output-file"
    def write_cache_output_file(self):
        dirname = os.path.dirname(os.path.join('cache', self.doc.name))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        output_filename = os.path.join('cache', self.doc.name)
        shutil.copyfile(self.filename(), output_filename)


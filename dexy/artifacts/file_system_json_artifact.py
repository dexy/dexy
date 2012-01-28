from dexy.artifact import Artifact
from ordereddict import OrderedDict
import codecs
import json
import os

class FileSystemJsonArtifact(Artifact):
    """Artifact which persists data by writing to the file system and using
    JSON for serializing metadata (default type of Artifact)"""

    # Metadata
    def meta_filename(self):
        return "%s-meta.json" % (self.hashstring)

    def meta_filepath(self):
        return os.path.join(self.artifacts_dir, self.meta_filename())

    def write_dict_to_file(self, data_dict, filepath):
        with open(filepath, "wb") as f:
            json.dump(data_dict, f)

    def read_dict_from_file(self, filepath):
        with open(filepath, "rb") as f:
            return json.load(f)

    def save_meta(self):
        m = {}
        attrs_to_persist = set(self.META_ATTRS + self.HASH_WHITELIST) - set(['input_data_dict', 'inputs'])
        for a in attrs_to_persist:
            if hasattr(self, a):
                v = getattr(self, a)
                m[a] = v

        m['inputs'] = self.input_hashes()

        self.write_dict_to_file(m, self.meta_filepath())

    def load_meta(self):
        m = self.read_dict_from_file(self.meta_filepath())

        self._inputs = dict((k, self.__class__.retrieve(h)) for (k, h) in m.pop('inputs').iteritems())

        for k, v in m.iteritems():
            setattr(self, k, v)

        # We only store filter name, not filter class, need to retrieve class from name
        if hasattr(self, "filter_name") and not hasattr(self, "filter_class"):
            self.filter_class = [k for n,k in self.FILTERS.iteritems() if k.__name__ == self.filter_name][0]

    # Input
    def load_input(self):
        """Load input data into memory, if applicable."""
        if self.is_loaded():
            return

        if self.binary_input:
            #not loading non-binary input
            pass
        elif self.initial:
            #initial artifact has no input
            pass
        elif self.additional:
            #additional artifact has no input
            pass
        elif len(self.input_data_dict) > 0:
            #we already have input data in memory
            pass
        elif not hasattr(self, 'previous_cached_output_filepath'):
            #no previous cached output, can't load
            pass
        else:
            with open(self.previous_cached_output_filepath, "rb") as f:
                self.input_data_dict = self.convert_numbered_dict_to_ordered_dict(json.load(f))

    # Output
    def cached_output_filename(self):
        return "%s-output.json" % (self.hashstring)

    def cached_output_filepath(self):
        return os.path.join(self.artifacts_dir, self.cached_output_filename())

    def is_output_cached(self):
        # TODO add checksums to verify data hasn't changed
        if self.binary_output:
            return self.is_canonical_output_cached()
        else:
            return self.is_json_output_cached() and self.is_canonical_output_cached()

    def is_json_output_cached(self):
        fp = self.cached_output_filepath()
        return os.path.isfile(fp) and (os.path.getsize(fp) > 0)

    def is_canonical_output_cached(self):
        fp = self.filepath()
        return os.path.isfile(fp) and (os.path.getsize(fp) > 0)

    def save_output(self):
        if not self.is_complete():
            raise Exception("should not be calling save_output unless artifact is complete")

        if not self.binary_output:
            if not self.data_dict or len(self.data_dict) == 0:
                # Our filter has written directly to an output file
                # We need to load this into memory first
                self.data_dict = OrderedDict()
                with codecs.open(self.filepath(), 'r', encoding="utf-8") as f:
                    data = f.read()
                self.data_dict['1'] = data
            else:
                # Write the canonical output file.
                with codecs.open(self.filepath(), 'w', encoding="utf-8") as f:
                    f.write(self.output_text())

            # Write the JSON output file.
            output_dict = self.convert_data_dict_to_numbered_dict()
            self.write_dict_to_file(output_dict, self.cached_output_filepath())

    def load_output(self):
        if not self.is_complete():
            raise Exception("should not be calling load_output unless artifact is complete")

        if not self.binary_output:
            output_dict = self.read_dict_from_file(self.cached_output_filepath())
            self.data_dict = self.convert_numbered_dict_to_ordered_dict(output_dict)


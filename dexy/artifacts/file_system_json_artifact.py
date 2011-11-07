from dexy.artifact import Artifact
from ordereddict import OrderedDict
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

    def save_meta(self):
        m = {}
        attrs_to_persist = set(self.META_ATTRS + self.HASH_WHITELIST) - set(['input_data_dict', 'inputs'])
        for a in attrs_to_persist:
            if hasattr(self, a):
                v = getattr(self, a)
                m[a] = v

        m['inputs'] = self.input_hashes()

        f = open(self.meta_filepath(), "w")
        try:
            json.dump(m, f)
        except UnicodeDecodeError as e:
            print e
            print m
            raise Exception("Binary data present in %s" % self.key)
        f.close()

    def load_meta(self):
        f = open(self.meta_filepath(), "r")
        m = json.load(f)
        f.close()

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
            f = open(self.previous_cached_output_filepath, "r")
            data_dict = json.load(f)
            f.close()

            self.input_data_dict = OrderedDict() # maybe unnecessary
            for x in sorted(data_dict.keys()):
                k = x.split(":", 1)[1]
                self.input_data_dict[k] = data_dict[x]

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
                with open(self.filepath(), 'r') as f:
                    data = f.read()
                self.data_dict['1'] = data

            # need to preserve ordering but we can't serialize OrderedDict
            # using JSON, so add sortable numbers to keys to preserve order
            data_dict = {}
            MAX = 10000
            if len(self.data_dict) >= MAX:
                raise Exception("""There is an arbitrary limit of %s dict items,
                               you can increase this if you need to.""" % MAX)
            i = -1
            for k, v in self.data_dict.iteritems():
                i += 1
                data_dict["%04d:%s" % (i, k)] = v

            # Write the JSON file.
            f = open(self.cached_output_filepath(), "w")
            try:
                json.dump(data_dict, f)
            except UnicodeDecodeError as e:
                print e
                print self.binary_output
                raise Exception(self.key)

            f.close()

            # Write the canonical file.
            f = open(self.filepath(), 'w')
            f.write(self.output_text())
            f.close()

    def load_output(self):
        if not self.is_complete():
            raise Exception("should not be calling load_output unless artifact is complete")

        if not self.binary_output:
            f = open(self.cached_output_filepath(), "r")
            data_dict = json.load(f)
            f.close()

            self.data_dict = OrderedDict() # maybe unnecessary
            for x in sorted(data_dict.keys()):
                k = x.split(":", 1)[1]
                self.data_dict[k] = data_dict[x]


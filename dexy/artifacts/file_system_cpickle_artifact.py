from ordereddict import OrderedDict
import cPickle as pickle
import dexy.artifacts.file_system_json_artifact as fsa
import os

class FileSystemcPickleArtifact(fsa.FileSystemJsonArtifact):
    """Artifact which persists data by writing to the file system and using
    cjson for serializing metadata"""

    def meta_filename(self):
        return "%s-meta.pickle" % (self.hashstring)

    def cached_output_filename(self):
        return "%s-output.pickle" % (self.hashstring)

    def save_meta(self):
        m = {}
        attrs_to_persist = set(self.META_ATTRS + self.HASH_WHITELIST) - set(['input_data_dict', 'inputs'])
        for a in attrs_to_persist:
            if hasattr(self, a):
                v = getattr(self, a)
                m[a] = v

        m['inputs'] = {}
        for k, a in self.inputs().iteritems():
            a.save()
            m['inputs'][k] = a.hashstring

        with open(self.meta_filepath(), "w") as f:
            pickle.dump(m, f)

    def load_meta(self):
        with open(self.meta_filepath(), "r") as f:
            m = pickle.load(f)

        self._inputs = dict((k, self.__class__.retrieve(h)) for (k, h) in m.pop('inputs').iteritems())

        for k, v in m.iteritems():
            setattr(self, k, v)

        # We only store filter name, not filter class, need to retrieve class from name
        if hasattr(self, "filter_name") and not hasattr(self, "filter_class"):
            self.filter_class = [k for n,k in self.FILTERS.iteritems() if k.__name__ == self.filter_name][0]

    def save_output(self):
        if not self.is_complete():
            raise Exception("should not be calling save_output unless artifact is complete")

        if not self.binary_output:
            if not self.data_dict or len(self.data_dict) == 0:
                # Our filter has written directly to an output file
                # We need to load this into memory first
                self.data_dict = OrderedDict()
                f = open(self.filepath(), 'r')
                data = f.read()
                f.close()
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

            # Write the data file.
            with open(self.cached_output_filepath(), "w") as f:
                pickle.dump(data_dict, f)

            # Write the canonical file.
            if not os.path.exists(self.filepath()):
                with open(self.filepath(), 'w') as f:
                    f.write(self.output_text())

    def load_output(self):
        if not self.is_complete():
            raise Exception("should not be calling load_output unless artifact is complete")

        if not self.binary_output:
            f = open(self.cached_output_filepath(), "r")
            data_dict = pickle.load(f)
            f.close()

            self.data_dict = OrderedDict() # maybe unnecessary
            for x in sorted(data_dict.keys()):
                k = x.split(":", 1)[1]
                self.data_dict[k] = data_dict[x]


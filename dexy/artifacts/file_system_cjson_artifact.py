import dexy.artifacts.file_system_json_artifact as fsa
import cjson

class FileSystemCjsonArtifact(fsa.FileSystemJsonArtifact):
    """Artifact which persists data by writing to the file system and using
    cjson for serializing metadata"""

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
           s = cjson.encode(m)
           f.write(s)

    def load_meta(self):
        with open(self.meta_filepath(), "r") as f:
            m = cjson.decode(f.read())

        self._inputs = dict((k, self.__class__.retrieve(h)) for (k, h) in m.pop('inputs').iteritems())

        for k, v in m.iteritems():
            setattr(self, k, v)

        # We only store filter name, not filter class, need to retrieve class from name
        if hasattr(self, "filter_name") and not hasattr(self, "filter_class"):
            self.filter_class = [k for n,k in self.FILTERS.iteritems() if k.__name__ == self.filter_name][0]

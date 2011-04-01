from dexy.artifact import Artifact
from ordereddict import OrderedDict
import json
import os

class FileSystemJsonArtifact(Artifact):
    """Artifact which persists data by writing to the file system (default type
    of Artifact)"""

    def data_filename(self):
        return "%s-data.json" % (self.hashstring)

    def data_filepath(self):
        return os.path.join(self.artifacts_dir, self.data_filename())

    def meta_filename(self):
        return "%s-meta.json" % (self.hashstring)

    def meta_filepath(self):
        return os.path.join(self.artifacts_dir, self.meta_filename())

    def save(self):
        try:
            json.dumps(self.data_dict)
        except UnicodeDecodeError:
            if not self.binary:
                raise Exception("should be marked binary", self.key)
            self.binary = True

        if not os.path.isfile(self.filepath()):
            f = open(self.filepath(), "w")
            f.write(self.output_text())
            f.close()

        if not self.binary:
            # Make keys we can sort by to retrieve in correct order.
            data_dict = {}
            if len(self.data_dict) > 9999:
                raise Exception("make n > 4")
            i = -1
            for k, v in self.data_dict.items():
                i += 1
                # TODO maybe don't hard code 4 places, calculate from len of data dict
                data_dict["%04d:%s" % (i, k)] = v

            f = open(self.data_filepath(), "w")
            json.dump(data_dict, f)
            f.close()

        # Metadata is the same whether binary or not
        metadata = {}
        for a in self.META_ATTRS:
            if hasattr(self, a):
                v = getattr(self, a)
                metadata[a] = v

        iak = {}
        for k, v in self.input_artifacts.items():
            iak[k] = v.hashstring
        metadata['input-artifacts'] = iak

        ia = {}
        for k, a in self.additional_inputs.items():
            if len(a.data_dict) == 0:
                if os.path.isfile(a.filepath()):
                    f = open(a.filepath(), "r")
                    a.data_dict['1'] = f.read()
                    f.close()
                    a.save()
            ia[k] = a.hashstring
        metadata['additional-inputs'] = ia

        f = open(self.meta_filepath(), "w")
        json.dump(metadata, f)
        f.close()

    def is_cached(self):
        mfexists = os.path.isfile(self.meta_filepath())

        if os.path.isfile(self.data_filepath()):
            dfexists = True
            df = self.data_filepath()
        elif mfexists:
            # TODO this is messy - would be easier to just store binary data in
            # standard location so don't need extension until later

            # need to determine file extension
            f = open(self.meta_filepath(), "r")
            m = json.load(f)
            f.close()
            self.ext = m['ext']

            if os.path.isfile(self.filepath()):
                dfexists = True
                df = self.filepath()
            else:
                dfexists = False
        else:
            dfexists = False

        if dfexists and not mfexists:
            locs = (df, self.meta_filepath())
            exception_text = "have a data file %s and no meta file %s!" % locs
            raise Exception(exception_text)
        if mfexists and not dfexists:
            locs = (self.meta_filepath())
            exception_text = "have a meta file %s and no data file!" % locs
            raise Exception(exception_text)
        return dfexists and mfexists

    def load(self):
        # Load artifact from the cache.
        if not self.is_cached():
            raise Exception("trying to load an artifact which isn't cached")

        f = open(self.meta_filepath(), "r")
        m = json.load(f)
        f.close()

        # Remove input-artifacts from metadata and process.
        self.input_artifacts = {}
        for k, h in m.pop('input-artifacts').items():
            a = self.__class__(k) # create a new artifact
            a.hashstring = h
            a.artifacts_dir = self.artifacts_dir # needed to load
            if not a.is_cached():
                raise Exception("input artifact not cached!")
            if not a.is_loaded():
                a.load()
            self.input_artifacts[k] = a

        # Remove additional-inputs from metadata and process.
        self.additional_inputs = {}
        for k, h in m.pop('additional-inputs').items():
            a = self.__class__(k) # create a new artifact
            a.hashstring = h
            a.artifacts_dir = self.artifacts_dir # needed to load
            if not a.is_cached():
                raise Exception("additional input not cached!")
            if not a.is_loaded():
                a.load()
            self.additional_inputs[k] = a

        for k, v in m.items():
            setattr(self, k, v)

        if not self.binary:
            f = open(self.data_filepath(), "r")
            data_dict = json.load(f)
            f.close()

            self.data_dict = OrderedDict()
            for x in sorted(data_dict.keys()):
                k = x.split(":", 1)[1]
                self.data_dict[k] = data_dict[x]


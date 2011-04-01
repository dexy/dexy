from dexy.artifact import Artifact
from ordereddict import OrderedDict
import mimetypes
import os
import riak

class RiakArtifact(Artifact):
    """Artifact which persists by storing data in Riak"""

    @classmethod
    def purge(klass):
        # TODO Write a real purge method.
        print "purging..."

    def init_bucket(self):
        if not hasattr(self, 'client'):
            self.client = riak.RiakClient()
        if not hasattr(self, 'bucket'):
            self.bucket = self.client.bucket('dexy-artifacts')

    def fetch(self):
        self.init_bucket()
        self.riak_object = self.bucket.get(self.hashstring)
        self.meta_object = self.bucket.get(self.metakey())

    def is_cached(self):
        if not hasattr(self, 'riak_object'):
            self.fetch()

        if self.riak_object.exists() and not self.meta_object.exists():
            raise Exception("have a riak object with no meta object!")
        if self.meta_object.exists() and not self.riak_object.exists():
            raise Exception("have a meta object with no riak object!")
        return self.riak_object.exists() and self.meta_object.exists()

    def metakey(self):
        return "%s-meta" % self.hashstring

    def load(self):
        if not hasattr(self, 'riak_object'):
            self.fetch()

        if self.is_loaded():
            raise Exception("trying to load an artifact that is already loaded")

        m = self.meta_object.get_data()

        # Remove input-artifacts from metadata and process.
        self.input_artifacts = {}
        for k, h in m.pop('input-artifacts').items():
            a = self.__class__() # create a new artifact
            a.hashstring = h
            if not a.is_cached():
                raise Exception("input artifact not cached!")
            if not a.is_loaded():
                a.load()
            self.input_artifacts[k] = a

        # Now load remaining metadata
        for k, v in m.items():
           setattr(self, k, v)

        if self.binary:
            binary_data = self.riak_object.get_data()
            self.data_dict = OrderedDict()
            self.data_dict['1'] = binary_data

            if not os.path.isfile(self.filepath()):
                f = open(self.filepath(), "wb")
                f.write(binary_data)
                f.close()
        else:
            data_dict = self.riak_object.get_data()
            self.data_dict = OrderedDict()
            for x in sorted(data_dict.keys()):
                k = x.split(":", 1)[1]
                self.data_dict[k] = data_dict[x]

            if not os.path.isfile(self.filepath()):
                f = open(self.filepath(), "w")
                f.write(self.output_text())
                f.close()

    def save(self):
        self.init_bucket()
        if self.binary:
            # Assume binary data has been saved in location given by filepath()
            binary_data = open(self.filepath(), "rb").read()
            mimetype, encoding = mimetypes.guess_type(self.filepath())
            if not mimetype:
                mimetype = 'application/octet-stream' # Riak's own default
            self.riak_object = self.bucket.new_binary(
                self.hashstring,
                binary_data,
                mimetype
            )
        else:
            # Make sure data has been written to filepath()
            # not all filters do this
            if not os.path.isfile(self.filepath()):
                f = open(self.filepath(), "w")
                f.write(self.output_text())
                f.close()

            data_dict = {}
            if len(self.data_dict) > 9999:
                raise Exception("make n > 4")
            i = -1
            for k, v in self.data_dict.items():
                i += 1
                # TODO maybe don't hard code 4 places, calculate from len of data dict
                data_dict["%04d:%s" % (i, k)] = v

            self.riak_object = self.bucket.new(
                self.hashstring,
                data_dict
            )

        metadata = {}
        for a in self.META_ATTRS:
            if hasattr(self, a):
                v = getattr(self, a)
                metadata[a] = v

        iak = {}
        for k, v in self.input_artifacts.items():
            iak[k] = v.hashstring
        metadata['input-artifacts'] = iak

        self.meta_object = self.bucket.new(
            self.metakey(),
            metadata
        )

        self.riak_object.store()
        self.meta_object.store()
        if not self.is_cached():
            raise Exception("should be cached after saving!")

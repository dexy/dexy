from dexy.plugin import PluginMeta
from dexy.wrapper import Wrapper
import dexy.storage
import os
import shutil

class Data:
    __metaclass__ = PluginMeta

    ALIASES = []
    DEFAULT_STORAGE_TYPE = 'generic'

    @classmethod
    def is_active(klass):
        return True

    @classmethod
    def retrieve(klass, key, ext, data_type, hashstring, storage_type, **kwargs):
        """
        Method to retrieve a Data object based on info stored in database.

        Optional kwags are passed to a RunParams instance.
        """
        wrapper = Wrapper(**kwargs)
        data_class = klass.aliases[data_type]
        return data_class(key, ext, hashstring, wrapper, storage_type)

    def __init__(self, key, ext, hashstring, wrapper, storage_type=None):
        self.key = key
        self.ext = ext
        self.hashstring = hashstring
        self.wrapper = wrapper

        self.calculate_name()

        self.storage_type = storage_type or self.DEFAULT_STORAGE_TYPE
        storage_class = dexy.storage.Storage.aliases[self.storage_type]
        self.storage = storage_class(hashstring, ext, self.wrapper)

        self._data = None

        # Allow doing custom setup stuff in subclasses.
        self.setup()

    def setup(self):
        pass

    def calculate_name(self):
        name_without_ext = os.path.splitext(self.key)[0]
        self.name = "%s%s" % (name_without_ext, self.ext)

    def parent_dir(self):
        return os.path.dirname(self.name)

    def long_name(self):
        return "%s%s" % (self.key.replace("|", "-"), self.ext)

    def web_safe_document_key(self):
        return self.long_name().replace("/", "--")

    def relative_refs(self, relative_to_file):
        doc_dir = os.path.dirname(relative_to_file)
        return [
                os.path.relpath(self.key, doc_dir),
                os.path.relpath(self.long_name(), doc_dir),
                "/%s" % self.key,
                "/%s" % self.long_name()
        ]

class GenericData(Data):
    ALIASES = ['generic']
    DEFAULT_STORAGE_TYPE = 'generic'

    """
    Data in a single lump, which may be binary or text-based.
    """
    def save(self):
        self.storage.write_data(self._data)

    def set_data(self, data):
        """
        Set data to the passed argument and persist data to disk.
        """
        self._data = data
        self.save()

    def load_data(self):
        self._data = self.storage.read_data()

    def has_data(self):
        return self._data or self.storage.data_file_exists()

    def is_cached(self):
        return self.storage.data_file_exists()

    def data(self):
        if not self._data:
            self.load_data()
        return self._data

    def as_text(self):
        return self.data()

    def as_sectioned(self):
        return {'1' : self.data()}

    def copy_from_file(self, filename):
        shutil.copyfile(filename, self.storage.data_file())

    def clear_data(self):
        self._data = None

    def output_to_file(self, filepath):
        """
        Write canonical output to a file. Parent directory must exist already.
        """
        self.storage.write_data(self._data, filepath)

class SectionedData(GenericData):
    ALIASES = ['sectioned']
    DEFAULT_STORAGE_TYPE = 'jsonordered'

    def as_text(self):
        return "\n".join(v for v in self.data().values())

    def as_sectioned(self):
        return self.data()

    def output_to_file(self, filepath):
        """
        Write canonical output to a file.
        """
        with open(filepath, "wb") as f:
            f.write(self.as_text())

class KeyValueData(GenericData):
    ALIASES  = ['keyvalue']
    DEFAULT_STORAGE_TYPE = 'json'

    def setup(self):
        self._data = {}

    def as_text(self):
        text = []
        for k, v in self._data.iteritems():
            text.append("%s: %s" % (k, v))
        return "\n".join(text)

    def append(self, key, value):
        self._data[key] = value

    def keys(self):
        return self._data.keys()

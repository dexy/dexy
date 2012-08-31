from dexy.plugin import PluginMeta
import dexy.storage
import shutil

class Data:
    ALIASES = []
    __metaclass__ = PluginMeta
    @classmethod
    def is_active(klass):
        return True

class GenericData(Data):
    ALIASES = ['generic']
    DEFAULT_STORAGE_TYPE = 'generic'

    """
    Data in a single lump, which may be binary or text-based.
    """
    def __init__(self, hashstring, ext, runner, storage_type=None):
        if not storage_type:
            storage_type = self.DEFAULT_STORAGE_TYPE

        if not runner.__class__.__name__ == "Runner":
            raise Exception

        self.hashstring = hashstring
        self.ext = ext
        self.runner = runner

        storage_class = dexy.storage.Storage.aliases[storage_type]
        self.storage = storage_class(hashstring, ext, self.runner)

        self._data = None

        # Allow doing custom setup stuff in subclasses.
        self.setup()

    def setup(self):
        pass

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

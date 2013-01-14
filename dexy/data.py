from dexy.common import OrderedDict
from dexy.plugin import PluginMeta
import chardet
import dexy.storage
import dexy.utils
import dexy.wrapper
import os
import posixpath
import shutil

class Data:
    __metaclass__ = PluginMeta

    ALIASES = []
    DEFAULT_STORAGE_TYPE = 'generic'

    @classmethod
    def is_active(klass):
        return True

    @classmethod
    def retrieve(klass, data_type, key, ext, name, hashstring, args, wrapper, storage_type):
        """
        Method to retrieve a Data object based on info stored in database.

        Optional kwags are passed to a RunParams instance.
        """
        data_class = klass.aliases[data_type]
        return data_class(key, ext, name, hashstring, args, wrapper, storage_type)

    @classmethod
    def storage_class_alias(klass, file_ext):
        return klass.DEFAULT_STORAGE_TYPE

    def __repr__(self):
        return "Data('%s')" % (self.key)

    def __unicode__(self):
        if isinstance(self.data(), unicode):
            return self.data()
        elif not self.data():
            return unicode(None)
        else:
            if self.wrapper.encoding == 'chardet':
                encoding = chardet.detect(self.data())['encoding']
                if not encoding:
                    return self.data().decode("utf-8")
                else:
                    return self.data().decode(encoding)
            else:
                return self.data().decode(self.wrapper.encoding)

    def __str__(self):
        return str(unicode(self))

    def __init__(self, key, ext, canonical_name, hashstring, args, wrapper, storage_type=None):
        self.key = key
        self.ext = ext
        self.name = canonical_name
        self.hashstring = hashstring
        self.args = args
        self.wrapper = wrapper

        self.setup_storage(storage_type)

        self._data = None

        # allow doing custom setup in subclasses
        self.setup()

    def keys(self):
        return []

    def setup(self):
        pass

    def setup_storage(self, storage_type):
        self.storage_type = storage_type or self.storage_class_alias(self.ext)
        storage_class = dexy.storage.Storage.aliases[self.storage_type]
        self.storage = storage_class(self.hashstring, self.ext, self.wrapper)
        self.storage.check_location_is_in_project_dir(self.name)

    def parent_dir(self):
        return posixpath.dirname(self.name)

    def long_name(self):
        if "|" in self.key:
            return "%s%s" % (self.key.replace("|", "-"), self.ext)
        else:
            return self.name

    def basename(self):
        return posixpath.basename(self.name)

    def baserootname(self):
        """
        Returns basename stripped of file extension.
        """
        return posixpath.splitext(self.basename())[0]

    def web_safe_document_key(self):
        return self.long_name().replace("/", "--")

    def relative_path_to(self, relative_to):
        return posixpath.relpath(relative_to, self.parent_dir())

    def relative_refs(self, relative_to_file):
        doc_dir = posixpath.dirname(relative_to_file)
        return [
                posixpath.relpath(self.key, doc_dir),
                posixpath.relpath(self.long_name(), doc_dir),
                "/%s" % self.key,
                "/%s" % self.long_name()
        ]

    # Define functions that might get called on expectation of a string...

    def strip(self):
        return unicode(self).strip()
    
    def splitlines(self, arg=None):
        return unicode(self).splitlines(arg)

class Generic(Data):
    """
    Data type representing generic binary or text-based data.
    """
    ALIASES = ['generic']
    DEFAULT_STORAGE_TYPE = 'generic'

    def save(self):
        if isinstance(self._data, unicode):
            self.storage.write_data(self._data.encode("utf-8"))
        else:
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
        if self.storage.data_file_size() == 0:
            self.wrapper.log.debug("Data file for %s (%s) has size 0" % (self.key, self.storage.data_file()))
        return self.storage.data_file_exists()

    def filesize(self):
        if self.is_cached():
            return os.path.getsize(self.storage.data_file())

    def data(self):
        if not self._data:
            self.load_data()
        return self._data

    def as_text(self):
        return unicode(self)

    def as_sectioned(self):
        return {'1' : self.data()}

    def json_as_dict(self):
        return self.from_json()

    def from_json(self):
        """
        Attempts to load data using a JSON parser, returning whatever objects are defined in the JSON.
        """
        if self._data and isinstance(self._data, basestring):
            return dexy.utils.parse_json(self._data)
        else:
            with open(self.storage.data_file(), "r") as f:
                return dexy.utils.parse_json_from_file(f)

    def copy_from_file(self, filename):
        shutil.copyfile(filename, self.storage.data_file())

    def clear_data(self):
        self._data = None

    def clear_cache(self):
        if os.path.exists(self.storage.data_file()):
            os.remove(self.storage.data_file())

    def output_to_file(self, filepath):
        """
        Write canonical output to a file. Parent directory must exist already.
        """
        if not self.storage.copy_file(filepath):
            self.storage.write_data(self.data(), filepath)

class Sectioned(Generic):
    """
    Data in sections which must be kept in order.
    """
    ALIASES = ['sectioned']
    DEFAULT_STORAGE_TYPE = 'jsonordered'


    def __unicode__(self):
        return u"\n".join(unicode(v) for v in self.data().values())

    def __str__(self):
        return "\n".join(str(v) for v in self.data().values())

    def as_sectioned(self):
        return self.data()

    def keys(self):
        return self.data().keys()

    def output_to_file(self, filepath):
        """
        Write canonical output to a file.
        """
        with open(filepath, "wb") as f:
            f.write(unicode(self).encode("utf-8"))

    def value(self, key):
        return self.data()[key]

    def __getitem__(self, key):
        return self.value(key)

class KeyValue(Generic):
    """
    Data class for key-value data.
    """
    ALIASES  = ['keyvalue']
    DEFAULT_STORAGE_TYPE = 'sqlite3'

    @classmethod
    def storage_class_alias(klass, file_ext):
        if file_ext == '.sqlite3':
            return 'sqlite3'
        elif file_ext == '.json':
            return 'json'
        else:
            return klass.DEFAULT_STORAGE_TYPE

    def setup(self):
        self.storage.setup()

    def as_text(self):
        text = []
        for k, v in self.storage:
            text.append(u"%s: %s" % (k, v))
        return u"\n".join(text)

    def as_sectioned(self):
        od = OrderedDict()
        for k, v in self.storage:
            od[k] = v
        return od

    def data(self):
        return self.as_sectioned()

    def value(self, key):
        return self.storage[key]

    def __getitem__(self, key):
        return self.value(key)

    def append(self, key, value):
        self.storage.append(key, value)

    def query(self, query):
        return self.storage.query(query)

    def keys(self):
        return self.storage.keys()

    def save(self):
        self.storage.save()

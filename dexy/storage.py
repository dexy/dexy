from dexy.common import OrderedDict
from dexy.plugin import PluginMeta
import dexy.exceptions
import os
import shutil
import sqlite3

# Generic Data

class Storage:
    __metaclass__ = PluginMeta

    @classmethod
    def is_active(klass):
        return True

    def check_location_is_in_project_dir(self, filepath):
        project_root = os.path.abspath(os.getcwd())
        if not project_root in os.path.abspath(filepath):
            raise dexy.exceptions.UserFeedback("trying to write '%s' outside of '%s'" % (filepath, project_root))

    def __init__(self, hashstring, ext, wrapper):
        self.hashstring = hashstring
        self.ext = ext
        self.wrapper = wrapper

class GenericStorage(Storage):
    """
    Default type of storage where content is stored in files.
    """
    ALIASES = ['generic']

    def data_file(self):
        ext = self.ext
        if not ext:
            ext = ".ext"

        return os.path.join(self.wrapper.artifacts_dir, "%s%s" % (self.hashstring, ext))

    def data_file_exists(self):
        return os.path.exists(self.data_file())

    def data_file_size(self):
        if self.data_file_exists():
            return os.path.getsize(self.data_file())

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        self.check_location_is_in_project_dir(filepath)

        if self.data_file_exists() and not filepath == self.data_file():
            shutil.copyfile(self.data_file(), filepath)
        else:
            with open(filepath, "wb") as f:
                f.write(data)

    def read_data(self):
        with open(self.data_file(), "rb") as f:
            return f.read()

    def copy_file(self, filepath):
        """
        If data file exists, copy file and return true. Otherwise return false.
        """
        if self.data_file_exists():
            self.check_location_is_in_project_dir(filepath)
            shutil.copyfile(self.data_file(), filepath)
            return True
        else:
            return False

# Sectioned Data
import json
class JsonOrderedStorage(GenericStorage):
    """
    Storage for ordered sectional data using JSON.
    """
    ALIASES = ['jsonordered']
    MAX_DATA_DICT_DECIMALS = 5
    MAX_DATA_DICT_LENGTH = 10 ** MAX_DATA_DICT_DECIMALS

    @classmethod
    def convert_numbered_dict_to_ordered_dict(klass, numbered_dict):
        ordered_dict = OrderedDict()
        for x in sorted(numbered_dict.keys()):
            k = x.split(":", 1)[1]
            ordered_dict[k] = numbered_dict[x]
        return ordered_dict

    @classmethod
    def convert_ordered_dict_to_numbered_dict(klass, ordered_dict):
        if len(ordered_dict) >= klass.MAX_DATA_DICT_LENGTH:
            exception_msg = """Your data dict has %s items, which is greater than the arbitrary limit of %s items.
You can increase this limit by changing MAX_DATA_DICT_DECIMALS."""
            raise Exception(exception_msg % (len(ordered_dict), klass.MAX_DATA_DICT_LENGTH))

        data_dict = {}
        i = -1
        for k, v in ordered_dict.iteritems():
            i += 1
            fmt = "%%0%sd:%%s" % klass.MAX_DATA_DICT_DECIMALS
            data_dict[fmt % (i, k)] = v
        return data_dict

    def value(self, key):
        return self.data()[key]

    def __getitem__(self, key):
        return self.value(key)

    def read_data(self):
        with open(self.data_file(), "rb") as f:
            numbered_dict = json.load(f)
            return self.convert_numbered_dict_to_ordered_dict(numbered_dict)

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        self.check_location_is_in_project_dir(filepath)

        with open(filepath, "wb") as f:
            numbered_dict = self.convert_ordered_dict_to_numbered_dict(data)
            json.dump(numbered_dict, f)

# Key Value Data
class JsonStorage(GenericStorage):
    """
    Storage for key value data using JSON.
    """
    ALIASES = ['json']

    def setup(self):
        self._data = {}

    def append(self, key, value):
        self._data[key] = value

    def keys(self):
        return self.data().keys()

    def value(self, key):
        return self.data()[key]

    def __getitem__(self, key):
        return self.value(key)

    def __iter__(self):
        for k, v in self.data().iteritems():
            yield k, v

    def read_data(self):
        with open(self.data_file(), "rb") as f:
            return json.load(f)

    def data(self):
        if len(self._data) == 0:
            self._data = self.read_data()
        return self._data

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        self.check_location_is_in_project_dir(filepath)

        with open(filepath, "wb") as f:
            json.dump(data, f)

    def save(self):
        with open(self.data_file(), "wb") as f:
            json.dump(self._data, f)

class Sqlite3Storage(GenericStorage):
    """
    Storage of key value storage in sqlite3 database files.
    """
    ALIASES = ['sqlite3']

    def working_file(self):
        return os.path.join(self.wrapper.artifacts_dir, "%s-tmp%s" % (self.hashstring, self.ext))

    def setup(self):
        if os.path.exists(self.data_file()):
            self._storage = sqlite3.connect(self.data_file())
            self._cursor = self._storage.cursor()
        else:
            if os.path.exists(self.working_file()):
                os.remove(self.working_file())
            self._storage = sqlite3.connect(self.working_file())
            self._cursor = self._storage.cursor()
            self._cursor.execute("CREATE TABLE kvstore (key TEXT, value TEXT)")
            self._append_counter = 0

    def append(self, key, value):
        self._cursor.execute("INSERT INTO kvstore VALUES (?, ?)", (str(key), str(value)))
        self._append_counter += 1
        if self._append_counter > 1000:
            self.wrapper.log.debug("intermediate commit to sqlite db, resetting append counter to 0")
            self._storage.commit()
            self._append_counter = 0

    def keys(self):
        self._cursor.execute("SELECT key from kvstore")
        return [str(k[0]) for k in self._cursor.fetchall()]

    def value(self, key):
        self._cursor.execute("SELECT value from kvstore where key = ?", (key,))
        return self._cursor.fetchone()[0]

    def query(self, query):
        if not '%' in query:
            query = "%%%s%%" % query
        self._cursor.execute("SELECT * from kvstore where key like ?", (query,))
        return self._cursor.fetchall()

    def __getitem__(self, key):
        return self.value(key)

    def __iter__(self):
        self._cursor = self._storage.cursor()
        self._cursor.execute("SELECT * from kvstore")
        rows = self._cursor.fetchall()
        for k, v in rows:
            yield k, v

    def save(self):
        self.check_location_is_in_project_dir(self.data_file())
        self._storage.commit()
        shutil.copyfile(self.working_file(), self.data_file())

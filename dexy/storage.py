from dexy.common import OrderedDict
from dexy.utils import file_exists
from dexy.utils import s
import dexy.exceptions
import dexy.plugin
import os
import shutil
import sqlite3

class Storage(dexy.plugin.Plugin):
    """
    Base class for types of Storage.
    """
    __metaclass__ = dexy.plugin.PluginMeta
    _settings = {}

    def assert_location_is_in_project_dir(self, filepath):
        if not self.wrapper.is_location_in_project_dir(filepath):
            msg = "trying to write '%s' outside of '%s'"
            msgargs = (filepath, self.wrapper.project_root,)
            raise dexy.exceptions.UserFeedback(msg % msgargs)

    def __init__(self, storage_key, ext, wrapper):
        self.storage_key = storage_key
        self.ext = ext
        self.wrapper = wrapper
        self._size = None

    def setup(self):
        pass

class GenericStorage(Storage):
    """
    Default type of storage where content is stored in files.
    """
    aliases = ['generic']

    def data_file(self, read=True):
        """
        Location of data file.
        """
        if read:
            if os.path.exists(self.this_data_file()):
                return self.this_data_file()
            elif os.path.exists(self.last_data_file()):
                return self.last_data_file()
            else:
                return self.this_data_file()
        else:
            return self.this_data_file()

    def last_data_file(self):
        """
        Location of data file in last/ cache dir.
        """
        return os.path.join(self.storage_dir(False), "%s%s" % (self.storage_key, self.ext))

    def this_data_file(self):
        """
        Location of data file in this/ cache dir.
        """
        return os.path.join(self.storage_dir(True), "%s%s" % (self.storage_key, self.ext))

    def data_file_exists(self, this):
        if this:
            return os.path.exists(self.this_data_file())
        else:
            return os.path.exists(self.last_data_file())

    def data_file_size(self, this):
        if this:
            return os.path.getsize(self.this_data_file())
        else:
            return os.path.getsize(self.last_data_file())

    def storage_dir(self, this=None):
        if this is None:
            this = (self.wrapper.state in ('walked', 'running'))

        if this:
            cache_dir = self.wrapper.this_cache_dir()
        else:
            cache_dir = self.wrapper.last_cache_dir()
        
        return os.path.join(cache_dir, self.storage_key[0:2])

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file(read=False)

        self.assert_location_is_in_project_dir(filepath)

        if os.path.exists(self.this_data_file()) and not filepath == self.this_data_file():
            shutil.copyfile(self.this_data_file(), filepath)
        else:
             with open(filepath, "wb") as f:
                 if not isinstance(data, unicode):
                     f.write(data)
                 else:
                     f.write(unicode(data).encode("utf-8"))

    def read_data(self):
        with open(self.data_file(read=True), "rb") as f:
            return f.read()

    def copy_file(self, filepath):
        """
        If data file exists, copy file and return true. Otherwise return false.
        """
        try:
            self.assert_location_is_in_project_dir(filepath)
            this = (self.wrapper.state in ('walked', 'running',))
            shutil.copyfile(self.data_file(this), filepath)
            return True
        except:
            return False

# Sectioned Data
import json
class JsonOrderedStorage(GenericStorage):
    """
    Storage for ordered sectional data using JSON.
    """
    aliases = ['jsonordered']
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
            msg = s("""Your data dict has %s items, which is greater
            than the arbitrary limit of %s items.  You can increase this limit
            by changing MAX_DATA_DICT_DECIMALS.""")
            msgargs = (len(ordered_dict), klass.MAX_DATA_DICT_LENGTH)
            raise dexy.exceptions.InternalDexyProblem(msg % msgargs)

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

    def read_data(self, this=True):
        with open(self.data_file(this), "rb") as f:
            numbered_dict = json.load(f)
            return self.convert_numbered_dict_to_ordered_dict(numbered_dict)

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        self.assert_location_is_in_project_dir(filepath)

        with open(filepath, "wb") as f:
            numbered_dict = self.convert_ordered_dict_to_numbered_dict(data)
            json.dump(numbered_dict, f)

# Key Value Data
class JsonStorage(GenericStorage):
    """
    Storage for key value data using JSON.
    """
    aliases = ['json']

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

    def read_data(self, this=True):
        with open(self.data_file(this), "rb") as f:
            return json.load(f)

    def data(self):
        if len(self._data) == 0:
            self._data = self.read_data()
        return self._data

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        self.assert_location_is_in_project_dir(filepath)

        with open(filepath, "wb") as f:
            json.dump(data, f)

    def save(self):
        with open(self.data_file(read=False), "wb") as f:
            json.dump(self._data, f)

class Sqlite3Storage(GenericStorage):
    """
    Storage of key value storage in sqlite3 database files.
    """
    aliases = ['sqlite3']

    def working_file(self):
        sk = self.storage_key[0:2]
        pathargs = (
                self.wrapper.work_cache_dir(),
                sk,
                self.storage_key
                )
        return os.path.join(*pathargs)

    def connect(self):
        self._append_counter = 0
        if self.wrapper.state in ('walked', 'checked', 'running'):
            if file_exists(self.this_data_file()):
                self.connected_to = 'existing'
                self._storage = sqlite3.connect(self.this_data_file())
                self._cursor = self._storage.cursor()
            elif file_exists(self.last_data_file()):
                msg ="Should not only have last data file %s"
                msgargs=(self.last_data_file())
                raise dexy.exceptions.InternalDexyProblem(msg % msgargs)
            else:
                assert not os.path.exists(self.working_file())
                assert os.path.exists(os.path.dirname(self.working_file()))
                self.connected_to = 'working'
                self._storage = sqlite3.connect(self.working_file())
                self._cursor = self._storage.cursor()
                self._cursor.execute("CREATE TABLE kvstore (key TEXT, value TEXT)")
        elif self.wrapper.state == 'walked':
            raise dexy.exceptions.InternalDexyProblem("connect should not be called in 'walked' state")
        else:
            if file_exists(self.last_data_file()):
                self._storage = sqlite3.connect(self.last_data_file())
                self._cursor = self._storage.cursor()
            elif file_exists(self.this_data_file()):
                self._storage = sqlite3.connect(self.this_data_file())
                self._cursor = self._storage.cursor()
            else:
                raise dexy.exceptions.InternalDexyProblem("no data for %s" % self.storage_key)

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
        row = self._cursor.fetchone()
        if not row:
            raise Exception("No value found for key '%s'" % key)
        else:
            return row[0]

    def like(self, key):
        self._cursor.execute("SELECT value from kvstore where key LIKE ?", (key,))
        row = self._cursor.fetchone()
        if not row:
            raise Exception("No value found for key '%s'" % key)
        else:
            return row[0]

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
        self.assert_location_is_in_project_dir(self.data_file(read=False))
        self._storage.commit()
        shutil.copyfile(self.working_file(), self.data_file(read=False))

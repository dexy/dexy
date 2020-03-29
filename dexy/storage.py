from dexy.exceptions import UserFeedback
from dexy.exceptions import InternalDexyProblem
from dexy.utils import file_exists
import dexy.exceptions
import dexy.plugin
import os
import shutil
import sqlite3

class Storage(dexy.plugin.Plugin, metaclass=dexy.plugin.PluginMeta):
    """
    Base class for types of Storage.
    """
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

    def connect(self):
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
                 if not isinstance(data, str):
                     f.write(data)
                 else:
                     f.write(data.decode("utf-8"))

    def read_data(self):
        with open(self.data_file(read=True), "rb") as f:
            raw = f.read()
            try:
                return raw.decode('utf-8')
            except UnicodeDecodeError:
                return raw

    def copy_file(self, filepath):
        """
        If data file exists, copy file and return true. Otherwise return false.
        """
        try:
            self.assert_location_is_in_project_dir(filepath)
            this = (self.wrapper.state in ('walked', 'running', 'ran',))
            shutil.copyfile(self.data_file(this), filepath)
            return True
        except:
            return False

# Sectioned Data
import json
class JsonSectionedStorage(GenericStorage):
    """
    Storage for sectional data using JSON.
    """
    aliases = ['jsonsectioned']

    def read_data(self, this=True):
        with open(self.data_file(this), "r") as f:
            data = json.load(f)
            if hasattr(data, 'keys'):
                msg = "Data storage format has changed. Please clear your dexy cache by running dexy with '-r' option."
                raise UserFeedback(msg)
            return data

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        self.assert_location_is_in_project_dir(filepath)

        with open(filepath, "w") as f:
            json.dump(data, f)

# Key Value Data
class JsonKeyValueStorage(GenericStorage):
    """
    Storage for key value data using JSON.
    """
    aliases = ['json']

    def setup(self):
        self._data = {}

    def append(self, key, value):
        self._data[key] = value

    def keys(self):
        return list(self.data().keys())

    def value(self, key):
        return self.data()[key]

    def __getitem__(self, key):
        return self.value(key)

    def items(self):
        return list(self.data().items())

    def iteritems(self):
        return iter(self.data().items())

    def read_data(self, this=True):
        with open(self.data_file(this), "r") as f:
            return json.load(f)

    def data(self):
        if len(self._data) == 0:
            self._data = self.read_data()
        return self._data

    def persist(self):
        self.write_data(self._data)

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        self.assert_location_is_in_project_dir(filepath)

        with open(filepath, "w") as f:
            json.dump(data, f)

class Sqlite3KeyValueStorage(GenericStorage):
    """
    Storage of key value storage in sqlite3 database files.
    """
    aliases = ['sqlite3']

    def working_file(self):
        sk = self.storage_key[0:2]
        pathargs = (
                self.wrapper.work_cache_dir(),
                sk,
                "%s.sqlite3" % self.storage_key,
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
        self._cursor.execute("INSERT INTO kvstore VALUES (?, ?)", (key, value))
        self._append_counter += 1
        if self._append_counter > 1000:
            self.wrapper.log.debug("intermediate commit to sqlite db, resetting append counter to 0")
            self._storage.commit()
            self._append_counter = 0

    def keys(self):
        self._cursor.execute("SELECT key from kvstore")
        return [str(k[0]) for k in self._cursor.fetchall()]

    def items(self):
        self._cursor.execute("SELECT key, value from kvstore")
        for k in self._cursor.fetchall():
            yield (str(k[0]), k[1])

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

    def persist(self):
        if self.connected_to == 'existing':
            assert os.path.exists(self.data_file(read=False))
        elif self.connected_to == 'working':
            self.assert_location_is_in_project_dir(self.data_file(read=False))
            self._storage.commit()
            shutil.copyfile(self.working_file(), self.data_file(read=False))
        else:
            msg = "Unexpected 'connected_to' value %s"
            msgargs = self.connected_to
            raise InternalDexyProblem(msg % msgargs)

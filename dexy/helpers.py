"""
Helpers for use in Python scripts to store data in a dexy-friendly format.

Data storage is typically intended to be write-once, read-one-or-more-times.

Intended to help with Python scripts and to serve as templates for implementing
similar helpers in other languages, or alternate Python implementations.
"""
import csv
import dexy.commands
import json
import os

class DataStorage(object):
    """
    Parent class for RowData and KeyValueData.
    """
    def __init__(self, filename, headers=None):
        self.filename = filename
        self.ext = os.path.splitext(filename)[1]
        self.headers = headers

        if os.path.exists(self.filename):
            self.init_read()
        else:
            self.init_write()

    def init_write(self):
        self.mode = "write"

        if self.ext == ".csv":
            self._data_file = open(self.filename, "wb")
            self._writer = csv.writer(self._data_file)
            if self.headers:
                self._writer.writerow(self.headers)

        elif self.ext == ".json":
            self._storage = {}

        elif self.ext == ".kch":
            from kyotocabinet import DB
            self._storage = DB()
            if not self._storage.open(self.filename, DB.OWRITER | DB.OCREATE):
                msg = "Error opening kyotocabinet db: %s" % (self._storage.error())
                raise dexy.commands.UserFeedback(msg)

        elif self.ext == ".sqlite3":
            self.init_write_sqlite3()

        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)

    def init_read(self):
        self.mode = "read"

        if self.ext == ".csv":
            self._file = open(self.filename, "rb")
        elif self.ext == ".json":
            with open(self.filename, "rb") as f:
                self._storage = json.load(f)
        elif self.ext == ".kch":
            from kyotocabinet import DB
            self._storage = DB()
            self._storage.open(self.filename, DB.OREADER)
        elif self.ext == ".sqlite3":
            import sqlite3
            self._storage = sqlite3.connect(self.filename)
            self._cursor = self._storage.cursor()
        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)

    def save(self):
        if self.ext == ".csv":
            self._data_file.close()
        elif self.ext == ".json":
            with open(self.filename, "wb") as f:
                import json
                json.dump(self._storage, f)
        elif self.ext == ".kch":
            if not self._storage.close():
                raise dexy.commands.UserFeedback(self._storage.error())
        elif self.ext == ".sqlite3":
            self._storage.commit()
            self._cursor.close()
        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)

class RowData(DataStorage):
    def init_write_sqlite3(self):
        import sqlite3
        self._storage = sqlite3.connect(self.filename)
        self._cursor = self._storage.cursor()
        # TODO need to define fields based on headers

    def append(self, *rowdata):
        if not self.mode == "write":
            raise dexy.commands.UserFeedback("Trying to write but in %s mode!" % self.mode)

        if self.ext == ".csv":
            self._writer.writerow(rowdata)
        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)

    def read(self):
        """
        Return all available data.
        """
        if not self.mode == "read":
            raise dexy.commands.UserFeedback("Trying to read but in '%s' mode!" % self.mode)

        if self.ext == ".csv":
            return self._file.read()
        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)

class KeyValueData(DataStorage):
    EXTENSIONS = [".json", ".sqlite3", ".kch"]

    def init_write_sqlite3(self):
        import sqlite3
        self._storage = sqlite3.connect(self.filename)
        self._cursor = self._storage.cursor()
        self._cursor.execute("CREATE TABLE kvstore (key TEXT, value TEXT)")

    def append(self, key, value):
        if self.ext == ".json":
            self._storage[key] = value
        elif self.ext == ".kch":
            if not self._storage.set(key, value):
                raise dexy.commands.UserFeedback("Error setting key %s in kyotocabinet: %s" % (key, self._storage.error()))
        elif self.ext == ".sqlite3":
            self._cursor.execute("INSERT INTO kvstore VALUES (?, ?)", (str(key), str(value)))
        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)

    def retrieve(self, key):
        if not self.mode == "read":
            raise dexy.commands.UserFeedback("Trying to read but in '%s' mode!" % self.mode)

        if self.ext == ".json":
            return self._storage[key]
        elif self.ext == ".kch":
            return self._storage.get(key)
        elif self.ext == ".sqlite3":
            self._cursor.execute("SELECT value from kvstore where key = ?", (key,))
            record = self._cursor.fetchone()
            if record:
                return record[0]
        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)

    def get(self, key, default=None):
        """
        Safe mode of 'retrieve' that returns None if no value is available.
        """
        if not self.mode == "read":
            raise dexy.commands.UserFeedback("Trying to read but in '%s' mode!" % self.mode)

        if self.ext == ".json":
            return self._storage.get(key, default)
        elif self.ext == ".kch":
            return self._storage.get(key)
        elif self.ext == ".sqlite3":
            self._cursor.execute("SELECT value from kvstore where key = ?", (key,))
            record = self._cursor.fetchone()
            if record:
                return record[0]
            else:
                return default
        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)


    def keys(self):
        if not self.mode == "read":
            raise dexy.commands.UserFeedback("Trying to read but in '%s' mode!" % self.mode)

        if self.ext == ".json":
            return self._storage.keys()
        elif self.ext == ".kch":
            return self._storage.match_prefix(None)
        elif self.ext == ".sqlite3":
            self._cursor.execute("SELECT key from kvstore")
            return [str(k[0]) for k in self._cursor.fetchall()]
        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)

    def query(self, query_string):
        if not self.mode == "read":
            raise dexy.commands.UserFeedback("Trying to read but in '%s' mode!" % self.mode)

        if self.ext == ".sqlite3":
            self._cursor.execute("SELECT * from kvstore WHERE key LIKE ? COLLATE RTRIM ORDER BY key", (query_string,))
            return [k[0] for k in self._cursor]
        elif self.ext == ".json":
            return [k for k in self.keys() if query_string in k]
        else:
            raise dexy.commands.UserFeedback("unsupported extension %s" % self.ext)

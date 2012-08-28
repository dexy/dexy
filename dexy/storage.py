from dexy.plugin import PluginMeta
import shutil
from ordereddict import OrderedDict
import os

# Generic Data

class Storage:
    __metaclass__ = PluginMeta

    @classmethod
    def is_active(klass):
        return True

    def __init__(self, hashstring, ext, run_params):
        self.hashstring = hashstring
        self.ext = ext
        self.run_params = run_params

class GenericStorage(Storage):
    ALIASES = ['generic']

    def data_file(self):
        return os.path.join(self.run_params.artifacts_dir, "%s%s" % (self.hashstring, self.ext))

    def data_file_exists(self):
        return os.path.exists(self.data_file())

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        if self.data_file_exists():
            shutil.copyfile(self.data_file(), filepath)
        else:
            with open(filepath, "wb") as f:
                f.write(data)

    def read_data(self):
        with open(self.data_file(), "rb") as f:
            return f.read()

# Sectioned Data
import json
class JsonOrderedStorage(GenericStorage):
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

    def read_data(self):
        with open(self.data_file(), "rb") as f:
            numbered_dict = json.load(f)
            return self.convert_numbered_dict_to_ordered_dict(numbered_dict)

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        with open(filepath, "wb") as f:
            numbered_dict = self.convert_ordered_dict_to_numbered_dict(data)
            json.dump(numbered_dict, f)

# Key Value Data
class JsonStorage(GenericStorage):
    ALIASES = ['json']

    def read_data(self):
        with open(self.data_file(), "rb") as f:
            return json.load(f)

    def write_data(self, data, filepath=None):
        if not filepath:
            filepath = self.data_file()

        with open(filepath, "wb") as f:
            json.dump(data, f)

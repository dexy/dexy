from dexy.data import Generic
from dexy.storage import GenericStorage
try:
    import tables
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class H5(Generic):
    """
    Data type for reading HDF5 files using pytables.
    """
    aliases = ['h5']
    _settings = {
            'storage-type' : 'h5storage'
            }

    def walk_groups(self):
        return self.data().walk_groups()

class H5Storage(GenericStorage):
    """
    Storage backend representing HDF5 files.
    """
    aliases = ['h5storage']

    def read_data(self):
        return tables.open_file(self.data_file(read=True), "r")

from dexy.common import OrderedDict
from dexy.plugin import PluginMeta
import hashlib

class Metadata:
    ALIASES = []
    __metaclass__ = PluginMeta

    @classmethod
    def is_active(klass):
        return True

    def get_string_for_hash(self):
        ordered = OrderedDict()
        for k in sorted(self.__dict__):
            ordered[k] = str(self.__dict__[k])

        return str(ordered)

class Md5(Metadata):
    """
    Class that stores metadata for a task. Uses md5 to calculate hash.
    """
    ALIASES = ['md5']
    def compute_hash(self):
        text = self.get_string_for_hash()
        return hashlib.md5(text).hexdigest()

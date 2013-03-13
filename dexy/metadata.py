import dexy.plugin
import hashlib

class Metadata(dexy.plugin.Plugin):
    ALIASES = []
    __metaclass__ = dexy.plugin.PluginMeta

    def is_active(self):
        return True

    def __init__(self):
        self.hash_info = {
                'file' : {},
                'args' : {},
                'env' : {},
                'inputs' : {},
                'children' : {},
                }

    def hash_info_by_kind(self, kind):
        ordered = []
        for k in sorted(self.hash_info[kind]):
            v = self.hash_info[kind][k]
            ordered.append((k, str(v),))
        return str(ordered)

    def hash_info_for_kinds(self, kinds=None, skip=None):
        if not kinds:
            if not skip:
                skip = []
            kinds = (k for k in sorted(self.hash_info.keys()) if not k in skip)

        ordered = []
        for k in kinds:
            ordered.append((k, self.hashstring_for_kind(k),))
        return str(ordered)

    def hashstring_for_kind(self, kind):
        text = self.hash_info_by_kind(kind)
        return self.do_hash(text)

    def compute_hash(self):
        text = self.hash_info_for_kinds(skip=["children"])
        return self.do_hash(text)

    def compute_hash_without_inputs(self):
        text = self.hash_info_for_kinds(skip=["children", "inputs"])
        return self.do_hash(text)

    def compute_hash_with_children(self):
        text = self.hash_info_for_kinds(skip=["inputs"])
        return self.do_hash(text)

    def do_hash(self):
        raise dexy.exceptions.InternalDexyProblem("should be implemented in subclass")

class Md5(Metadata):
    """
    Class that stores metadata for a task. Uses md5 to calculate hash.
    """
    ALIASES = ['md5']

    def do_hash(self, text):
        return hashlib.md5(text).hexdigest()

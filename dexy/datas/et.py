from dexy.data import Generic
import xml.etree.ElementTree as ET

class EtreeData(Generic):
    """
    Expose etree method to query XML using ElementTree.
    """
    aliases = ['etree']

    def etree(self):
        """
        Returns a tree root object.
        """
        if not hasattr(self, '_etree_root'):
            self._etree_root = ET.fromstring(self.data())
        return self._etree_root

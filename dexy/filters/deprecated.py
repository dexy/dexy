from dexy.filter import DexyFilter
import dexy.exceptions

class Deprecated(DexyFilter):
    """
    Base class for deprecated filters.
    """
    aliases = []

    def process(self):
        msg = "%s\n%s" % (self.artifact.key, self.__doc__)
        raise dexy.exceptions.UserFeedback(msg)

class FilenameFilter(Deprecated):
    """
    Deprecated. No longer needed.
    
    Dexy should now automatically detect new files that are created by your
    scripts if the add-new-files setting is true (which it is by default in
    many filters). You should remove '|fn' from your config and anywhere
    documents are referenced, and remove the 'dexy--' prefix from filenames in
    your scripts.
    """
    aliases = ['fn']

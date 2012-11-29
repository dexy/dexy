from dexy.filter import DexyFilter
import dexy.exceptions

class Deprecated(DexyFilter):
    """
    Base class for deprecated filters.
    """
    ALIASES = []

    def process(self):
        msg = "%s\n%s" % (self.artifact.key, self.__doc__)
        raise dexy.exceptions.UserFeedback(msg)

class FilenameFilter(Deprecated):
    """
    The filename (fn) filter has been removed from dexy. Dexy should now
    automatically detect new files that are created by your scripts. You should
    remove '|fn' from your config and anywhere documents are referenced, and
    remove the 'dexy--' prefix from filenames in your scripts.
    """
    ALIASES = ['fn']


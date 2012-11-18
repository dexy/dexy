from dexy.filter import DexyFilter
import dexy.exceptions

class Deprecated(DexyFilter):
    ALIASES = ['deprecated']

    def process(self):
        msg = "%s\n%s" % (self.artifact.key, self.MSG)
        raise dexy.exceptions.UserFeedback(msg)

class FilenameFilter(Deprecated):
    ALIASES = ['fn']
    MSG = """\
The filename (fn) filter has been removed from dexy. Dexy should now
automatically detect new files that are created by your scripts. You should
remove '|fn' from your config and anywhere documents are referenced, and remove
the 'dexy--' prefix from filenames in your scripts."""


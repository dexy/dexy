from docutils import core
from dexy.dexy_filter import DexyFilter

class RestructuredTextFilter(DexyFilter):
    """
    A 'native' ReST filter which uses the library rather than the command line tool. Recommended.
    """
    ALIASES = ['rst']
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".html", ".tex"]

    def process_text(self, input_text):
        if self.artifact.ext == ".html":
            parts = core.publish_parts(
                    input_text,
                    writer_name = "html"
                    )
            return parts['body']
        elif self.artifact.ext == ".tex":
            parts = core.publish_parts(
                    input_text,
                    writer_name = "latex"
                    )

            # Note any latex requirements in logfile
            self.log.debug("Requirements for ReST:")
            for l in parts['requirements'].splitlines():
                self.log.debug(l)
            return parts['body']
        else:
            raise Exception("unsupported extension %s" % self.artifact.ext)



from dexy.filter import DexyFilter
from dexy.plugins.process_filters import SubprocessFilter

try:
    from docutils import core
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class RestructuredTextFilter(DexyFilter):
    """
    A 'native' ReST filter which uses the docutils library.
    """
    ALIASES = ['rst']
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".html", ".tex", ".xml"]

    @classmethod
    def is_active(klass):
        return AVAILABLE

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

class Rst2HtmlFilter(SubprocessFilter):
    """
    This uses the command line tool rst2html.
    """
    ADD_NEW_FILES = False
    EXECUTABLES = ['rst2html', 'rst2html.py']
    VERSION_COMMAND = 'rst2html.py --version'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['rst2html']

class Rst2LatexFilter(SubprocessFilter):
    """
    This uses the command line tool rst2latex.
    """
    ADD_NEW_FILES = False
    ALIASES = ['rst2latex']
    EXECUTABLES = ['rst2latex', 'rst2latex.py']
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    VERSION_COMMAND = 'rst2latex.py --version'

class Rst2XmlFilter(SubprocessFilter):
    """
    This uses the command line tool rst2xml.
    """
    ADD_NEW_FILES = False
    EXECUTABLES = ['rst2xml', 'rst2xml.py']
    VERSION_COMMAND = 'rst2xml.py --version'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2xml']

class Rst2OdtFilter(SubprocessFilter):
    """
    This uses the command line tool rst2odt.
    """
    EXECUTABLES = ['rst2odt', 'rst2odt.py']
    VERSION_COMMAND = 'rst2odt.py --version'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".odt"]
    ALIASES = ['rst2odt']

class Rst2BeamerFilter(SubprocessFilter):
    """
    Filter for rst2beamer command line tool, requires docutils plus rst2beamer package.
    """
    ADD_NEW_FILES = False
    ALIASES = ['rst2beamer']
    EXECUTABLES = ['rst2beamer', 'rst2beamer.py']
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    VERSION_COMMAND = "rst2beamer --version"

class Rst2Man(SubprocessFilter):
    """
    Filter for rst2man command line tool, requires docutils.
    """
    ADD_NEW_FILES = False
    ALIASES = ['rst2man']
    EXECUTABLES = ['rst2man', 'rst2man.py']
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".man"]
    VERSION_COMMAND = "rst2man.py --version"

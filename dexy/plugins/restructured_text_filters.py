from dexy.filter import DexyFilter
from dexy.plugins.process_filters import SubprocessFilter

try:
    from docutils import core
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class RestructuredTextBase(DexyFilter):
    """
    Base class for ReST filters using the docutils library.
    """
    ALIASES = []
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".html", ".tex", ".xml"]

    @classmethod
    def is_active(klass):
        return AVAILABLE

    def docutils_writer_name(self):
        if self.arg_value('writer'):
            return self.arg_value('writer')
        elif self.artifact.ext == ".html":
            return 'html'
        elif self.artifact.ext == ".tex":
            return 'latex2e'
        elif self.artifact.ext == ".xml":
            return 'docutils_xml'
        else:
            raise Exception("unsupported extension %s" % self.artifact.ext)

class RestructuredText(RestructuredTextBase):
    """
    A 'native' ReST filter which uses the docutils library.
    """
    ALIASES = ['rst']
    FRAGMENT = False

    def process(self):
        core.publish_file(
                source_path = self.input().storage.data_file(),
                destination_path = self.output().storage.data_file(),
                writer_name=self.docutils_writer_name(),
                settings_overrides=self.args()
                )

class RstBody(RestructuredTextBase):
    """
    Returns just the body part of an ReST document.
    """
    ALIASES = ['rstbody']

    def process_text(self, input_text):
        parts = core.publish_parts(
                input_text,
                writer_name=self.docutils_writer_name(),
                )
        return parts['body']

class RstDocParts(DexyFilter):
    """
    Returns key-value storage of document parts.
    """
    ALIASES = ['rstdocparts']
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_DATA_TYPE = 'keyvalue'
    OUTPUT_EXTENSIONS = ['.sqlite3', '.json']

    def process(self):
        input_text = unicode(self.input())
        writer = self.arg_value('writer', 'html')

        parts = core.publish_parts(
                input_text,
                writer_name = writer
                )

        for k, v in parts.iteritems():
            self.output().append(k, v)
        self.output().save()

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

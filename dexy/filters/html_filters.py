from bs4 import BeautifulSoup
from dexy.dexy_filter import DexyFilter
from dexy.helpers import KeyValueData
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import get_lexer_for_filename

class HtmlSectionFilter(DexyFilter):
    """
    Returns any element of an HTML document with an 'id' attribute.
    """
    INPUT_EXTENSIONS = [".xml", ".html", ".md", ".txt"]
    OUTPUT_EXTENSIONS = KeyValueData.EXTENSIONS
    ALIASES = ["htmlsec"]

    def process(self):
        self.artifact.setup_kv_storage()
        html_formatter = HtmlFormatter(lineanchors=self.artifact.web_safe_document_key())
        latex_formatter = LatexFormatter()

        soup = BeautifulSoup(self.artifact.input_text())

        for element in soup.find_all(id=True):
            element_id = element.attrs['id']
            self.artifact.storage().append("%s:text" % element_id, element.text)
            self.artifact.storage().append("%s:source" % element_id, str(element))
            # TODO add more attributes

        self.artifact._storage.save()

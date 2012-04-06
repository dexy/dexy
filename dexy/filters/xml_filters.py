from dexy.dexy_filter import DexyFilter
from lxml import etree
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import get_lexer_for_filename

class XmlSectionFilter(DexyFilter):
    """
    Returns any element of an XML or HTML document with an 'id' attribute.
    """
    INPUT_EXTENSIONS = [".xml", ".html", ".md", ".txt"]
    OUTPUT_EXTENSIONS = [".json", ".kch"]
    ALIASES = ["xxml"]

    def process(self):
        self.artifact.setup_kv_storage()

        lexer = get_lexer_for_filename(self.artifact.previous_canonical_filename)
        html_formatter = HtmlFormatter(lineanchors=self.artifact.web_safe_document_key())
        latex_formatter = LatexFormatter()

        root = etree.fromstring(self.artifact.input_text().encode("utf-8"))
        tree = root.getroottree()

        for element in tree.iter("*"):
            if element.attrib.has_key('id'):
                element_id = element.attrib['id']
                source = etree.tostring(element, pretty_print=True).strip()
                inner_html = "\n".join(etree.tostring(child) for child in element.iterchildren())
                self.artifact.append_to_kv_storage("%s:lineno" % element_id, element.sourceline)
                self.artifact.append_to_kv_storage("%s:tail" % element_id, element.tail)
                self.artifact.append_to_kv_storage("%s:text" % element_id, element.text)
                self.artifact.append_to_kv_storage("%s:source" % element_id, source)
                self.artifact.append_to_kv_storage("%s:inner-html" % element_id, inner_html)
                self.artifact.append_to_kv_storage("%s:html-source" % element_id, highlight(source, lexer, html_formatter))
                self.artifact.append_to_kv_storage("%s:latex-source" % element_id, highlight(source, lexer, latex_formatter))

        self.artifact.persist_kv_storage()
        self.artifact.data_dict = self.artifact.input_data_dict

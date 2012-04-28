from dexy.dexy_filter import DexyFilter
from dexy.helpers import KeyValueData
from lxml import etree
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import get_lexer_for_filename

class XmlSectionFilter(DexyFilter):
    """
    Returns any element of an XML document with an 'id' attribute.
    """
    INPUT_EXTENSIONS = [".xml", ".html", ".md", ".txt"]
    OUTPUT_EXTENSIONS = KeyValueData.EXTENSIONS
    ALIASES = ["xxml", "xmlsec"]

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
                self.artifact._storage.append("%s:lineno" % element_id, element.sourceline)
                self.artifact._storage.append("%s:tail" % element_id, element.tail)
                self.artifact._storage.append("%s:text" % element_id, element.text)
                self.artifact._storage.append("%s:source" % element_id, source)
                self.artifact._storage.append("%s:inner-html" % element_id, inner_html)
                self.artifact._storage.append("%s:html-source" % element_id, highlight(source, lexer, html_formatter))
                self.artifact._storage.append("%s:latex-source" % element_id, highlight(source, lexer, latex_formatter))

        self.artifact._storage.save()

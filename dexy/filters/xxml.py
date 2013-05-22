from dexy.filter import DexyFilter
from lxml import etree
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import get_lexer_for_filename

class XmlSectionFilter(DexyFilter):
    """
    Stores all elements of an XML document which have an 'id' attribute in key-value storage.
    """
    aliases = ["xxml", "xmlsec"]
    _settings = {
            'input-extensions' : [".xml", ".html", ".txt"],
            'output-data-type' : 'keyvalue',
            'output-extensions' :  [".json", ".sqlite3"]
            }

    def process(self):
        assert self.output_data.state == 'ready'

        lexer = get_lexer_for_filename(self.input_data.storage.data_file())
        html_formatter = HtmlFormatter(lineanchors=self.output_data.web_safe_document_key())
        latex_formatter = LatexFormatter()

        root = etree.fromstring(unicode(self.input_data))
        tree = root.getroottree()

        for element in tree.iter("*"):
            if element.attrib.has_key('id'):
                element_id = element.attrib['id']
                source = etree.tostring(element, pretty_print=True).strip()
                inner_html = "\n".join(etree.tostring(child) for child in element.iterchildren())
                self.output_data.append("%s:lineno" % element_id, element.sourceline)
                self.output_data.append("%s:tail" % element_id, element.tail)
                self.output_data.append("%s:text" % element_id, element.text)
                self.output_data.append("%s:source" % element_id, source)
                self.output_data.append("%s:inner-html" % element_id, inner_html)
                self.output_data.append("%s:html-source" % element_id, highlight(source, lexer, html_formatter))
                self.output_data.append("%s:latex-source" % element_id, highlight(source, lexer, latex_formatter))

        self.output_data.save()

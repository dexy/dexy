from dexy.filter import DexyFilter
from lxml import etree
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import get_lexer_for_filename

class XmlSectionFilter(DexyFilter):
    """
    Stores all elements of an XML document in key-value storage. Elements are
    indexed by an xpath (calculated using tree.getpath(element), and also an id
    attribute if it is present in the element.
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

        root = etree.XML(str(self.input_data))
        tree = root.getroottree()

        for element in tree.iter("*"):
            element_ids = [tree.getpath(element)]
            if element.attrib.has_key('id'):
                element_ids.append(element.attrib['id'])
            if element.attrib.has_key('name'):
                element_ids.append("%s:%s" % (element.tag, element.attrib['name']))

            for element_id in element_ids:
                source = etree.tostring(element, pretty_print=True).strip()
                inner_html = "\n".join(etree.tostring(child) for child in element.iterchildren())
                self.output_data.append("%s:lineno" % element_id, element.sourceline)
                self.output_data.append("%s:tail" % element_id, element.tail)
                self.output_data.append("%s:text" % element_id, element.text)
                self.output_data.append("%s:tag" % element_id, element.tag)
                self.output_data.append("%s:source" % element_id, source)
                self.output_data.append("%s:inner-html" % element_id, inner_html)
                self.output_data.append("%s:html-source" % element_id, highlight(source, lexer, html_formatter))
                self.output_data.append("%s:latex-source" % element_id, highlight(source, lexer, latex_formatter))

        self.output_data.save()

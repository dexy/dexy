from dexy.dexy_filter import DexyFilter
from lxml import etree
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers.web import XmlLexer
import json


class XmlSectionFilter(DexyFilter):
    """
    A filter for breaking an XML file up into various sections, referenced by
    xpaths, and optionally syntax highlighting the various sections to allow
    easy access to any subsection of an XML document.
    """
    INPUT_EXTENSIONS = [".xml"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ["xxml"]
    FINAL = False

    def process_text(self, input_text):
        lexer = XmlLexer()
        html_formatter = HtmlFormatter(lineanchors=self.artifact.web_safe_document_key())
        latex_formatter = LatexFormatter()

        output = {}

        root = etree.fromstring(input_text)
        tree = root.getroottree()

        for element in tree.iter("*"):
            xpath = tree.getpath(element)
            source = etree.tostring(element, pretty_print=True).strip()

            # Convert _Attrib to dict
            attributes = dict((k, v) for k, v in element.attrib.iteritems())

            element_info = {
                    "attributes" : attributes,
                    "lineno" : element.sourceline,
                    "prefix" : element.prefix,
                    "source" : source,
                    "source-html" : highlight(source, lexer, html_formatter),
                    "source-latex" : highlight(source, lexer, latex_formatter),
                    "tag" : element.tag,
                    "tail" : element.tail,
                    "text" : element.text
                }
            output[xpath] = element_info

            if attributes.has_key("name"):
                key = "%s:%s" % (element.tag, attributes["name"])
                output[key] = element_info

        return json.dumps(output, indent=4, sort_keys=True)

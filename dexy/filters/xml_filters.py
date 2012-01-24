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
        html_formatter = HtmlFormatter()
        latex_formatter = LatexFormatter()

        output = {}

        root = etree.fromstring(input_text)
        tree = root.getroottree()

        for element in tree.iter("*"):
            xpath = tree.getpath(element)
            source = etree.tostring(element, pretty_print=True).strip()
            output[xpath] = {
                    "lineno" : element.sourceline,
                    "source" : source,
                    "source-html" : highlight(source, lexer, html_formatter),
                    "source-latex" : highlight(source, lexer, latex_formatter),
                    "tag" : element.tag,
                    "tail" : element.tail,
                    "text" : element.text
                }

        return json.dumps(output, indent=4, sort_keys=True)

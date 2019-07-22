from dexy.filter import DexyFilter
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import get_lexer_for_filename
import json

try:
    from lxml import etree
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class XmlSectionFilter(DexyFilter):
    """
    Stores all elements in the input XML document which have any of the
    attributes specified in unique-attributes or qualified-attributes.
    """
    aliases = ["xxml", "xmlsec"]
    _settings = {
            'input-extensions' : [".xml", ".html", ".txt"],
            'pygments' : ("Whether to apply pygments syntax highlighting", True),
            'unique-attributes' : ("Elements to be added if they have this attribute, to be treated as globally unique.", ["id"]),
            'qualified-attributes' : ("Elements to be added if they have this attribute, to be qualified by element type.", ["name"]),
            'data-type' : 'keyvalue',
            'output-extensions' :  [".json", ".sqlite3"]
            }

    def is_active(self):
        return AVAILABLE

    def append_element_attributes_with_key(self, element, element_key):
        source = etree.tostring(element, pretty_print=True).strip()
        inner_html = "\n".join(etree.tostring(child) for child in element.iterchildren())
        self.output_data.append("%s:lineno" % element_key, element.sourceline)
        self.output_data.append("%s:tail" % element_key, element.tail)
        self.output_data.append("%s:text" % element_key, element.text)
        self.output_data.append("%s:tag" % element_key, element.tag)
        self.output_data.append("%s:source" % element_key, source)
        self.output_data.append("%s:inner-html" % element_key, inner_html)

        safe_attrib = {}
        for k, v in element.attrib.items():
            try:
                json.dumps(v)
                safe_attrib[k] = v
            except TypeError:
                pass

        self.output_data.append("%s:attrib" % element_key, json.dumps(safe_attrib))

        if self.setting('pygments'):
            self.output_data.append("%s:html-source" % element_key, highlight(source, self.lexer, self.html_formatter))
            self.output_data.append("%s:latex-source" % element_key, highlight(source, self.lexer, self.latex_formatter))

    def process(self):
        assert self.output_data.state == 'ready'

        if self.setting('pygments'):
            self.lexer = get_lexer_for_filename(self.input_data.storage.data_file())
            self.html_formatter = HtmlFormatter(lineanchors=self.output_data.web_safe_document_key())
            self.latex_formatter = LatexFormatter()

        if self.input_data.ext in ('.xml', '.txt'):
            parser = etree.XMLParser()
        elif self.input_data.ext == '.html':
            parser = etree.HTMLParser()
        else:
            raise Exception("Unsupported extension %s" % self.input_data.ext)

        tree = etree.parse(self.input_data.storage.data_file(), parser)

        for element in tree.iter("*"):
            element_keys = []
           
            for attribute_name in self.setting('unique-attributes'):
                if attribute_name in element.attrib:
                    element_keys.append(element.attrib[attribute_name])
            for attribute_name in self.setting('qualified-attributes'):
                if attribute_name in element.attrib:
                    element_keys.append(element.attrib[attribute_name])
                    element_keys.append("%s:%s" % (element.tag, element.attrib[attribute_name]))

            for element_key in element_keys:
                self.append_element_attributes_with_key(element, element_key)

        self.output_data.save()

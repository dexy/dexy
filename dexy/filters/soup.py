from dexy.filter import DexyFilter
import inflection
import re

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

class SoupSections(DexyFilter):
    """
    Split a HTML file into nested sections based on header tags.
    """
    aliases = ['soups']

    _settings = {
            'output-data-type' : 'sectioned',
            'html-parser' : ("Name of html parser BeautifulSoup should use.", 'html.parser'),
            'initial-section-name' : ("Name to use for the initial section which currently holds all the contents.", u"Actual Document Contents"),
            }

    def is_active(self):
        return BS4_AVAILABLE

    def append_current_section(self):
        section_dict = {
                "name" : self.current_section_name,
                "contents" : self.current_section_text,
                "level" : self.current_section_level,
                "id" : self.current_section_anchor
                }
        self.output_data._data.append(section_dict)

    def process(self):
        soup = BeautifulSoup(unicode(self.input_data), self.setting('html-parser'))

        for tag in soup.find_all(re.compile("^h[0-6]")):
            name = tag.text
            m = re.match("^h([0-6])$", tag.name)

            if not tag.attrs.has_key('id'):
                tag.attrs['id'] = inflection.parameterize(name)

            self.current_section_anchor = tag.attrs['id']
            self.current_section_text = None
            self.current_section_name = name
            self.current_section_level = int(m.groups()[0])

            self.append_current_section()

        self.current_section_text = unicode(soup)
        self.current_section_name = self.setting('initial-section-name')
        self.current_section_level = 1
        self.current_section_anchor = None

        self.append_current_section()

        self.output_data.save()

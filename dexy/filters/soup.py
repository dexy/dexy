from dexy.filter import DexyFilter
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
            'initial-section-name' : ("Name to use for a section which appears before any header tags.", u"Initial Anonymous Section"),
            }

    def is_active(self):
        return BS4_AVAILABLE

    def process_tag(self, tag):
        if hasattr(tag, 'name'):
            m = re.match("^h([0-6])$", tag.name)
            if m:
                if self.current_section_text:
                    self.append_current_section()

                self.current_section_text = [unicode(tag)]
                self.current_section_name = tag.text
                self.current_section_level = int(m.groups()[0])

            else:
                self.current_section_text.append(unicode(tag))


    def append_current_section(self):
        section_dict = {
                "name" : self.current_section_name,
                "contents" : "\n".join(self.current_section_text),
                "level" : self.current_section_level
                }
        self.output_data._data.append(section_dict)

    def process(self):
        soup = BeautifulSoup(unicode(self.input_data))
        body = soup("body")[0]

        self.current_section_text = []
        self.current_section_name = self.setting('initial-section-name')
        self.current_section_level = 1

        first = body.find(True)

        self.process_tag(first)

        # Iterate over all top-level elements.
        for tag in first.next_siblings:
            self.process_tag(tag)

        self.append_current_section()

        self.output_data.save()

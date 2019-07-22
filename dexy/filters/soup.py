from bs4 import BeautifulSoup
from dexy.filter import DexyFilter
from dexy.utils import chdir
import base64
import inflection
import mimetypes
import re
import urllib

class Customize(DexyFilter):
    """
    Add <script> tags or <link> tags to an HTML file's header.
    
    Uses BeautifulSoup.
    """
    aliases = ['customize']

    _settings = {
            'scripts' : ("Javascript files to add.", []),
            'stylesheets' : ("CSS files to add.", [])
            }

    def process_text(self, input_text):
        soup = BeautifulSoup(input_text)

        for js in self.setting('scripts'):
            js_tag = soup.new_tag("script", type="text/javascript", src=js)
            soup.head.append(js_tag)

        for css in self.setting('stylesheets'):
            css_tag = soup.new_tag("link", rel="stylesheet", type="text/css", href=css)
            soup.head.append(css_tag)

        return str(soup)

class InlineAssets(DexyFilter):
    """
    Imports any referenced images as data URIs.
    """
    aliases = ['inliner']

    _settings = {
            'html-parser' : ("Name of html parser BeautifulSoup should use.", 'html.parser'),
            'inline-images' : ("Whether to inline images using the data uri scheme.", True),
            'inline-styles' : ("Whether to embed referenced CSS in the page header.", True)
            }

    def inline_images(self, soup):
        for tag in soup.find_all("img"):
            path = tag.get('src')

            f = urllib.urlopen(path)
            data = f.read()
            f.close()

            mime, _ = mimetypes.guess_type(path)
            data64 = base64.encodestring(data)
            dataURI = 'data:%s;base64,%s' % (mime, data64)
            tag['src'] = dataURI

    def inline_styles(self, soup):
        for tag in soup.find_all("link"):
            path = tag.get('href')

            f = urllib.urlopen(path)
            data = f.read()
            f.close()

            style = soup.new_tag('style')
            style.string = data

            tag.replace_with(style)

    def process(self):
        soup = BeautifulSoup(str(self.input_data), self.setting('html-parser'))
        self.populate_workspace()

        with chdir(self.parent_work_dir()):
            if self.setting('inline-images'):
                self.inline_images(soup)
    
            if self.setting('inline-styles'):
                self.inline_styles(soup)
    
        self.output_data.set_data(str(soup))

class SoupSections(DexyFilter):
    """
    Split a HTML file into nested sections based on header tags.
    """
    aliases = ['soups']

    _settings = {
            'data-type' : 'sectioned',
            'html-parser' : ("Name of html parser BeautifulSoup should use.", 'html.parser'),
            'initial-section-name' : ("Name to use for the initial section which currently holds all the contents.", "Actual Document Contents"),
            }

    def append_current_section(self):
        section_dict = {
                "name" : self.current_section_name,
                "contents" : self.current_section_text,
                "level" : self.current_section_level,
                "id" : self.current_section_anchor
                }
        self.output_data._data.append(section_dict)

    def process(self):
        soup = BeautifulSoup(str(self.input_data), self.setting('html-parser'))

        for tag in soup.find_all(re.compile("^h[0-6]")):
            name = tag.text
            m = re.match("^h([0-6])$", tag.name)

            if not 'id' in tag.attrs:
                tag.attrs['id'] = inflection.parameterize(name)

            self.current_section_anchor = tag.attrs['id']
            self.current_section_text = None
            self.current_section_name = name
            self.current_section_level = int(m.groups()[0])

            self.append_current_section()

        self.current_section_text = str(soup)
        self.current_section_name = self.setting('initial-section-name')
        self.current_section_level = 1
        self.current_section_anchor = None

        self.append_current_section()

        self.output_data.save()

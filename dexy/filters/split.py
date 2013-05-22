from dexy.common import OrderedDict
from dexy.filter import DexyFilter
import os
import re

class HtmlSectionsFilter(DexyFilter):
    """
    Split content according to HTML comments.
    """
    aliases = ['htmlsections']
    _settings = {
            'examples' : ['htmlsections'],
            'output' : True,
            'output-data-type' : 'sectioned',
            'output-extensions' : ['.json']
            }

    def process(self):
        output = OrderedDict()

        sections = re.split("<!-- section \"(.+)\" -->\n", unicode(self.input_data))

        for i in range(1, len(sections), 2):
            section_name = sections[i]
            section_content = sections[i+1]
            if not section_name == 'end':
                output[section_name] = section_content

        self.output_data.set_data(output)

class SplitHtmlFilter(DexyFilter):
    """
    Create multiple HTML pages from a single template, with an automatic index page.

    The split filter looks for specially formatted HTML comments in your
    document and splits your HTML into separate pages at each split comment.
    """
    aliases = ['split', 'splithtml']
    _settings = {
            'output' : True,
            'input-extensions' : ['.html'],
            'output-extensions' : ['.html'],
            'split-ul-class' : ("HTML class to apply to <ul> elements", None)
            }

    def process(self):
        input_text = unicode(self.input_data)

        if input_text.find("<!-- endsplit -->") > 0:
            body, footer = re.split("<!-- endsplit -->", input_text, maxsplit=1)
            sections = re.split("<!-- split \"(.+)\" -->\n", body)
            header = sections[0]

            pages = OrderedDict()
            index_content = None
            for i in range(1, len(sections), 2):
                if sections[i] == 'index':
                    index_content = sections[i+1]
                else:
                    section_label = sections[i]
                    section_url = section_label.split(" ")[0]

                    filename = "%s.html" % section_url
                    filepath = os.path.join(self.output_data.parent_dir(), filename)
                    pages[section_label] = filename

                    new_page = self.add_doc(filepath, header + sections[i+1] + footer)
                    new_page.args['title'] = section_label

                    self.log_debug("added key %s to %s ; links to file %s" %
                              (filepath, self.key, new_page.name))

            index_items = []
            for k in sorted(pages.keys()):
                index_items.append("""<li><a href="%s">%s</a></li>""" %
                                   (pages[k], k))

            output = []
            output.append(header)
            if index_content:
                output.append(index_content)

            if self.setting("split-ul-class"):
                ul = "<ul class=\"%s\">" % self.setting('split-ul-class')
            else:
                ul = "<ul class=\"split\">"

            output.append("%s\n%s\n</ul>" % (ul, "\n".join(index_items)))
            output.append(footer)
        else:
            # No endsplit found, do nothing.
            output = input_text

        self.output_data.set_data("\n".join(output))

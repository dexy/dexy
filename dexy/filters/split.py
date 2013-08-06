from dexy.filter import DexyFilter
import os
import re

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
            rawbody, footer = re.split("<!-- endsplit -->", input_text, maxsplit=1)
           
            if rawbody.find("<!-- footer -->") > 0:
                body, index_footer_content = re.split("<!-- footer -->", rawbody, maxsplit=1) 
            else:
                body = rawbody
                index_footer_content = ""

            sections = re.split("<!-- split \"(.+)\" -->\n", body)
            header = sections[0]

            pages = {}
            index_top_content = ""
            for i in range(1, len(sections), 2):
                if sections[i] == 'index':
                    index_top_content = sections[i+1]
                else:
                    section_label = sections[i]
                    section_content = sections[i+1]

                    section_url = section_label.split(" ")[0]

                    if "<!-- content -->" in section_content:
                        section_description, section_content = section_content.split("<!-- content -->")
                    else:
                        section_description = ""

                    filename = "%s.html" % section_url

                    filepath = os.path.join(self.output_data.parent_dir(), filename)
                    pages[section_label] = (section_description, filename,)

                    new_page = self.add_doc(filepath, header + section_content + footer)
                    new_page.update_setting('title', section_label)

                    self.log_debug("added key %s to %s ; links to file %s" %
                              (filepath, self.key, new_page.name))

            index_items = ""
            for page_label in sorted(pages):
                page_description, filename = pages[page_label]
                index_items += """<li><a href="%s">%s</a></li>\n%s\n""" % (filename, page_label, page_description)

            output = header + index_top_content

            if self.setting("split-ul-class"):
                ul = "<ul class=\"%s\">" % self.setting('split-ul-class')
            else:
                ul = "<ul class=\"split\">"

            output += "%s\n%s\n</ul>" % (ul, index_items)
            output += index_footer_content + footer

        else:
            # No endsplit found, do nothing.
            output = input_text

        self.output_data.set_data(output)

from dexy.filter import Filter
import re
import os
from ordereddict import OrderedDict

class SplitHtmlFilter(Filter):
    """
    Create multiple HTML pages from a single template, with an automatic index page.

    The split filter looks for specially formatted HTML comments in your
    document and splits your HTML into separate pages at each split comment.
    """
    ALIASES = ['split', 'splithtml']
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]

    def process(self):
        input_text = self.artifact.input_data.data()

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
                    section_name = sections[i]
                    # TODO proper url/filename escaping
                    section_url = section_name.replace(" ","-")

                    filename = "%s.html" % section_url
                    filepath = os.path.join(self.artifact.parent_dir(), filename)
                    pages[section_name] = filename

                    new_page = self.add_doc(filepath, header + sections[i+1] + footer)

                    self.artifact.log.debug("added key %s to artifact %s ; links to file %s" %
                              (filepath, self.artifact.key, new_page.name))

            index_items = []
            for k in sorted(pages.keys()):
                index_items.append("""<li><a href="%s">%s</a></li>""" %
                                   (pages[k], k))

            output = []
            output.append(header)
            if index_content:
                output.append(index_content)

            if self.artifact.args.has_key("split-ul-class"):
                ul = "<ul class=\"%s\">" % self.artifact.args['split-ul-class']
            else:
                ul = "<ul class=\"split\">"

            output.append("%s\n%s\n</ul>" % (ul, "\n".join(index_items)))
            output.append(footer)
        else:
            # No endsplit found, do nothing.
            output = input_text

        self.artifact.output_data.set_data("\n".join(output))

#class SplitLatexFilter(Filter):
#    """Splits a latex doc into multiple latex docs."""
#    ALIASES = ['splitlatex']
#    INPUT_EXTENSIONS = [".tex"]
#    OUTPUT_EXTENSIONS = [".tex"]
#    FINAL = True
#
#    def process(self):
#        parent_dir = os.path.dirname(self.artifact.canonical_filename())
#        input_text = self.artifact.input_text()
#
#        if input_text.find("%% endsplit\n") > 0:
#            body, footer = re.split("%% endsplit\n", input_text, maxsplit=1)
#            sections = re.split("%% split \"(.+)\"\n", body)
#            header = sections[0]
#
#            pages = OrderedDict()
#            for i in range(1, len(sections), 2):
#                section_name = sections[i]
#                # TODO proper url/filename escaping
#                section_url = section_name.replace(" ","-")
#                source = header + sections[i+1] + footer
#
#                ext = '.tex'
#
#                filename = "%s%s" % (section_url, ext)
#                filepath = os.path.join(parent_dir, filename)
#                pages[section_name] = filename
#
#                artifact = self.artifact.__class__(filepath)
#                artifact.ext = ext
#                artifact.binary = False
#                artifact.final = True
#                artifact.artifacts_dir = self.artifact.artifacts_dir
#                artifact.hashstring = str(uuid.uuid4())
#                artifact.set_data(source)
#                artifact.save()
#
#                self.artifact.inputs()[filepath] = artifact
#                self.artifact.log.debug("added key %s to artifact %s ; links to file %s" %
#                          (filepath, self.artifact.key, artifact.filename()))
#
#            index_items = []
#            for k in sorted(pages.keys()):
#                index_items.append("""<li><a href="%s">%s</a></li>""" %
#                                   (pages[k], k))
#
#        output_dict = self.artifact.input_data_dict
#        self.artifact.data_dict = output_dict

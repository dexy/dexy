from dexy.dexy_filter import DexyFilter
from dexy.utils import print_string_diff
from dexy.utils import wrap_text
from ordereddict import OrderedDict
import copy
import json
import os
import re
import uuid

class TestFilter(DexyFilter):
    """
    Lets you test the output of running a filter, raises exception if expectation not met.

    If the test passes, the original content is returned so you can chain this filter.
    """

    ALIASES = ['test']

    def process(self):
        if self.artifact.controller_args['disabletests']:
            print "tests disabled, not running test", self.artifact.key
            self.artifact.data_dict = self.artifact.input_data_dict
            return False

        print "testing", self.artifact.key, "...",

        if self.artifact.args.has_key('test-expects'):
            # 'expects' should be an exact match
            expects = self.artifact.args['test-expects']
            if expects.startswith("@"):
                expects_file = open(expects.lstrip("@"), "r")
                expects_content = expects_file.read()
                expects_file.close()
            else:
                expects_content = expects
            expects = expects_content

            if hasattr(expects, 'items'):
                for k, v in self.artifact.input_data_dict.items():
                    msg = print_string_diff(expects[k], v)
                    msg += "\nexpected output '%s' (section %s) does not match actual '%s'" % (expects[k], k, v)
                    assert expects[k] == v, msg
            else:
                inp = self.artifact.input_text()
                msg = print_string_diff(expects, inp)
                msg += "\nexpected output '%s' does not match actual '%s'" % (expects, inp)
                assert expects == inp, msg
        elif self.artifact.args.has_key('test-includes'):
            # specified text should appear somewhere in the output
            includes_text = self.artifact.args['test-includes']
            assert includes_text in self.artifact.input_text()

        elif self.artifact.args.has_key('expects'):
            raise Exception("'expects' is deprecated, please use 'test-expects' instead.")

        else:
            raise Exception("Must pass one of 'test-expects', 'test-includes' to test filter so there is something to test.")

        comment = ""
        if self.artifact.args.has_key("comment"):
           comment = "[%s]" % self.artifact.args['comment']
        print "ok", comment

        # Return the original output, so 'test' filter doesn't change anything.
        self.artifact.data_dict = self.artifact.input_data_dict

class JoinFilter(DexyFilter):
    """
    Takes sectioned code and joins it into a single section. Some filters which
    don't preserve sections will raise an error if they receive multiple
    sections as input, so this forces acknowledgement that sections will be
    lost.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['join']

    def process_dict(self, input_dict):
        return {'1' : self.artifact.input_text()}


class HeaderFilter(DexyFilter):
    """
    Adds a header to file. Looks for a file named _header.ext where ext is the
    same extension as the file this is being applied to. So _header.html for a
    file named index.html. Or, you can specify the name of the header file to
    use in the args by passing a value to 'header'.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['hd', 'header']
    DEFAULT_FILTERS = ['jinja']

    def find_closest_parent(self, param_name = 'header'):
        inputs = self.artifact.inputs()

        search_key_specified = self.artifact.args.has_key(param_name)

        if search_key_specified:
            search_key = self.artifact.args[param_name]
        else:
            # nothing specified, look for the default pattern
            search_key = "_%s%s" % (param_name, self.artifact.ext)

        path_elements = self.artifact.name.split(os.sep)[:-1]
        doc = None
        n = len(path_elements)

        if search_key_specified and "/" in search_key:
            n = -1
            doc = inputs[search_key.lstrip("/")]

        for i in range(0, n+1):
            # Start in the immediate directory, proceed through parent
            # directories as far as project root until a header file is
            # found.
            if i < n:
                directory = os.path.join(*(path_elements[0:(n-i)]))
                search_key_in_dir = os.path.join(directory, search_key)
            else:
                search_key_in_dir = search_key

            if inputs.has_key(search_key_in_dir):
                doc = inputs[search_key_in_dir]

            elif not search_key_specified:
                for pattern in self.DEFAULT_FILTERS:
                    if pattern:
                        try_key = "%s|%s" % (search_key_in_dir, pattern)
                    if inputs.has_key(try_key):
                        doc = inputs[try_key]
                        break

            if doc:
                break

        return doc

    def process_text(self, input_text):
        header_doc = self.find_closest_parent()

        if not header_doc:
            raise Exception("Couldn't find input to use for header. Available inputs: %s" % ",".join(self.artifact.inputs().keys()))

        self.log.debug("using %s as header for %s" % (header_doc.key, self.artifact.document_key))
        return "%s\n%s" % (header_doc.output_text(), input_text)

class FooterFilter(HeaderFilter):
    """
    Adds a footer to file. Looks for a file named _footer.ext where ext is the
    same extension as the file this is being applied to. So _footer.html for a
    file named index.html. Or, you can specify the name of the footer file to
    use in the args by passing a value to 'footer'.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['ft', 'footer']
    DEFAULT_FOOTER_FILTERS = ['dexy', 'jinja']

    def process_text(self, input_text):
        footer_doc = self.find_closest_parent('footer')

        if not footer_doc:
            raise Exception("Couldn't find input to use for footer. Available inputs: %s" % ",".join(self.artifact.inputs().keys()))

        self.log.debug("using %s as footer for %s" % (footer_doc.key, self.artifact.document_key))
        return "%s\n%s" % (input_text, footer_doc.output_text())

class HeadFilter(DexyFilter):
    """
    Returns just the first 10 lines of input.
    """
    ALIASES = ['head']
    def process_text(self, input_text):
        return "\n".join(input_text.split("\n")[0:10]) + "\n"

class WordWrapFilter(DexyFilter):
    """
    Wraps text after 79 characters (tries to preserve existing line breaks and
    spaces).
    """
    ALIASES = ['ww', 'wrap']
    DEFAULT_WIDTH=79

    def process_text(self, input_text):
        if self.artifact.args.has_key('width'):
            width = self.artifact.args['width']
        else:
            width=self.DEFAULT_WIDTH

        return wrap_text(input_text, width)

class SplitHtmlFilter(DexyFilter):
    """
    Create multiple HTML pages from a single template, with an automatic index page.

    The split filter looks for specially formatted HTML comments in your
    document and splits your HTML into separate pages at each split comment.
    """
    ALIASES = ['split', 'splithtml']
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]
    FINAL = True

    def process(self):
        parent_dir = os.path.dirname(self.artifact.canonical_filename())
        input_text = self.artifact.input_text()

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
                    filepath = os.path.join(parent_dir, filename)
                    pages[section_name] = filename

                    artifact = self.artifact.add_additional_artifact(filepath, 'html')
                    artifact.set_data(header + sections[i+1] + footer)
                    artifact.save()

                    self.artifact.log.debug("added key %s to artifact %s ; links to file %s" %
                              (filepath, self.artifact.key, artifact.filename()))

            index_items = []
            for k in sorted(pages.keys()):
                index_items.append("""<li><a href="%s">%s</a></li>""" %
                                   (pages[k], k))

            output_dict = OrderedDict()
            output_dict['header'] = header
            if index_content:
                output_dict['index-page-content'] = index_content

            if self.artifact.args.has_key("split-ul-class"):
                ul = "<ul class=\"%s\">" % self.artifact.args['split-ul-class']
            else:
                ul = "<ul class=\"split\">"

            output_dict['index'] = "%s\n%s\n</ul>" % (ul, "\n".join(index_items))
            output_dict['footer'] = footer
        else:
            # No endsplit found, do nothing.
            output_dict = self.artifact.input_data_dict
        self.artifact.data_dict = output_dict

class SplitLatexFilter(DexyFilter):
    """Splits a latex doc into multiple latex docs."""
    ALIASES = ['splitlatex']
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    FINAL = True

    def process(self):
        parent_dir = os.path.dirname(self.artifact.canonical_filename())
        input_text = self.artifact.input_text()

        if input_text.find("%% endsplit\n") > 0:
            body, footer = re.split("%% endsplit\n", input_text, maxsplit=1)
            sections = re.split("%% split \"(.+)\"\n", body)
            header = sections[0]

            pages = OrderedDict()
            for i in range(1, len(sections), 2):
                section_name = sections[i]
                # TODO proper url/filename escaping
                section_url = section_name.replace(" ","-")
                source = header + sections[i+1] + footer

                ext = '.tex'

                filename = "%s%s" % (section_url, ext)
                filepath = os.path.join(parent_dir, filename)
                pages[section_name] = filename

                artifact = self.artifact.__class__(filepath)
                artifact.ext = ext
                artifact.binary = False
                artifact.final = True
                artifact.artifacts_dir = self.artifact.artifacts_dir
                artifact.hashstring = str(uuid.uuid4())
                artifact.set_data(source)
                artifact.save()

                self.artifact.inputs()[filepath] = artifact
                self.artifact.log.debug("added key %s to artifact %s ; links to file %s" %
                          (filepath, self.artifact.key, artifact.filename()))

            index_items = []
            for k in sorted(pages.keys()):
                index_items.append("""<li><a href="%s">%s</a></li>""" %
                                   (pages[k], k))

        output_dict = self.artifact.input_data_dict
        self.artifact.data_dict = output_dict

class PrettyPrintJsonFilter(DexyFilter):
    ALIASES = ['ppjson']
    OUTPUT_EXTENSIONS = ['.json']

    def process_text(self, input_text):
        json_content = json.loads(input_text)
        return json.dumps(json_content, sort_keys=True, indent=4)

class SillyFilter(DexyFilter):
    ALIASES =['silly']

    def process_text(self, input_text):
        return "you said: '%s'\n that's silly!\n" % input_text

class SectionsByLineFilter(DexyFilter):
    ALIASES = ['lines']

    def process_text_to_dict(self, input_text):
        data_dict = OrderedDict()
        for i, line in enumerate(input_text.splitlines()):
            data_dict["%s" % (i+1)] = line
        return data_dict

class MarkupTagsFilter(DexyFilter):
    """
    Wrap text in specified HTML tags.
    """
    ALIASES = ['tags']

    def process_text(self, input_text):
        tags = copy.copy(self.artifact.args['tags'])
        open_tags = "".join("<%s>" % t for t in tags)
        tags.reverse()
        close_tags = "".join("</%s>" % t for t in tags)

        return "%s\n%s\n%s" % (open_tags, input_text, close_tags)

class StartSpaceFilter(DexyFilter):
    """
    Add a blank space to the start of each line.

    Useful for passing syntax highlighted/preformatted code to mediawiki.
    """
    ALIASES = ['ss', 'startspace']

    def process_text(self, input_text):
        return "\n".join(" %s" % line for line in input_text.splitlines())

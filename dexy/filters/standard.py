from dexy.filter import DexyFilter
from dexy.utils import indent
import copy
import dexy.exceptions
import json
import os
import re
import textwrap

class Resub(DexyFilter):
    """
    Runs re.sub on each line of input.
    """
    aliases = ['resub']
    _settings = {
            'expressions' : ("Tuples of (regexp, replacement) to apply.", []),
            }

    def process_text(self, input_text):
        for regexp, replacement in self.setting('expressions'):
            self.log_debug("Applying %s" % regexp)
            working_text = []

            for line in input_text.splitlines():
                working_text.append(re.sub(regexp, replacement, line))

            input_text = "\n".join(working_text)

        return input_text


class PreserveDataClassFilter(DexyFilter):
    """
    Sets PRESERVE_PRIOR_DATA_CLASS to True.
    """
    aliases = []
    _settings = {
            'preserve-prior-data-class' : True
            }

    def data_class_alias(self, ext):
        if self.setting('preserve-prior-data-class'):
            return self.input_data.alias
        else:
            return self.setting('data-type')

    def calculate_canonical_name(self):
        return self.prev_filter.calculate_canonical_name()

class ChangeExtensionManuallyFilter(PreserveDataClassFilter):
    """
    Dummy filter for allowing changing a file extension.
    """
    aliases = ['chext']

class KeyValueStoreFilter(DexyFilter):
    """
    Creates a new key-value store.

    The key-value store will be populated via side effects from other filters.
    """
    aliases = ['kv']
    _settings = {
            'data-type' : 'keyvalue'
            }

    def process(self):
        self.output_data.copy_from_file(self.input_data.storage.data_file())

        # Call setup() again since it will have created a new blank database.
        self.output_data.storage.setup()
        self.output_data.storage.connect()

class HeaderFilter(DexyFilter):
    """
    Apply another file to top of file.
    """
    aliases = ['hd']
    _settings = {
            'key-name' : ("Name of key to use.", 'header'),
            'header' : ("Document key of file to use as header.", None)
            }

    def find_input_in_parent_dir(self, matches):
        docs = list(self.doc.walk_input_docs())
        docs_d = dict((task.output_data().long_name(), task) for task in docs)

        key_name = self.setting('key-name')
        requested = self.setting(key_name)
        if requested:
            if requested in docs_d:
                matched_key = requested
            else:
                msg = "Couldn't find the %s file %s you requested" % (self.setting(key_name), requested)
                raise dexy.exceptions.UserFeedback(msg)
        else:
            matched_key = None
            for k in sorted(docs_d.keys()):
                if (os.path.dirname(k) in self.output_data.parent_dir()) and (matches in k):
                    matched_key = k

        if not matched_key:
            msg = "no %s input found for %s" 
            msgargs = (self.setting('key-name'), self.key)
            raise dexy.exceptions.UserFeedback(msg % msgargs)

        return docs_d[matched_key].output_data()

    def process_text(self, input_text):
        header_data = self.find_input_in_parent_dir("_header")
        return "%s\n%s" % (str(header_data), input_text)

class FooterFilter(HeaderFilter):
    """
    Apply another file to bottom of file.
    """
    aliases = ['ft']
    _settings = {
            'key-name' : 'footer',
            'footer' : ("Document key of file to use as footer.", None)
            }

    def process_text(self, input_text):
        footer_data = self.find_input_in_parent_dir("_footer")
        return "%s\n%s" % (input_text, str(footer_data))

class TemplateContentFilter(HeaderFilter):
    """
    Apply template to file. Template should specify %(content)s.
    """
    aliases = ['applytemplate']
    _settings = {
            'key-name' : 'template',
            'template' : ("Document key of file to use as template.", None)
            }

    def process_text(self, input_text):
        template_data = self.find_input_in_parent_dir("_template")
        return str(template_data) % { 'content' : input_text, 'title' : self.input_data.title()}

class FormatTemplateContentFilter(HeaderFilter):
    """
    Apply template to file. Template should specify {content}.
    """
    aliases = ['formattemplate']
    _settings = {
            'key-name' : 'template',
            'template' : ("Document key of file to use as footer.", None)
            }

    def process_text(self, input_text):
        template_data = self.find_input_in_parent_dir("_template")
        return str(template_data).format({ 'content' : input_text, 'title' : self.input_data.title()})

class MarkupTagsFilter(DexyFilter):
    """
    Wrap text in specified HTML tags.
    """
    aliases = ['tags']
    _settings = {
            'tags' : ("Tags.", {})
            }

    def process_text(self, input_text):
        tags = copy.copy(self.setting('tags'))
        open_tags = "".join("<%s>" % t for t in tags)
        tags.reverse()
        close_tags = "".join("</%s>" % t for t in tags)

        return "%s\n%s\n%s" % (open_tags, input_text, close_tags)

class StartSpaceFilter(DexyFilter):
    """
    Add a blank space to the start of each line.

    Useful for passing syntax highlighted/preformatted code to mediawiki.
    """
    aliases = ['ss', 'startspace']
    _settings = {
            'n' : ("Number of spaces to prepend to each line.", 1),
            'data-type' : 'sectioned'
            }

    def process(self):
        n = self.setting('n')
        for section_name, section_input in self.input_data.items():
            self.output_data[section_name] = indent(section_input, n)
        self.output_data.save()

class SectionsByLine(DexyFilter):
    """
    Returns each line in its own section.
    """
    aliases = ['lines']
    _settings = {
            'data-type' : 'sectioned'
            }

    def process(self):
        input_text = str(self.input_data)
        for i, line in enumerate(input_text.splitlines()):
            self.output_data["%s" % (i+1)] = line
        self.output_data.save()

class ClojureWhitespaceFilter(DexyFilter):
    """
    Parse clojure code into sections based on whitespace and try to guess a
    useful name for each section by looking for def, defn, deftest or a
    comment.
    """
    aliases = ['cljws']
    _settings = {
            'added-in-version' : '1.0.1',
            'data-type' : 'sectioned',
            'name-regex' : (
                """List of regular expressions including a match group
                representing the name of the section. Will be tried in
                order.""",
                [
                    "\(def ([a-z\-\?]+)",
                    "\(defn ([a-z\-\?]+)",
                    "\(defn- ([a-z\-\?]+)",
                    "\(defn= ([a-z\-\?]+)",
                    "\(deftest ([a-z\-\?]+)",
                ])
            }

    def process(self):
        input_text = str(self.input_data)
        for i, section in enumerate(input_text.split("\n\n")):
            section_name = self.parse_section_name(section)
            if section_name:
                self.output_data[section_name] = section
            else:
                self.output_data["%s" % (i+1)] = section

        self.output_data.save()

    def parse_section_name(self, section_text):
        """
        Parse a section name out of the section text.
        """
        if not section_text:
            return

        for line in section_text.splitlines():
            firstline = line
            if not line.strip().startswith(';'):
                break

        for regex in self.setting('name-regex'):
            m = re.match(regex, firstline)
            if m:
                return m.groups()[0]

class PrettyPrintJsonFilter(DexyFilter):
    """
    Pretty prints JSON input.
    """
    aliases = ['ppjson']
    _settings = {
            'output-extensions' : ['.json']
            }

    def process_text(self, input_text):
        json_content = json.loads(input_text)
        return json.dumps(json_content, sort_keys=True, indent=4)

class JoinFilter(DexyFilter):
    """
    Takes sectioned code and joins it into a single section. Some filters which
    don't preserve sections will raise an error if they receive multiple
    sections as input, so this forces acknowledgement that sections will be
    lost.
    """
    aliases = ['join']

    def process(self):
        joined_data = "\n".join(str(v) for v in list(self.input_data.values()))
        print("joined data is", joined_data)
        self.output_data.set_data(joined_data)

class HeadFilter(DexyFilter):
    """
    Returns just the first 10 lines of input.
    """
    aliases = ['head']

    def process_text(self, input_text):
        return "\n".join(input_text.split("\n")[0:10]) + "\n"

class WordWrapFilter(DexyFilter):
    """
    Wraps text after 79 characters (tries to preserve existing line breaks and
    spaces).
    """
    aliases = ['ww', 'wrap']
    _settings = {
            'width' : ("Width of text to wrap to.", 79)
            }

    def wrap_text(self, text, width):
        """
        A word-wrap function that preserves existing line breaks
        and most spaces in the text. Expects that existing line
        breaks are posix newlines (\n).
        """
        return "\n".join(textwrap.wrap(text, width))

    def process_text(self, input_text):
        return self.wrap_text(input_text, self.setting('width'))

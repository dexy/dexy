from dexy.common import OrderedDict
from dexy.filter import DexyFilter
import copy
import dexy.exceptions
import json
import os

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
            return self.setting('output-data-type')

    def calculate_canonical_name(self):
        return self.prev_filter.calculate_canonical_name()

class ChangeExtensionManuallyFilter(PreserveDataClassFilter):
    """
    Dummy filter for allowing changing a file extension.
    """
    aliases = ['chext']

class KeyValueStoreFilter(DexyFilter):
    """
    Filter for creating a new key value store on the fly
    """
    aliases = ['kv']
    _settings = {
            'output-data-type' : 'keyvalue'
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
            if docs_d.has_key(requested):
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
            msgargs = (self.KEY_NAME, self.key)
            raise dexy.exceptions.UserFeedback(msg % msgargs)

        return docs_d[matched_key].output_data()

    def process_text(self, input_text):
        header_data = self.find_input_in_parent_dir("_header")
        return "%s\n%s" % (header_data.as_text(), input_text)

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
        return "%s\n%s" % (input_text, footer_data.as_text())

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
            'n' : ("Number of spaces to prepend to each line.", 1)
            }

    @classmethod
    def add_spaces_at_start(self, text, n):
        spaces = " " * n
        return "\n".join("%s%s" % (spaces, line) for line in text.splitlines())

    def process_dict(self, input_dict):
        result = OrderedDict()
        n = self.setting('n')
        for section_name, section_text in input_dict.iteritems():
            result[section_name] = self.add_spaces_at_start(section_text, n)
        return result

class SectionsByLineFilter(DexyFilter):
    """
    Returns each line in its own section.
    """
    aliases = ['lines']
    _settings = {
            'output-data-type' : 'sectioned'
            }

    def process_text_to_dict(self, input_text):
        data_dict = OrderedDict()
        for i, line in enumerate(input_text.splitlines()):
            data_dict["%s" % (i+1)] = line
        return data_dict

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
        joined_data = "\n".join(self.input_data.as_sectioned().values())
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

    #http://code.activestate.com/recipes/148061-one-liner-word-wrap-function/
    def wrap_text(self, text, width):
        """
        A word-wrap function that preserves existing line breaks
        and most spaces in the text. Expects that existing line
        breaks are posix newlines (\n).
        """
        return reduce(lambda line, word, width=width: '%s%s%s' %
                 (line,
                   ' \n'[(len(line)-line.rfind('\n')-1
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 )

    def process_text(self, input_text):
        return self.wrap_text(input_text, self.setting('width'))

from dexy.filter import Filter
import json
import copy
from dexy.common import OrderedDict

class MarkupTagsFilter(Filter):
    """
    Wrap text in specified HTML tags.
    """
    ALIASES = ['tags']

    def process_text(self, input_text):
        tags = copy.copy(self.args()['tags'])
        open_tags = "".join("<%s>" % t for t in tags)
        tags.reverse()
        close_tags = "".join("</%s>" % t for t in tags)

        return "%s\n%s\n%s" % (open_tags, input_text, close_tags)

class StartSpaceFilter(Filter):
    """
    Add a blank space to the start of each line.

    Useful for passing syntax highlighted/preformatted code to mediawiki.
    """
    ALIASES = ['ss', 'startspace']

    def process_text(self, input_text):
        return "\n".join(" %s" % line for line in input_text.splitlines())

class SectionsByLineFilter(Filter):
    ALIASES = ['lines']
    OUTPUT_DATA_TYPE = 'sectioned'

    def process_text_to_dict(self, input_text):
        data_dict = OrderedDict()
        for i, line in enumerate(input_text.splitlines()):
            data_dict["%s" % (i+1)] = line
        return data_dict

class PrettyPrintJsonFilter(Filter):
    ALIASES = ['ppjson']
    OUTPUT_EXTENSIONS = ['.json']

    def process_text(self, input_text):
        json_content = json.loads(input_text)
        return json.dumps(json_content, sort_keys=True, indent=4)

class JoinFilter(Filter):
    """
    Takes sectioned code and joins it into a single section. Some filters which
    don't preserve sections will raise an error if they receive multiple
    sections as input, so this forces acknowledgement that sections will be
    lost.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['join']

    def process(self):
        joined_data = "\n".join(self.artifact.input_data.as_sectioned().values())
        self.artifact.output_data.set_data(joined_data)

class HeadFilter(Filter):
    """
    Returns just the first 10 lines of input.
    """
    ALIASES = ['head']
    def process_text(self, input_text):
        return "\n".join(input_text.split("\n")[0:10]) + "\n"

class WordWrapFilter(Filter):
    """
    Wraps text after 79 characters (tries to preserve existing line breaks and
    spaces).
    """
    ALIASES = ['ww', 'wrap']
    DEFAULT_WIDTH=79

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
        width = self.args().get('width', self.DEFAULT_WIDTH)
        return self.wrap_text(input_text, width)

from dexy.handler import DexyHandler
import shutil
from dexy.utils import print_string_diff

class TestHandler(DexyHandler):
    """The test handler raises an error if output is not as expected. Handy for
    testing your custom filters or for ensuring that examples in your
    documentation stay correct."""

    ALIASES = ['test']

    def process(self):
        print "testing", self.artifact.key, "...",
        if not self.artifact.doc.args.has_key('expects'):
            raise "You need to pass 'expects' to the test filter."

        expects = self.artifact.doc.args['expects']
        # TODO check if expects is a filename and if so load contents of file
        # TODO handle different types of expectation, e.g. when don't know exact
        # output but can look for type of data returned
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

        print "ok"

        # Don't change the output so we can use end result still...
        self.artifact.data_dict = self.artifact.input_data_dict

class CopyHandler(DexyHandler):
    """
    Like 'dexy' filter for binary files. Copies the file without trying to read
    the contents. Hacky!
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['cp']
    
    def process(self):
        self.artifact.auto_write_artifact = False
        shutil.copyfile(self.doc.name, self.artifact.filename())

class JoinHandler(DexyHandler):
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

class FooterHandler(DexyHandler):
    """
    Adds a footer to file. Looks for a file named _footer.ext where ext is the
    same extension as the file this is being applied to. So _footer.html for a
    file named index.html.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['ft', 'footer']

    def process_text(self, input_text):
        self.artifact.load_input_artifacts()
        footer_key = "_footer%s" % self.artifact.ext
        footer_keys = []
        for k in self.artifact.input_artifacts_dict.keys():
            contains_footer = k.find(footer_key) > 0
            contains_pyg = k.find('|pyg') > 0
            if contains_footer and not contains_pyg:
                footer_keys.append(k)

        if len(footer_keys) > 0:
            footer_key = sorted(footer_keys)[-1]
            footer_text = self.artifact.input_artifacts_dict[footer_key]['data']
        else:
            raise Exception("No file matching %s was found to work as a footer." % footer_key)
                            
        return "%s\n%s" % (input_text, footer_text)

class HeaderHandler(DexyHandler):
    """
    Adds a header to file. Looks for a file named _header.ext where ext is the
    same extension as the file this is being applied to. So _header.html for a
    file named index.html.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['hd', 'header']

    def process_text(self, input_text):
        self.artifact.load_input_artifacts()
        header_key = "_header%s" % self.artifact.ext
        header_keys = []
        for k in self.artifact.input_artifacts_dict.keys():
            contains_header = k.find(header_key) > 0
            contains_pyg = k.find('|pyg') > 0
            if contains_header and not contains_pyg:
                header_keys.append(k)
        if len(header_keys) > 0:
            header_key = sorted(header_keys)[-1]
            header_text = self.artifact.input_artifacts_dict[header_key]['data']
        else:
            raise Exception("No file matching %s was found to work as a header for %s." % (header_key, self.artifact.key))
                            
        return "%s\n%s" % (header_text, input_text)

# TODO implement combined header/footer handler as a shortcut

### @export "head-handler"
class HeadHandler(DexyHandler):
    """
    Returns just the first 10 lines of input.
    """
    ALIASES = ['head']
    def process_text(self, input_text):
        return "\n".join(input_text.split("\n")[0:10]) + "\n"

### @export "word-wrap"
class WordWrapHandler(DexyHandler):
    """
    Wraps text after 79 characters (tries to preserve existing line breaks and
    spaces).
    """
    ALIASES = ['ww', 'wrap']

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
        return self.wrap_text(input_text, 79)

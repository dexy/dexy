"""
DexyFilters written to be examples of how to write filters.
"""
from dexy.common import OrderedDict
from dexy.doc import Doc
from dexy.filter import DexyFilter
import os

class Example(DexyFilter):
    """
    Base class for example filters intended to show filter development features but not be actual usable filters.
    """
    ALIASES = []
    NODOC = True

class KeyValueExample(Example):
    """
    Example of storing key value data.
    """
    ALIASES = ['keyvalueexample']
    OUTPUT_DATA_TYPE = 'keyvalue'
    OUTPUT_EXTENSIONS = ['.sqlite3', '.json']

    def process(self):
        self.output().append("foo", "bar")
        self.output().save()

class AccessOtherDocuments(Example):
    """
    Example of accessing other documents.
    """
    ALIASES = ["others"]

    def process_text(self, input_text):
        info = []
        info.append("Here is a list of previous docs in this tree (not including %s)." % self.artifact.key)

        ### @export "access-other-docs-iterate"
        for doc in self.processed():
            assert isinstance(doc, Doc)

            ### @export "access-other-docs-lens"
            n_children = len(doc.children)
            n_inputs = len(doc.inputs)

            ### @export "access-other-docs-output-length"
            if doc.output().has_data():
                length = len(doc.output().data())
            else:
                length = len(doc.output().ordered_dict())

            ### @export "access-other-docs-finish"
            info.append("%s (%s children, %s inputs, length %s)" % (doc.key, n_children, n_inputs, length))
        s = "%s        " % os.linesep
        return s.join(info)
        ### @end

class AddNewDocument(Example):
    """
    A filter which adds an extra document to the tree.
    """
    ALIASES = ['newdoc']

    def process_text(self, input_text):
        self.add_doc("newfile.txt|processtext", "newfile")
        return "we added a new file"

class ConvertDict(Example):
    """
    Returns an ordered dict with a single element.
    """
    ALIASES = ['dict']

    def process_text_to_dict(self, input_text):
        ordered_dict = OrderedDict()
        ordered_dict['1'] = input_text
        return ordered_dict

class ExampleProcessTextMethod(Example):
    """
    Uses process_text method
    """
    ALIASES = ['processtext']

    def process_text(self, input_text):
        return "Dexy processed the text '%s'" % input_text

class ExampleProcessDictMethod(Example):
    """
    Uses process_dict method
    """
    ALIASES = ['processdict']

    def process_dict(self, input_dict):
        output_dict = OrderedDict()
        for k, v in input_dict.iteritems():
            output_dict[k] = "Dexy processed the text '%s'" % v
        return output_dict

class ExampleProcessTextToDictMethod(Example):
    """
    Uses process_text_do_dict method
    """
    ALIASES = ['processtexttodict']

    def process_text_to_dict(self, input_text):
        output_dict = OrderedDict()
        output_dict['1'] = "Dexy processed the text '%s'" % input_text
        return output_dict

class ExampleProcessMethod(Example):
    """
    A filter implementing a process method which stores raw data.
    """
    ALIASES = ['process']

    def process(self):
        output = "Dexy processed the text '%s'" % self.input().data()
        self.output().set_data(output)

class ExampleProcessMethodManualWrite(Example):
    """
    A filter implementing a process method which stores raw data by writing directly to the output file.
    """
    ALIASES = ['processmanual']

    def process(self):
        input_data = self.input().data()
        output = "Dexy processed the text '%s'" % input_data
        with open(self.output_filepath(), "wb") as f:
            f.write(output)

class ExampleProcessWithDictMethod(Example):
    """
    A filter implementing a process method which uses OrderedDict to store sectional data.
    """
    ALIASES = ['processwithdict']
    OUTPUT_DATA_TYPE = 'sectioned'

    def process(self):
        input_data = self.input().data()
        output_dict = OrderedDict()
        output_dict['1'] = "Dexy processed the text '%s'" % input_data
        self.output().set_data(output_dict)

class AbcExtension(Example):
    """
    Only outputs extension .abc
    """
    OUTPUT_EXTENSIONS = [".abc"]
    ALIASES = ['outputabc']

    def process_text(self, input_text):
        return "Dexy processed the text '%s'" % input_text

class ExampleFilterArgs(Example):
    """
    Prints out the args it receives.
    """
    ALIASES = ['filterargs']

    def process_text(self, input_text):
        result = ["Here are the arguments you passed:"]
        for k in sorted(self.args()):
            v = self.args()[k]
            result.append("%s: %s" % (k, v))
        return os.linesep.join(result)

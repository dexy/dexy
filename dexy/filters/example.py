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
    aliases = []
    NODOC = True

class KeyValueExample(Example):
    """
    Example of storing key value data.
    """
    aliases = ['keyvalueexample']

    _settings = {
            'output-data-type' : 'keyvalue',
            'output-extensions' : ['.sqlite3', '.json']
            }

    def process(self):
        assert self.output_data.state == 'ready'
        self.output_data.append("foo", "bar")
        self.output_data.save()

class AccessOtherDocuments(Example):
    """
    Example of accessing other documents.
    """
    aliases = ["others"]

    def process_text(self, input_text):
        info = []
        info.append("Here is a list of previous docs in this tree (not including %s)." % self.key)

        ### @export "access-other-docs-iterate"
        for doc in self.doc.walk_input_docs():
            assert isinstance(doc, Doc)

            ### @export "access-other-docs-lens"
            n_children = len(doc.children)
            n_inputs = len(doc.inputs)

            ### @export "access-other-docs-output-length"
            if doc.output_data().has_data():
                length = len(doc.output_data().data())
            else:
                length = len(doc.output_data().ordered_dict())

            ### @export "access-other-docs-finish"
            info.append("%s (%s children, %s inputs, length %s)" % (doc.key, n_children, n_inputs, length))
        s = "%s        " % os.linesep
        return s.join(info)
        ### @end

class AddNewDocument(Example):
    """
    A filter which adds an extra document to the tree.
    """
    aliases = ['newdoc']

    def process_text(self, input_text):
        self.add_doc("newfile.txt|processtext", "newfile")
        return "we added a new file"

class ConvertDict(Example):
    """
    Returns an ordered dict with a single element.
    """
    aliases = ['dict']

    def process_text_to_dict(self, input_text):
        ordered_dict = OrderedDict()
        ordered_dict['1'] = input_text
        return ordered_dict

class ExampleProcessTextMethod(Example):
    """
    Uses process_text method
    """
    aliases = ['processtext']

    def process_text(self, input_text):
        return "Dexy processed the text '%s'" % input_text

class ExampleProcessDictMethod(Example):
    """
    Uses process_dict method
    """
    aliases = ['processdict']

    def process_dict(self, input_dict):
        output_dict = OrderedDict()
        for k, v in input_dict.iteritems():
            output_dict[k] = "Dexy processed the text '%s'" % v
        return output_dict

class ExampleProcessTextToDictMethod(Example):
    """
    Uses process_text_do_dict method
    """
    aliases = ['processtexttodict']

    def process_text_to_dict(self, input_text):
        output_dict = OrderedDict()
        output_dict['1'] = "Dexy processed the text '%s'" % input_text
        return output_dict

class ExampleProcessMethod(Example):
    """
    A filter implementing a process method which stores raw data.
    """
    aliases = ['process']

    def process(self):
        output = "Dexy processed the text '%s'" % self.input_data
        self.output_data.set_data(output)

class ExampleProcessMethodManualWrite(Example):
    """
    A filter implementing a process method which stores raw data by writing directly to the output file.
    """
    aliases = ['processmanual']

    def process(self):
        input_data = self.input_data
        output = "Dexy processed the text '%s'" % input_data
        with open(self.output_filepath(), "wb") as f:
            f.write(output)

class ExampleProcessWithDictMethod(Example):
    """
    A filter implementing a process method which uses OrderedDict to store sectional data.
    """
    aliases = ['processwithdict']
    _settings = {
            'output-data-type' : 'sectioned'
            }

    def process(self):
        output_dict = OrderedDict()
        output_dict['1'] = "Dexy processed the text '%s'" % self.input_data
        self.output_data.set_data(output_dict)

class AbcExtension(Example):
    """
    Only outputs extension .abc
    """
    aliases = ['outputabc']
    _settings = {
            'output-extensions' : ['.abc']
            }

    def process_text(self, input_text):
        return "Dexy processed the text '%s'" % input_text

class ExampleFilterArgs(Example):
    """
    Prints out the args it receives.
    """
    aliases = ['filterargs']

    _settings = {
            "abc" : ("The abc setting.", None),
            "foo" : ("The foo setting.", None),
            }

    def process_text(self, input_text):
        # Filter Settings
        result = ["Here are the filter settings:"]
        for k in sorted(self.setting_values()):
            v = self.setting_values()[k]
            result.append("  %s: %s" % (k, v))

        # Doc args
        result.append("Here are the document args:")
        for k in sorted(self.doc.args):
            v = self.doc.args[k]
            result.append("  %s: %s" % (k, v))

        return os.linesep.join(result)

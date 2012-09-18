import dexy.plugin
import dexy.utils
import dexy.doc
import dexy.exceptions
import inspect

class FilterException(Exception):
    pass

class Filter:
    __metaclass__ = dexy.plugin.PluginMeta

    ALIASES = ['dexy']
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_DATA_TYPE = 'generic'
    OUTPUT_EXTENSIONS = [".*"]
    TAGS = []
    PRESERVE_PRIOR_DATA_CLASS = False

    @classmethod
    def is_active(klass):
        return True

    @classmethod
    def inactive_because_missing(klass):
        if hasattr(klass, 'executables'):
            return klass.executables()
        elif hasattr(klass, 'IMPORTS'):
            return klass.IMPORTS

    def args(self):
        return self.artifact.filter_args()

    def arg_value(self, key, default=None):
        return self.args().get(key, default)

    @classmethod
    def data_class_alias(klass, file_ext):
        return klass.OUTPUT_DATA_TYPE

    def process(self):
        pass

    def add_doc(self, doc_name, doc_contents=None):
        additional_doc_filters = self.args().get("additional_doc_filters")

        if additional_doc_filters:
            doc_key = "%s|%s" % (doc_name, additional_doc_filters)
        else:
            doc_key = doc_name

        doc = dexy.doc.Doc(doc_key, contents=doc_contents)
        self.artifact.add_doc(doc)
        return doc

    def input(self):
        return self.artifact.input_data

    def input_data(self):
        return self.input().data()

    def result(self):
        return self.artifact.output_data

    def prior(self):
        return self.artifact.prior.output_data

    def output_filepath(self):
        return self.result().storage.data_file()

    def processed(self):
        for doc in self.artifact.doc.completed_child_docs():
            yield doc

class DexyFilter(Filter):
    ALIASES = ['dexy']

    @classmethod
    def data_class_alias(klass, file_ext):
        if hasattr(klass, 'process_dict'):
            return 'sectioned'
        elif hasattr(klass, 'process_text_to_dict'):
            return 'sectioned'
        else:
            return klass.OUTPUT_DATA_TYPE

    def process(self):
        if hasattr(self, "process_text_to_dict"):
            output = self.process_text_to_dict(self.input().as_text())
            self.result().set_data(output)

        elif hasattr(self, "process_dict"):
            output = self.process_dict(self.input().as_sectioned())
            self.result().set_data(output)

        elif hasattr(self, "process_text"):
            output = self.process_text(self.input().as_text())
            self.result().set_data(output)

        else:
            self.result().copy_from_file(self.input().storage.data_file())

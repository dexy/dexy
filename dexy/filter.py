import dexy.plugin
import dexy.utils
import dexy.doc
import dexy.exceptions

class FilterException(Exception):
    pass

class Filter:
    __metaclass__ = dexy.plugin.PluginMeta

    ALIASES = ['dexy']
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_DATA_TYPE = 'generic'
    OUTPUT_EXTENSIONS = [".*"]
    TAGS = []

    @classmethod
    def is_active(self):
        return True

    def args(self):
        return self.artifact.filter_args()

    def arg_value(self, key, default=None):
        return self.args().get(key, default)

    @classmethod
    def data_class_alias(klass):
        return klass.OUTPUT_DATA_TYPE

    def process(self):
        pass

    def add_doc(self, doc_name, doc_contents):
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
        """
        Returns an iterator of previously processed documents in this tree.
        """
        for doc in self.artifact.doc.completed_child_docs():
            yield doc

class DexyFilter(Filter):
    ALIASES = ['dexy']

    @classmethod
    def data_class_alias(klass):
        if hasattr(klass, 'process_dict'):
            return 'sectioned'
        elif hasattr(klass, 'process_text_to_dict'):
            return 'sectioned'
        else:
            return klass.OUTPUT_DATA_TYPE

    def process(self):
        """
        This is the method that does the "work" of the handler, that is
        filtering the input and producing output. This method can be overridden
        in a subclass, or one of the convenience methods named below can be
        implemented and will be delegated to.
        """

        if not self.input().has_data():
            raise Exception("no data!")

        if hasattr(self, "process_text_to_dict"):
            if not self.result().__class__.__name__ == "SectionedData":
                raise dexy.exceptions.InternalDexyProblem("filter implementing a process_text_to_dict method must specify OUTPUT_DATA_TYPE = 'sectioned'")

            output = self.process_text_to_dict(self.input().as_text())
            self.result().set_data(output)

            method_used = "process_text_to_dict"

        elif hasattr(self, "process_dict"):
            output = self.process_dict(self.input().as_sectioned())
            self.result().set_data(output)

            method_used = "process_dict"

        elif hasattr(self, "process_text"):
            output = self.process_text(self.input().as_text())
            self.result().set_data(output)

            method_used = "process_text"

        else:
            self.result().copy_from_file(self.artifact.input_data.storage.data_file())

            method_used = "process"

        self.log.debug("Used method %s of default process method." % method_used)
        return method_used

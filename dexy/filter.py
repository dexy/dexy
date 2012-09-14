import dexy.plugin
import dexy.utils
import dexy.doc
import dexy.exceptions
import os

class FilterException(Exception):
    pass

class Filter:
    __metaclass__ = dexy.plugin.PluginMeta

    ALIASES = ['dexy']
    DEFAULT_INPUT_SEARCH_FILTERS = []
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    OUTPUT_DATA_TYPE = 'generic'
    TAGS = [] # Descriptive keywords about the filter.
    VERSION_COMMAND = None
    WINDOWS_VERSION_COMMAND = None

    @classmethod
    def version(klass):
        pass

    @classmethod
    def data_class_alias(klass):
        if hasattr(klass, 'process_dict'):
            return 'sectioned'
        elif hasattr(klass, 'process_text_to_dict'):
            return 'sectioned'
        else:
            return klass.OUTPUT_DATA_TYPE

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

    @classmethod
    def output_file_extension(klass, ext, key, next_input_extensions=None):
        out_ext = None

        if set([ext, ".*"]).isdisjoint(set(klass.INPUT_EXTENSIONS)):
            exception_text = """Error in %s for %s. Extension %s is not supported.
            Supported extensions are: %s""" % (klass.__name__, key, ext, ', '.join(klass.INPUT_EXTENSIONS))
            raise Exception(exception_text)

        if ".*" in klass.OUTPUT_EXTENSIONS:
            out_ext = ext
        else:
            if next_input_extensions and not ".*" in next_input_extensions:
                for e in klass.OUTPUT_EXTENSIONS:
                    if e in next_input_extensions:
                        out_ext = e

                if not out_ext:
                  err_str = "unable to find one of %s in %s for %s"
                  prev_out = ", ".join(klass.OUTPUT_EXTENSIONS)
                  next_in = ", ".join(next_input_extensions)
                  err_str = err_str % (prev_out, next_in, klass.__name__)
                  raise dexy.exceptions.UserFeedback(err_str)
            else:
                out_ext = klass.OUTPUT_EXTENSIONS[0]
        return out_ext

    @classmethod
    def is_active(self):
        """Allow filters to be disabled."""
        return True

    def find_closest_parent(self, param_name):
        self.log.debug("In find_closest_parent for %s" % self.artifact.key)
        inputs = self.artifact.inputs()

        search_key_specified = self.artifact.args.has_key(param_name)

        if search_key_specified:
            search_key = self.artifact.args[param_name]
        else:
            # nothing specified, look for the default pattern
            search_key = "_%s%s" % (param_name, self.artifact.ext)

        self.log.debug("Using search key %s" % search_key)
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
                for pattern in self.DEFAULT_INPUT_SEARCH_FILTERS:
                    if pattern:
                        try_key = "%s|%s" % (search_key_in_dir, pattern)
                    if inputs.has_key(try_key):
                        doc = inputs[try_key]
                        break

            if doc:
                break

        if not doc:
            raise dexy.exceptions.UserFeedback("Can't find any inputs!")

        self.log.debug("selected %s" % doc.key)
        return doc

    def args(self):
        if not hasattr(self, '_args'):
            self._args = self.artifact.filter_args()
        return self._args

    def arg_value(self, key, default=None):
        return self.args().get(key, default)

    ### @export "processed"
    def processed(self):
        """
        Returns an iterator of previously processed documents in this tree.
        """
        for doc in self.artifact.doc.completed_child_docs():
            yield doc

    ### @end
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

class DexyFilter(Filter):
    ALIASES = ['dexy']

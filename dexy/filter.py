import dexy.plugin
import dexy.utils
import dexy.doc
import dexy.exceptions
import os
import platform
import subprocess

class FilterException(Exception):
    pass

class Filter:
    """
    This is the main DexyFilter class. To make custom filters you should
    subclass this and override the process() method. You may also want to
    specify INPUT_EXTENSIONS and OUTPUT_EXTENSIONS. You must define unique
    ALIASES in each handler, use java-style namespacing, e.g. com.abc.alias
    """
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
    def output_data_class(klass):
        output_data_type = klass.OUTPUT_DATA_TYPE

        if hasattr(klass, 'process_dict'):
            output_data_type = 'sectioned'
        elif hasattr(klass, 'process_text_to_dict'):
            output_data_type = 'sectioned'

        return dexy.data.Data.aliases[output_data_type]

    def add_doc(self, doc_name, doc_contents):
        additional_doc_filters = self.args().get("additional_doc_filters")

        if additional_doc_filters:
            doc_key = "%s|%s" % (doc_name, additional_doc_filters)
        else:
            doc_key = doc_name

        doc = dexy.doc.Doc(doc_key, contents=doc_contents)
        self.artifact.add_doc(doc)
        return doc

    def inputs(self):
        pass

    def input_data(self):
        return self.artifact.input_data

    def output_filepath(self):
        return self.artifact.output_data.storage.data_file()

    @classmethod
    def executables(self):
        """
        Returns list of executables defined for this filter, in order of preference. If empty, no executable is required.
        """
        executables = []

        if platform.system() == 'Windows' and hasattr(self, 'WINDOWS_EXECUTABLE'):
            executables.append(self.WINDOWS_EXECUTABLE)
        else:
            if hasattr(self, 'EXECUTABLE'):
                executables.append(self.EXECUTABLE)
            elif hasattr(self, 'EXECUTABLES'):
                executables += self.EXECUTABLES

        return executables

    @classmethod
    def executable(self):
        """
        Returns the executable to use. Looks in WINDOWS_EXECUTABLE if on
        windows. Otherwise looks at EXECUTABLE or EXECUTABLES. If specified
        executables are not detected on the system, returns None.
        """
        for exe in self.executables():
            if exe:
                cmd = exe.split()[0] # remove any --arguments
                if dexy.utils.command_exists(cmd):
                    return exe

    @classmethod
    def version_command(klass):
        if platform.system() == 'Windows':
            return klass.WINDOWS_VERSION_COMMAND or klass.VERSION_COMMAND
        else:
            return klass.VERSION_COMMAND

    @classmethod
    def version(klass, log=None):
        vc = klass.version_command()

        if vc:
            # TODO make custom env available here...
            proc = subprocess.Popen(vc, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            stdout, stderr = proc.communicate()

            if proc.returncode > 0:
                err_msg = """An error occurred running %s""" % vc
                if log:
                    log.debug(err_msg)
                return False
            else:
                return stdout.strip().split("\n")[0]
        else:
            return None

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

        if not self.artifact.input_data.has_data():
            raise Exception("no data!")

        if hasattr(self, "process_text_to_dict"):
            if not self.artifact.output_data.__class__.__name__ == "SectionedData":
                raise dexy.exceptions.InternalDexyProblem("filter implementing a process_text_to_dict method must specify OUTPUT_DATA_TYPE = 'sectioned'")

            output = self.process_text_to_dict(self.artifact.input_data.as_text())
            self.artifact.output_data.set_data(output)

            method_used = "process_text_to_dict"

        elif hasattr(self, "process_dict"):
            output = self.process_dict(self.artifact.input_data.as_sectioned())
            self.artifact.output_data.set_data(output)

            method_used = "process_dict"

        elif hasattr(self, "process_text"):
            output = self.process_text(self.artifact.input_data.as_text())
            self.artifact.output_data.set_data(output)

            method_used = "process_text"

        else:
            self.artifact.output_data.copy_from_file(self.artifact.input_data.storage.data_file())

            method_used = "process"

        self.log.debug("Used method %s of default process method." % method_used)
        return method_used

class DexyFilter(Filter):
    ALIASES = ['dexy']

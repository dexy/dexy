try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import inspect
import logging
import os
import platform
import subprocess
import time

class DexyHandler(object):
    """
    This is the main DexyHandler class. To make custom handlers you should
    subclass this and override the process() method. You may also want to
    specify INPUT_EXTENSIONS and OUTPUT_EXTENSIONS. You must define unique
    ALIASES in each handler, use java-style namespacing, e.g. com.abc.alias
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['dexy']
    BINARY = False
    FINAL = False

    @classmethod
    def executable(self):
        """A standard way of specifying a command line executable. For usage
        example see stdout filter. This does not need to be used, and is not
        relevant for many filters, but is intended to allow introspection for
        those which do use it."""
        if platform.system() == 'Windows':
            if hasattr(self, 'WINDOWS_EXECUTABLE'):
                return self.WINDOWS_EXECUTABLE
        else:
            if hasattr(self, 'EXECUTABLE'):
                return self.EXECUTABLE

    @classmethod
    def version_command(self):
        if platform.system() == 'Windows':
            if hasattr(self, 'WINDOWS_VERSION'):
                return self.WINDOWS_VERSION
        else:
            if hasattr(self, 'VERSION'):
                return self.VERSION

    @classmethod
    def version(self):
        vc = self.version_command()
        if vc:
            proc = subprocess.Popen(vc, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            output, e = proc.communicate()

            if proc.returncode > 0:
                raise Exception("An error occurred running %s" % vc)
            else:
                return output
        else:
            return "unspecified"

    @classmethod
    def output_file_extension(klass, ext, key, next_handler_class):
        out_ext = None

        if set([ext, ".*"]).isdisjoint(set(klass.INPUT_EXTENSIONS)):
            exception_text = """Error in %s for %s. Extension %s is not supported.
            Supported extensions are: %s""" % (klass.__name__, key, ext, ', '.join(klass.INPUT_EXTENSIONS))
            raise Exception(exception_text)

        if ".*" in klass.OUTPUT_EXTENSIONS:
            out_ext = ext
        else:
            if next_handler_class and not ".*" in next_handler_class.INPUT_EXTENSIONS:
                for e in klass.OUTPUT_EXTENSIONS:
                    if e in next_handler_class.INPUT_EXTENSIONS:
                        out_ext = e

                if not out_ext:
                  err_str = "unable to find one of %s in %s for %s %s"
                  prev_out = ", ".join(klass.OUTPUT_EXTENSIONS)
                  next_in = ", ".join(next_handler_class.INPUT_EXTENSIONS)
                  next_handler_name = next_handler_class.__name__
                  err_str = err_str % (prev_out, next_in, next_handler_name, key)
                  raise Exception(err_str)
            else:
                out_ext = klass.OUTPUT_EXTENSIONS[0]

        return out_ext

    @classmethod
    def setup(klass, doc, artifact_key, previous_artifact, next_handler_class):
        h = klass()
        h.doc = doc
        h.log = doc.log

        artifact_class = previous_artifact.__class__

        artifact = artifact_class.setup(doc, artifact_key, previous_artifact)
        artifact.handler = h
        artifact.handler_source = inspect.getsource(klass)
        artifact.handler_version = klass.version()
        if os.path.basename(artifact.doc.name).startswith("_"):
            artifact.final = False
            previous_artifact.final = False
        elif not artifact.final:
            artifact.final = klass.FINAL
        artifact.binary = klass.BINARY

        if next_handler_class:
            artifact.next_handler_name = next_handler_class.__name__

        artifact.ext = klass.output_file_extension(
            previous_artifact.ext, doc.key(), next_handler_class)

        artifact.set_hashstring()

        h.ext = artifact.ext
        h.artifact = artifact
        return h

    def process(self):
        """This is the method that does the "work" of the handler, that is
        filtering the input and producing output. This method can be overridden
        in a subclass, or one of the convenience methods named below can be
        implemented and will be delegated to. If more than 1 convenience method
        is implemented then an exception will be raised."""
        method_used = None

        if hasattr(self, "process_text"):
            if method_used:
                raise Exception("%s has already been called" % method_used)
            if len(self.artifact.input_data_dict.keys()) > 1:
                raise Exception("""You have passed input with multiple sections
                                to the %s handler. This handler does not preserve
                                sections. Either remove sectioning or add a call
                                to the join filter before this handler.""")
            input_text = self.artifact.input_text()
            output_text = self.process_text(input_text)
            self.artifact.data_dict['1'] = output_text
            method_used = "process_text"

        if hasattr(self, "process_dict"):
            if method_used:
                raise Exception("%s has already been called" % method_used)
            input_dict = self.artifact.input_data_dict
            output_dict = self.process_dict(input_dict)
            self.artifact.data_dict = output_dict
            method_used = "process_dict"

        if hasattr(self, "process_text_to_dict"):
            if method_used:
                raise Exception("%s has already been called" % method_used)
            input_text = self.artifact.input_text()
            output_dict = self.process_text_to_dict(input_text)
            self.artifact.data_dict = output_dict
            method_used = "process_text_to_dict"

        if not method_used:
            # This code implements the neutral 'dexy' handler.
            self.artifact.data_dict = self.artifact.input_data_dict
            method_used = "process"

        return method_used

    def set_input_text(self, input_text):
        if hasattr(self, 'artifact'):
            raise Exception("already have an artifact!")
        self.artifact = self.doc.artifact_class()
        self.artifact.input_data_dict = {'1' : input_text}
        self.artifact.data_dict = OrderedDict()

    def generate_artifact(self):
        self.artifact.start_time = time.time()
        if self.artifact.is_cached():
            self.artifact.method = 'cached'
            if not self.artifact.is_loaded():
                self.artifact.load()
        else:
            self.artifact.method = 'generated'
            self.process()
#            self.artifact.binary = self.BINARY
#            if not hasattr(self.artifact, 'final') or not self.artifact.final:
#                self.artifact.final = self.FINAL
            self.artifact.save()

        self.artifact.finish_time = time.time()
        return self.artifact


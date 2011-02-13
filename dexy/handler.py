try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from dexy.artifact import Artifact
import dexy.logger
import time
import subprocess
import platform

### @export "class"
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

### @export "executable"
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

### @export "version_command"
    @classmethod
    def version_command(self):
        if platform.system() == 'Windows':
            if hasattr(self, 'WINDOWS_VERSION'):
                return self.WINDOWS_VERSION
        else:
            if hasattr(self, 'VERSION'):
                return self.VERSION

### @export "version"
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

### @export "setup"
    @classmethod
    def setup(klass, doc, artifact_key, previous_artifact = None, next_handler = None):
        h = klass()
        h.doc = doc
        h.artifact = Artifact.setup(doc, artifact_key, h, previous_artifact)
        if next_handler:
            h.artifact.next_handler_name = next_handler.__name__

        # Determine file extension.
        ext = previous_artifact.ext
        if set([ext, ".*"]).isdisjoint(set(h.INPUT_EXTENSIONS)):
            exception_text = """Error in %s for %s. Extension %s is not supported.
            Supported extensions are: %s""" % (klass.__name__, doc.key(), ext, ', '.join(h.INPUT_EXTENSIONS))
            raise Exception(exception_text)
        h.ext = ext
        
        if ".*" in h.OUTPUT_EXTENSIONS:
            h.artifact.ext = ext
        else:
            if next_handler and not ".*" in next_handler.INPUT_EXTENSIONS:
                for e in h.OUTPUT_EXTENSIONS:
                    if e in next_handler.INPUT_EXTENSIONS:
                        h.artifact.ext = e
                
                if not hasattr(h.artifact, 'ext'):
                  err_str = "unable to find one of %s in %s for %s %s"
                  err_str = err_str % (", ".join(h.OUTPUT_EXTENSIONS), ", ".join(next_handler.INPUT_EXTENSIONS), next_handler.__name__, doc.key())
                  raise Exception(err_str)
            else:
                h.artifact.ext = h.OUTPUT_EXTENSIONS[0]
    
        h.artifact.set_hashstring()
        if hasattr(dexy.logger.log, 'getChild'):
            # This adds a nice namespacing, only available in Python 2.7
            h.log = dexy.logger.log.getChild(klass.__name__)
        else:
            h.log = dexy.logger.log
        return h

### @export "process"
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

### @export "set-input-text"
    def set_input_text(self, input_text):
        if hasattr(self, 'artifact'):
            raise Exception("already have an artifact!")
        self.artifact = Artifact()
        self.artifact.input_data_dict = {'1' : input_text}
        self.artifact.data_dict = OrderedDict()

### @export "generate"
    def generate(self):
        self.artifact.generate()

### @export "generate-artifact"
    def generate_artifact(self): 
        start = time.time()

        if self.artifact.dj_file_exists():
            method = 'cached'
            self.artifact.load_dj()
        else:
            method = 'generated'
            self.process()
            self.generate()

        finish = time.time()
        self.log_time(start, finish, method)

        return self.artifact

### @export "log-time"
    def log_time(self, start, finish, method):
        doc = self.artifact.doc

        elapsed = finish - start
        row = [
            self.artifact.key,
            self.artifact.hashstring,
            doc.key(),
            self.__class__.__name__,
            method,
            start, 
            finish, 
            elapsed
        ]
        self.artifact.doc.controller.log_time(row)

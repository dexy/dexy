import platform
import subprocess
from dexy.utils import command_exists

class DexyFilter(object):
    """
    This is the main DexyFilter class. To make custom filters you should
    subclass this and override the process() method. You may also want to
    specify INPUT_EXTENSIONS and OUTPUT_EXTENSIONS. You must define unique
    ALIASES in each handler, use java-style namespacing, e.g. com.abc.alias
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['dexy']
    BINARY = False
    FINAL = None

    @classmethod
    def executable(self):
        """A standard way of specifying a command line executable. For usage
        example see stdout filter. This does not need to be used, and is not
        relevant for many filters, but is intended to allow introspection for
        those which do use it."""
        if platform.system() == 'Windows' and hasattr(self, 'WINDOWS_EXECUTABLE'):
            return self.WINDOWS_EXECUTABLE
        else:
            if hasattr(self, 'EXECUTABLE'):
                return self.EXECUTABLE
            elif hasattr(self, 'EXECUTABLES'):
                # Allows you to specify multiple options for an executable and,
                # at runtime, use whichever one is present on the system. The
                # first listed executable to be found is the one used.
                return self.find_present_executable()


    @classmethod
    def find_present_executable(klass):
        # determine which executable to use
        for exe in klass.EXECUTABLES:
            if klass.executable_present(exe):
                return exe
                break
        return None

    @classmethod
    def executable_present(klass, exe=None):
        """Determine whether the specified executable is available."""
        if not exe:
            exe = klass.executable()

        if exe:
            cmd = exe.split()[0] # remove any --arguments
            return command_exists(cmd)
        else:
            # why true? because there's nothing to run?
            return True

    @classmethod
    def version_command(self):
        if platform.system() == 'Windows':
            if hasattr(self, 'WINDOWS_VERSION'):
                return self.WINDOWS_VERSION
        else:
            if hasattr(self, 'VERSION'):
                return self.VERSION

    @classmethod
    def version(self, log=None):
        vc = self.version_command()
        if vc:
            # TODO make custom env available here...
            proc = subprocess.Popen(vc, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            output, e = proc.communicate()

            if proc.returncode > 0:
                err_msg = """An error occurred running %s, this may be due to a path issue""" % vc
                if log:
                    log.debug(err_msg)
                else:
                    print err_msg
                return "error"
            else:
                return output
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
                  err_str = err_str % (prev_out, next_in, key)
                  raise Exception(err_str)
            else:
                out_ext = klass.OUTPUT_EXTENSIONS[0]
        return out_ext

    @classmethod
    def enabled(self):
        """Allow filters to be disabled."""
        return True

    def handle_subprocess_proc_return(self, returncode, stderr):
        if returncode is None:
            raise Exception("no return code, proc not finished!")
        elif returncode != 0:
            if self.artifact.dexy_args.ignore_errors:
                self.artifact.log.warn(stderr)
            else:
                print stderr
                raise Exception("""proc returned nonzero status code! if you don't
want dexy to raise errors on failed scripts then pass the --ignore-errors option""")

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


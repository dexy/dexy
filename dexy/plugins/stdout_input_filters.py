from dexy.plugins.process_filters import SubprocessInputFilter
import dexy.exceptions

class ApplySed(SubprocessInputFilter):
    """
    A filter which runs on a text file and applies a sed file (specified as an
    input) to that text file. Output is the modified text file.
    """
    ALIASES = ['used']
    EXECUTABLES = ['gsed', 'sed']
    OUTPUT_DATA_TYPE = 'generic'

    def process(self):
        for doc in self.artifact.doc.node.walk_input_docs():
            if doc.output().ext == ".sed":
                command = "%s -f %s" % (self.executable(), doc.output().name)

        if not command:
            raise dexy.exceptions.UserFeedback("A .sed file must be passed as an input to %s" % self.artifact.key)

        proc, stdout = self.run_command(command, self.setup_env(), unicode(self.input()))
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.output().set_data(stdout)

class Sed(SubprocessInputFilter):
    """
    A filter which runs on a sed file and applies this sed file to text files
    passed as inputs. Output is a dict of filenames and output text from each
    input file. If there is only a single input file, output is a dict of
    section names and output text from each section in that input file.
    """
    ALIASES = ['sed']
    EXECUTABLES = ['gsed', 'sed']
    INPUT_EXTENSIONS = [".sed"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'sed --version'

    def command_string(self):
        return "%s -f %s" % (self.executable(), self.input_filename())

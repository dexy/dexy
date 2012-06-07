from dexy.filters.process_filters import SubprocessStdoutInputFilter
from dexy.filters.process_filters import SubprocessStdoutInputFileFilter
import os

class ApplySedSubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    ALIASES = ['used']
    EXECUTABLES = ['gsed', 'sed']

    def process(self):
        for artifact in self.artifact.inputs().values():
            if artifact.name.endswith(".sed"):
                command = "%s -f %s" % (self.executable(), artifact.canonical_basename())

        if not command:
            raise UserFeedback("A .sed file must be passed as an input to %s" % self.artifact.key)

        proc, stdout = self.run_command(command, self.setup_env(), self.artifact.input_text())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.artifact.data_dict['1'] = stdout

class SedSubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    ALIASES = ['sed']
    EXECUTABLES = ['gsed', 'sed']
    INPUT_EXTENSIONS = [".sed"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'sed --version'

    def command_string_stdout(self):
        wf = os.path.basename(self.artifact.previous_canonical_filename)
        return "%s -f %s" % (self.executable(), wf)

class RubySubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    EXECUTABLE = 'ruby'
    VERSION_COMMAND = 'ruby --version'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rbinput', 'irboutinput']

class PythonSubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    ALIASES = ['pyinput']
    EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'python --version'

class BashSubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    ALIASES = ['shinput']
    EXECUTABLE = 'bash -e'
    INPUT_EXTENSIONS = [".sh", ".bash", ".txt", ""]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'bash --version'

class RegetronSubprocessStdoutInputFileFilter(SubprocessStdoutInputFileFilter):
    ALIASES = ['regetron']
    EXECUTABLE = 'regetron'
    INPUT_EXTENSIONS = [".regex"]
    OUTPUT_EXTENSIONS = [".txt"]

    def command_string_stdout_input(self, input_artifact):
        wf = os.path.basename(self.artifact.previous_canonical_filename)
        input_file = input_artifact.canonical_basename()
        return "%s %s %s" % (self.executable(), input_file, wf)


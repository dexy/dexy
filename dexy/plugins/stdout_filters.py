from dexy.plugins.process_filters import SubprocessStdoutFilter

class PythonSubprocessStdoutFilter(SubprocessStdoutFilter):
    ALIASES = ['py', 'pyout']
    EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'python --version'

class BashSubprocessStdoutFilter(SubprocessStdoutFilter):
    ALIASES = ['sh', 'bash']
    EXECUTABLE = 'bash -e'
    INPUT_EXTENSIONS = [".sh", ".bash", ".txt", ""]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'bash --version'

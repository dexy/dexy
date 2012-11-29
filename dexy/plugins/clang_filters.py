from dexy.plugins.process_filters import SubprocessCompileFilter
from dexy.plugins.process_filters import SubprocessCompileInputFilter

class ClangSubprocessCompileFilter(SubprocessCompileFilter):
    """
    Compile code using clang and run.
    """
    ALIASES = ['clang']
    EXECUTABLE = "clang"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "clang --version"

class ClangSubprocessCompileInputFilter(SubprocessCompileInputFilter):
    """
    Compile code using clang and run with input.
    """
    ALIASES = ['clanginput']
    EXECUTABLE = "clang"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "clang --version"

class CSubprocessCompileFilter(SubprocessCompileFilter):
    """
    Compile code using gcc and run.
    """
    ALIASES = ['c', 'gcc']
    EXECUTABLE = "gcc"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "gcc --version"

class CFussySubprocessCompileFilter(SubprocessCompileFilter):
    """
    Compile code using gcc and run, raising an error if compiled code returns nonzero exit.
    """
    ALIASES = ['cfussy']
    EXECUTABLE = "gcc"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "gcc --version"
    CHECK_RETURN_CODE = True

class CSubprocessCompileInputFilter(SubprocessCompileInputFilter):
    """
    Compile code using gcc and run with input.
    """
    ALIASES = ['cinput']
    EXECUTABLE = "gcc"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "gcc --version"

class CppSubprocessCompileFilter(SubprocessCompileFilter):
    """
    Compile c++ code using cpp and run.
    """
    ALIASES = ['cpp']
    EXECUTABLE ="c++"
    INPUT_EXTENSIONS = [".cpp"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "c++ --version"

class CppSubprocessCompileInputFilter(SubprocessCompileInputFilter):
    """
    Compile c++ code using cpp and run with input.
    """
    ALIASES = ['cppinput']
    EXECUTABLE ="c++"
    INPUT_EXTENSIONS = [".cpp"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "c++ --version"

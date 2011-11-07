from dexy.filters.process_filters import SubprocessCompileFilter
from dexy.filters.process_filters import SubprocessCompileInputFilter

class ClangSubprocessCompileFilter(SubprocessCompileFilter):
    ALIASES = ['clang']
    EXECUTABLE = "clang"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "clang --version"

class ClangSubprocessCompileInputFilter(SubprocessCompileInputFilter):
    ALIASES = ['clanginput']
    EXECUTABLE = "clang"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "clang --version"

class CSubprocessCompileFilter(SubprocessCompileFilter):
    ALIASES = ['c', 'gcc']
    EXECUTABLE = "gcc"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "gcc --version"

class CFussySubprocessCompileFilter(SubprocessCompileFilter):
    ALIASES = ['cfussy']
    EXECUTABLE = "gcc"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "gcc --version"
    CHECK_RETURN_CODE = True

class CSubprocessCompileInputFilter(SubprocessCompileInputFilter):
    ALIASES = ['cinput']
    EXECUTABLE = "gcc"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "gcc --version"

class CppSubprocessCompileFilter(SubprocessCompileFilter):
    ALIASES = ['cpp']
    EXECUTABLE ="c++"
    INPUT_EXTENSIONS = [".cpp"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "c++ --version"

class CppSubprocessCompileInputFilter(SubprocessCompileInputFilter):
    ALIASES = ['cppinput']
    EXECUTABLE ="c++"
    INPUT_EXTENSIONS = [".cpp"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "c++ --version"

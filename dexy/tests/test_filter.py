from dexy.dexy_filter import DexyFilter
from dexy.filters.process_filters import SubprocessStdoutFilter
from dexy.tests.utils import run_dexy
from dexy.tests.utils import set_filter_list

def test_filter():
    DexyFilter()

class NonexistentExecutableFilter(SubprocessStdoutFilter):
    EXECUTABLE = 'doesnotexist'

class NonexistentExecutablesFilter(SubprocessStdoutFilter):
    EXECUTABLES = ['doesnotexist']

class FirstExecutableNonexistent(SubprocessStdoutFilter):
    EXECUTABLES = ['doesnotexist', 'bash']

def test_executable_detection():
    assert not NonexistentExecutableFilter.executable()
    assert not NonexistentExecutablesFilter.executable()
    assert FirstExecutableNonexistent.executable() == 'bash'

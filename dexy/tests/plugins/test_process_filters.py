from dexy.plugins.process_filters import SubprocessFilter

class NotPresentExecutable(SubprocessFilter):
    EXECUTABLE = 'notreal'

def test_not_present_executable():
    assert 'notreal' in NotPresentExecutable.executables()
    assert not NotPresentExecutable.executable()

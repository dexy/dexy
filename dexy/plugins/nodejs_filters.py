from dexy.plugins.process_filters import SubprocessFilter
from dexy.plugins.process_filters import SubprocessStdoutFilter
import os

class NodeJsStdoutFilter(SubprocessStdoutFilter):
    """
    Runs scripts using node js.
    """
    ADD_NEW_FILES = True
    ALIASES = ['nodejs']
    EXECUTABLE = 'node'
    INPUT_EXTENSIONS = ['.js', '.txt']
    OUTPUT_EXTENSIONS = ['.txt']
    VERSION_COMMAND = 'node --version'


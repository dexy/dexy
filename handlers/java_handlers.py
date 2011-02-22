from dexy.handler import DexyHandler
import pexpect
import time
import handlers.pexpect_handlers
import handlers.stdout_handlers

### @export "jruby-handler"
class JrubyHandler(handlers.stdout_handlers.ProcessStdoutHandler):
    VERSION = "/usr/bin/env jruby --version"
    EXECUTABLE = "/usr/bin/env jruby"
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jruby']

### @export "jirb-handler"
class JirbHandler(handlers.pexpect_handlers.ProcessLinewiseInteractiveHandler):
    VERSION = "/usr/bin/env jirb --version"
    EXECUTABLE = "/usr/bin/env jirb --prompt-mode simple"
    INPUT_EXTENSIONS = [".rb"]
    PROMPT = ">>|\?>"
    OUTPUT_EXTENSIONS = [".rbcon"]
    ALIASES = ['jirb']

### @export "jython-handler"
class JythonHandler(handlers.stdout_handlers.ProcessStdoutHandler):
    VERSION = "/usr/bin/env jython --version"
    EXECUTABLE = "/usr/bin/env jython"
    INPUT_EXTENSIONS = [".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jython']

### @export "jython-interactive-handler"
class JythonInteractiveHandler(handlers.pexpect_handlers.ProcessLinewiseInteractiveHandler):
    VERSION = "/usr/bin/env jython --version"
    EXECUTABLE = "/usr/bin/env jython -i"
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".pycon"]
    ALIASES = ['jythoni']


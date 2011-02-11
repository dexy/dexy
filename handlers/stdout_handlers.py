try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from dexy.handler import DexyHandler

import os
import subprocess
import platform

### @export "stdout"
class ProcessStdoutHandler(DexyHandler):
    """
    Intended for use with command line processes where your only interest is in
    the contents of stdout.
    """
    EXECUTABLE = '/usr/bin/env python'
    WINDOWS_EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['py', 'python', 'pyout']

    def executable(self):
        if platform.system() == 'Windows':
            return WINDOWS_EXECUTABLE
        else:
            return EXECUTABLE
    
    def process(self):
        self.artifact.generate_workfile()
        if self.artifact.doc.args.has_key('timeout'):
            timeout = self.artifact.doc.args['timeout']
        else:
            timeout = None
        command = "%s %s" % (self.executable(), self.artifact.work_filename(False))
        cla = self.artifact.command_line_args()
        if cla:
            command = "%s %s" % (command, cla)
        self.log.debug(command)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.wait()
        self.artifact.data_dict['1'] = proc.stdout
        if proc.returncode != 0:
            if self.artifact.doc.args.has_key('raiseerrors'):
                raise "return code not 0!"
            else:
                self.log.warn("an error occurred:\n%s" % proc.stderr)

### @export "bash"
class BashHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env bash'
    INPUT_EXTENSIONS = [".sh", ".bash", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['bash']

### @export "php"
class PhpHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env php'
    INPUT_EXTENSIONS = [".php"]
    OUTPUT_EXTENSIONS = [".html", ".txt"]
    ALIASES = ['php']

### @export "escript"
class EscriptHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env escript'
    INPUT_EXTENSIONS = [".erl"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['escript']

### @export "luaout"
class LuaStdoutHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env lua'
    VERSION = '/usr/bin/env lua -v'
    INPUT_EXTENSIONS = ['.lua']
    OUTPUT_EXTENSIONS = ['.txt']
    ALIASES = ['luaout']

### @export "redcloth"
class RedclothHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env redcloth'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['redcloth', 'textile']

### @export "redclothl"
class RedclothLatexHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env redcloth -o latex'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['redclothl', 'latextile']

### @export "rst2html"
class Rst2HtmlHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env rst2html.py'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['rst2html']

### @export "rst2latex"
class Rst2LatexHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env rst2latex.py'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2latex']

### @export "rst2beamer"
class Rst2BeamerHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env rst2beamer'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2beamer']

### @export "sloccount"
class SloccountHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env sloccount'
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['sloc', 'sloccount']

### @export "rb"
class RubyStdoutHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env ruby'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rb']



from dexy.dexy_filter import DexyFilter
import os
import subprocess

class ProcessStdoutFilter(DexyFilter):
    """
    Runs python script and returns STDOUT.
    """
    EXECUTABLE = 'python'
    VERSION = 'python --version'
    WINDOWS_EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['py', 'python', 'pyout']

    def process(self):
        # allow running code from different directory
        cwd = self.artifact.artifacts_dir
        if self.artifact.args.has_key('cwd'):
            cwd = os.path.join(cwd, self.artifact.args['cwd'])
            print "running from", os.path.abspath(cwd)

        self.artifact.generate_workfile()
        wf = os.path.abspath(os.path.join(self.artifact.artifacts_dir,
                                          self.artifact.work_filename()))

        if hasattr(self, 'instance_executable'):
            command = "%s %s" % (self.instance_executable(), wf)
        else:
            command = "%s %s" % (self.executable(), wf)

        cla = self.artifact.command_line_args()
        if cla:
            command = "%s %s" % (command, cla)

        if self.artifact.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.args['env'])
        else:
            env = None

        self.artifact.log.debug(command)

        proc = subprocess.Popen(command, shell=True,
                                cwd=cwd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)
        stdout, stderr = proc.communicate()
        self.artifact.data_dict['1'] = stdout
        self.artifact.stdout = stderr

        self.handle_subprocess_proc_return(proc.returncode, stderr)

class BashFilter(ProcessStdoutFilter):
    """
    Runs bash script and returns STDOUT.
    """
    EXECUTABLE = 'bash'
    VERSION = 'bash --version'
    INPUT_EXTENSIONS = [".sh", ".bash", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['bash']

class PhpFilter(ProcessStdoutFilter):
    """
    Runs php script and returns STDOUT.
    """
    EXECUTABLE = 'php'
    VERSION = 'php --version'
    INPUT_EXTENSIONS = [".php"]
    OUTPUT_EXTENSIONS = [".html", ".txt"]
    ALIASES = ['php']

class EscriptFilter(ProcessStdoutFilter):
    """
    Runs escript (erlang) and returns STDOUT.
    """
    EXECUTABLE = 'escript'
    INPUT_EXTENSIONS = [".erl"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['escript']

class LuaFilter(ProcessStdoutFilter):
    """
    Runs lua script and returns STDOUT.
    """
    EXECUTABLE = 'lua'
    VERSION = 'lua -v'
    INPUT_EXTENSIONS = ['.lua']
    OUTPUT_EXTENSIONS = ['.txt']
    ALIASES = ['lua']

class RedclothFilter(ProcessStdoutFilter):
    """
    Runs redcloth, converts textile markup to HTML.
    """
    EXECUTABLE = 'redcloth'
    VERSION = 'redcloth --version'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['redcloth', 'textile']

class RedclothLatexFilter(ProcessStdoutFilter):
    """
    Runs redcloth, converts textile markup to LaTeX.
    """
    EXECUTABLE = 'redcloth -o latex'
    VERSION = 'redcloth --version'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['redclothl', 'latextile']

class Rst2HtmlFilter(ProcessStdoutFilter):
    EXECUTABLE = 'rst2html.py'
    VERSION = 'rst2html.py --version'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['rst2html']
    FINAL = True

class Rst2LatexFilter(ProcessStdoutFilter):
    EXECUTABLE = 'rst2latex.py'
    VERSION = 'rst2latex.py --version'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2latex']

class Rst2BeamerFilter(ProcessStdoutFilter):
    EXECUTABLE = 'rst2beamer'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2beamer']

class SloccountFilter(ProcessStdoutFilter):
    EXECUTABLE = 'sloccount'
    VERSION = 'sloccount --version'
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['sloc', 'sloccount']

class RubyStdoutFilter(ProcessStdoutFilter):
    EXECUTABLE = 'ruby'
    VERSION = 'ruby --version'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rb']

class RdConvFilter(ProcessStdoutFilter):
    """Convert R documentation to other formats."""
    EXECUTABLE = "R CMD Rdconv"
    VERSION = "R CMD Rdconv -v"
    INPUT_EXTENSIONS = ['.Rd']
    OUTPUT_EXTENSIONS = ['.txt', '.html', '.tex', '.R']
    ALIASES = ['rdconv']
    EXTENSION_TO_FORMAT = {
        '.txt' : 'txt',
        '.html' : 'html',
        '.tex' : 'latex',
        '.R' : 'example'
    }

    def instance_executable(self):
        return "%s --type=%s" % (self.EXECUTABLE, self.EXTENSION_TO_FORMAT[self.artifact.ext])

class RagelRubyDotFilter(ProcessStdoutFilter):
    """
    Generates state chart in .dot format of ragel state machine for ruby.
    """
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".dot"]
    ALIASES = ['rlrbd', 'ragelrubydot']
    VERSION = 'ragel --version'
    EXECUTABLE = 'ragel -R -V'


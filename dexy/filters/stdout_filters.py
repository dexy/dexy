from dexy.filters.process_filters import SubprocessStdoutFilter
from dexy.filters.process_filters import SubprocessStdoutInputFilter
from dexy.filters.process_filters import SubprocessStdoutInputFileFilter

class RhinoSubprocessStdoutFilter(SubprocessStdoutFilter):
    EXECUTABLE = "rhino -f"
    INPUT_EXTENSIONS = [".js"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['js', 'rhino']

class CowsaySubprocessStdoutFilter(SubprocessStdoutFilter):
    ALIASES = ['cowsay']
    EXECUTABLE = 'cowsay'
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".txt"]

    def command_string_stdout(self):
        args = self.command_line_args() or ""
        text = self.artifact.input_text()
        return "%s %s \"%s\"" % (self.executable(), args, text)

class CowthinkSubprocessStdoutFilter(CowsaySubprocessStdoutFilter):
    ALIASES = ['cowthink']
    EXECUTABLE = 'cowthink'

class PythonSubprocessStdoutFilter(SubprocessStdoutFilter):
    ALIASES = ['py', 'pyout']
    EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'python --version'

class PythonSubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    ALIASES = ['pyinput']
    EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'python --version'

class BashSubprocessStdoutFilter(SubprocessStdoutFilter):
    ALIASES = ['sh', 'bash']
    EXECUTABLE = 'bash'
    INPUT_EXTENSIONS = [".sh", ".bash", ".txt", ""]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'bash --version'

class BashSubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    ALIASES = ['shinput']
    EXECUTABLE = 'bash'
    INPUT_EXTENSIONS = [".sh", ".bash", ".txt", ""]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'bash --version'

class SedSubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    ALIASES = ['sed']
    EXECUTABLE = 'sed'
    INPUT_EXTENSIONS = [".sed"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'sed --version'

    def command_string_stdout(self):
        wf = self.artifact.previous_artifact_filename
        return "%s -f %s" % (self.executable(), wf)

class RegetronSubprocessStdoutInputFileFilter(SubprocessStdoutInputFileFilter):
    ALIASES = ['regetron']
    EXECUTABLE = 'regetron'
    INPUT_EXTENSIONS = [".regex"]
    OUTPUT_EXTENSIONS = [".txt"]

    def command_string_stdout_input(self, input_artifact):
        wf = self.artifact.previous_artifact_filename
        input_file = input_artifact.filename()
        return "%s %s %s" % (self.executable(), input_file, wf)

class IrbSubprocessStdoutFilter(SubprocessStdoutFilter):
    ALIASES = ['irbout']
    EXECUTABLE = 'irb --simple-prompt --noreadline'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".rbcon"]
    VERSION_COMMAND = 'irb --version'

class IrbSubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    ALIASES = ['irboutinput']
    EXECUTABLE = 'irb --simple-prompt --noreadline'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".rbcon"]
    VERSION_COMMAND = 'irb --version'

class RubySubprocessStdoutFilter(SubprocessStdoutFilter):
    EXECUTABLE = 'ruby'
    VERSION_COMMAND = 'ruby --version'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rb']

class RubySubprocessStdoutInputFilter(SubprocessStdoutInputFilter):
    EXECUTABLE = 'ruby'
    VERSION_COMMAND = 'ruby --version'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rbinput']

class EscriptSubprocessStdoutFilter(SubprocessStdoutFilter):
    """
    Runs Erlang scripts using the escript command.
    """
    EXECUTABLE = 'escript'
    INPUT_EXTENSIONS = [".erl"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['escript']

# Unchecked below this...

class PhpFilter(SubprocessStdoutFilter):
    """
    Runs php script and returns STDOUT.
    """
    EXECUTABLE = 'php'
    VERSION_COMMAND = 'php --version'
    INPUT_EXTENSIONS = [".php"]
    OUTPUT_EXTENSIONS = [".html", ".txt"]
    ALIASES = ['php']

class LuaFilter(SubprocessStdoutFilter):
    """
    Runs lua script and returns STDOUT.
    """
    EXECUTABLE = 'lua'
    VERSION_COMMAND = 'lua -v'
    INPUT_EXTENSIONS = ['.lua']
    OUTPUT_EXTENSIONS = ['.txt']
    ALIASES = ['lua']

class RedclothFilter(SubprocessStdoutFilter):
    """
    Runs redcloth, converts textile markup to HTML.
    """
    EXECUTABLE = 'redcloth'
    VERSION_COMMAND = 'redcloth --version'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['redcloth', 'textile']

class RedclothLatexFilter(SubprocessStdoutFilter):
    """
    Runs redcloth, converts textile markup to LaTeX.
    """
    EXECUTABLE = 'redcloth -o latex'
    VERSION_COMMAND = 'redcloth --version'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['redclothl', 'latextile']

class Rst2HtmlFilter(SubprocessStdoutFilter):
    EXECUTABLE = 'rst2html.py'
    VERSION_COMMAND = 'rst2html.py --version'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['rst2html']
    FINAL = True

class Rst2LatexFilter(SubprocessStdoutFilter):
    EXECUTABLE = 'rst2latex.py'
    VERSION_COMMAND = 'rst2latex.py --version'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2latex']

class Rst2BeamerFilter(SubprocessStdoutFilter):
    EXECUTABLE = 'rst2beamer'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2beamer']

class SloccountFilter(SubprocessStdoutFilter):
    EXECUTABLE = 'sloccount'
    VERSION_COMMAND = 'sloccount --version'
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['sloc', 'sloccount']

class RdConvFilter(SubprocessStdoutFilter):
    """Convert R documentation to other formats."""
    EXECUTABLE = "R CMD Rdconv"
    VERSION_COMMAND = "R CMD Rdconv -v"
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

class RagelRubyDotFilter(SubprocessStdoutFilter):
    """
    Generates state chart in .dot format of ragel state machine for ruby.
    """
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".dot"]
    ALIASES = ['rlrbd', 'ragelrubydot']
    VERSION_COMMAND = 'ragel --version'
    EXECUTABLE = 'ragel -R -V'

class LynxDumpFilter(SubprocessStdoutFilter):
    """
    Converts HTML to plain text by using lynx -dump.
    """
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['lynxdump']
    VERSION_COMMAND = 'lynx --version'
    EXECUTABLE = 'lynx -dump'

class NonexistentFilter(SubprocessStdoutFilter):
    ALIASES = ['zzzdoesnotexist']
    VERSION_COMMAND = 'notherenopexxx --version'

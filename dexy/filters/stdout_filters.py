from dexy.filters.process_filters import SubprocessStdoutFilter
import json
import os

class CleanSubprocessStdoutFilter(SubprocessStdoutFilter):
    """
    Clean non-printing characters from text using the 'strings' tool.
    """
    ALIASES = ['clean', 'strings']
    EXECUTABLE = 'strings'

class ManPageSubprocessStdoutFilter(SubprocessStdoutFilter):
    """
    Read command names from a file and fetch man pages for each.

    Returns a JSON dict whose keys are the program names and values are man
    pages.
    """
    ALIASES = ['man']
    EXECUTABLE = 'man'
    VERSION_COMMAND = 'man --version'
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".json"]

    def command_string(self, prog_name):
        # Use bash rather than the default of sh (dash) so we can set pipefail.
        return "bash -c \"set -e; set -o pipefail; man %s | col -b | strings\"" % (prog_name)

    def process(self):
        man_info = {}
        for prog_name in self.artifact.input_text().split():
            command = self.command_string(prog_name)
            proc, stdout = self.run_command(command, self.setup_env())
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)
            man_info[prog_name] = stdout

        self.artifact.set_data(json.dumps(man_info))

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

class BashSubprocessStdoutFilter(SubprocessStdoutFilter):
    ALIASES = ['sh', 'bash']
    EXECUTABLE = 'bash -e'
    INPUT_EXTENSIONS = [".sh", ".bash", ".txt", ""]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'bash --version'

class IrbSubprocessStdoutFilter(SubprocessStdoutFilter):
    ALIASES = ['irbout']
    CHECK_RETURN_CODE = False
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

class SloccountFilter(SubprocessStdoutFilter):
    EXECUTABLE = 'sloccount'
    VERSION_COMMAND = 'sloccount --version'
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['sloc', 'sloccount']

class LuaFilter(SubprocessStdoutFilter):
    """
    Runs lua script and returns STDOUT.
    """
    EXECUTABLE = 'lua'
    VERSION_COMMAND = 'lua -v'
    INPUT_EXTENSIONS = ['.lua']
    OUTPUT_EXTENSIONS = ['.txt']
    ALIASES = ['lua']

class PhpFilter(SubprocessStdoutFilter):
    """
    Runs php file, note that php code must be included in <?php ... ?> tags.
    """
    EXECUTABLE = 'php'
    CHECK_RETURN_CODE = False # TODO see if it's possible to check return code for PHP
    VERSION_COMMAND = 'php --version'
    INPUT_EXTENSIONS = [".php"]
    OUTPUT_EXTENSIONS = [".html", ".txt"]
    ALIASES = ['php']

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

class EscriptSubprocessStdoutFilter(SubprocessStdoutFilter):
    """
    Runs Erlang scripts using the escript command.
    """
    EXECUTABLE = 'escript'
    INPUT_EXTENSIONS = [".erl"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['escript']

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
    """
    This uses the command line tool rst2html. The 'rst' filter is recommended instead of this.
    """
    EXECUTABLES = ['rst2html', 'rst2html.py']
    VERSION_COMMAND = 'rst2html.py --version'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['rst2html']
    FINAL = True

class Rst2LatexFilter(SubprocessStdoutFilter):
    """
    This uses the command line tool rst2latex. The 'rst' filter is recommended instead of this.
    """
    EXECUTABLES = ['rst2latex', 'rst2latex.py']
    VERSION_COMMAND = 'rst2latex.py --version'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2latex']

class Rst2BeamerFilter(SubprocessStdoutFilter):
    ALIASES = ['rst2beamer']
    EXECUTABLES = ['rst2beamer', 'rst2beamer.py']
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    VERSION_COMMAND = "rst2beamer --version"

class Wiki2BeamerFilter(SubprocessStdoutFilter):
    ALIASES = ['wiki2beamer']
    EXECUTABLES = ['wiki2beamer']
    INPUT_EXTENSIONS = [".wiki", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    VERSION_COMMAND = "wiki2beamer --version"

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

    def command_string_stdout(self):
        exe = self.executable()
        args = self.command_line_args() or ""
        fmt = self.EXTENSION_TO_FORMAT[self.artifact.ext]
        script_file = os.path.basename(self.artifact.previous_canonical_filename)
        return "%s %s --type=%s %s" % (exe, args, fmt, script_file)

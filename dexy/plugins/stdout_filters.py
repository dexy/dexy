from dexy.plugins.process_filters import SubprocessStdoutFilter
from dexy.plugins.process_filters import SubprocessInputFileFilter
import json

class NodeJsStdoutFilter(SubprocessStdoutFilter):
    """
    Runs scripts using node js.
    """
    ADD_NEW_FILES = True
    ALIASES = ['nodejs', 'node']
    EXECUTABLE = 'node'
    INPUT_EXTENSIONS = ['.js', '.txt']
    OUTPUT_EXTENSIONS = ['.txt']
    VERSION_COMMAND = 'node --version'

class Regetron(SubprocessInputFileFilter):
    """
    Filter which loads .regex file into regetron and runs any input text against it.
    """
    ALIASES = ['regetron']
    EXECUTABLE = 'regetron'
    INPUT_EXTENSIONS = [".regex"]
    OUTPUT_EXTENSIONS = [".txt"]

    def command_string_for_input(self, input_doc):
        text = input_doc.output().name
        regex = self.input_filename()
        return "%s %s %s" % (self.executable(), text, regex)

class Pdfinfo(SubprocessStdoutFilter):
    """
    Uses the pdfinfo script to retrieve metadata about a PDF.
    """
    ALIASES = ['pdfinfo']
    EXECUTABLE = 'pdfinfo'
    INPUT_EXTENSIONS = ['.pdf']
    OUTPUT_EXTENSIONS = ['.txt']

class Wordcount(SubprocessStdoutFilter):
    """
    Runs input through wc command line tool.
    """
    ALIASES = ['wc']
    EXECUTABLE = 'wc'
    OUTPUT_EXTENSIONS = ['.txt']

class Python(SubprocessStdoutFilter):
    """
    Runs Python code and returns stdout.
    """
    ALIASES = ['py', 'pyout']
    EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'python --version'
    TAGS = ['python']

class Bash(SubprocessStdoutFilter):
    """
    Runs bash scripts and returns stdout.
    """
    ALIASES = ['sh', 'bash']
    EXECUTABLE = 'bash -e'
    INPUT_EXTENSIONS = [".sh", ".bash", ".txt", ""]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'bash --version'

class Ruby(SubprocessStdoutFilter):
    """
    Runs ruby scripts and return stdout.
    """
    EXECUTABLE = 'ruby'
    VERSION_COMMAND = 'ruby --version'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rb']

class Irb(SubprocessStdoutFilter):
    """
    Runs ruby scripts in irb.
    """
    ALIASES = ['irbout']
    CHECK_RETURN_CODE = False
    EXECUTABLE = 'irb --simple-prompt --noreadline'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".rbcon"]
    VERSION_COMMAND = 'irb --version'

class Sloccount(SubprocessStdoutFilter):
    """
    Runs code through sloccount.
    """
    EXECUTABLE = 'sloccount'
    VERSION_COMMAND = 'sloccount --version'
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['sloc', 'sloccount']

class Rhino(SubprocessStdoutFilter):
    """
    Runs code through rhino js interpreter.
    """
    EXECUTABLE = "rhino -f"
    INPUT_EXTENSIONS = [".js", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['js', 'rhino']

class Lua(SubprocessStdoutFilter):
    """
    Runs code through lua interpreter.
    """
    EXECUTABLE = 'lua'
    VERSION_COMMAND = 'lua -v'
    INPUT_EXTENSIONS = ['.lua', '.txt']
    OUTPUT_EXTENSIONS = ['.txt']
    ALIASES = ['lua']

class Cowsay(SubprocessStdoutFilter):
    """
    Runs input through 'cowsay'.
    """
    ADD_NEW_FILES = False
    ALIASES = ['cowsay']
    EXECUTABLE = 'cowsay'
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".txt"]

    def command_string_stdout(self):
        args = self.command_line_args() or ""
        text = self.input().as_text()
        return "%s %s \"%s\"" % (self.executable(), args, text)

class Cowthink(Cowsay):
    """
    Runs input through 'cowthink'.
    """
    ALIASES = ['cowthink']
    EXECUTABLE = 'cowthink'

class Figlet(Cowsay):
    """
    Runs input through 'figlet'.
    """
    ALIASES = ['figlet']
    EXECUTABLE = 'figlet'

class Wiki2Beamer(SubprocessStdoutFilter):
    """
    Converts wiki content to beamer.
    """
    ALIASES = ['wiki2beamer']
    EXECUTABLES = ['wiki2beamer']
    INPUT_EXTENSIONS = [".wiki", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    VERSION_COMMAND = "wiki2beamer --version"

class Strings(SubprocessStdoutFilter):
    """
    Clean non-printing characters from text using the 'strings' tool.
    """
    ALIASES = ['strings']
    EXECUTABLE = 'strings'

class Php(SubprocessStdoutFilter):
    """
    Runs php file, note that php code must be included in <?php ... ?> tags.
    """
    EXECUTABLE = 'php'
    CHECK_RETURN_CODE = False # TODO see if it's possible to check return code for PHP
    VERSION_COMMAND = 'php --version'
    INPUT_EXTENSIONS = [".php", ".txt"]
    OUTPUT_EXTENSIONS = [".html", ".txt"]
    ALIASES = ['php']

class RagelRubyDot(SubprocessStdoutFilter):
    """
    Generates state chart in .dot format of ragel state machine for ruby.
    """
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".dot"]
    ALIASES = ['rlrbd', 'ragelrubydot']
    VERSION_COMMAND = 'ragel --version'
    EXECUTABLE = 'ragel -R -V'

class ManPage(SubprocessStdoutFilter):
    """
    Read command names from a file and fetch man pages for each.

    Returns a JSON dict whose keys are the program names and values are man
    pages.
    """
    ALIASES = ['man']
    EXECUTABLE = 'man'
    REQUIRED_EXECUTABLES = ['strings']
    VERSION_COMMAND = 'man --version'
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".json"]

    def command_string(self, prog_name):
        # Use bash rather than the default of sh (dash) so we can set pipefail.
        return "bash -c \"set -e; set -o pipefail; man %s | col -b | strings\"" % (prog_name)

    def process(self):
        man_info = {}
        for prog_name in self.input().data().split():
            command = self.command_string(prog_name)
            proc, stdout = self.run_command(command, self.setup_env())
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)
            man_info[prog_name] = stdout

        self.output().set_data(json.dumps(man_info))

class Lynxdump(SubprocessStdoutFilter):
    """
    Converts HTML to plain text by using lynx -dump.
    """
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['lynxdump']
    VERSION_COMMAND = 'lynx --version'
    EXECUTABLE = 'lynx -dump'

class Escript(SubprocessStdoutFilter):
    """
    Runs Erlang scripts using the escript command.
    """
    EXECUTABLE = 'escript'
    INPUT_EXTENSIONS = [".erl"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['escript']

class Redcloth(SubprocessStdoutFilter):
    """
    Runs redcloth, converts textile markup to HTML.
    """
    EXECUTABLE = 'redcloth'
    VERSION_COMMAND = 'redcloth --version'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['redcloth', 'textile']

class RedclothLatex(SubprocessStdoutFilter):
    """
    Runs redcloth, converts textile markup to LaTeX.
    """
    EXECUTABLE = 'redcloth -o latex'
    VERSION_COMMAND = 'redcloth --version'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['redclothl', 'latextile']

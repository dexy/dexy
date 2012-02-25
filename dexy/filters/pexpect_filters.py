from dexy.filters.process_filters import ProcessFilter
from dexy.filters.process_filters import DexyEOFException
from ordereddict import OrderedDict
import os
import pexpect
import re

class PexpectReplFilter(ProcessFilter):
    """
    Base class for filters which use pexpect to retrieve output line-by-line based on detecting prompts.
    """
    ALIASES = ['pexpectreplfilter']
    ALLOW_MATCH_PROMPT_WITHOUT_NEWLINE = False
    INITIAL_PROMPT = None
    LINE_ENDING = "\r\n"
    PROMPTS = ['>>>', '...'] # Python uses >>> prompt normally and ... when in multi-line structures like loops
    PROMPT_REGEX = None
    PS1 = None
    PS2 = None
    PS3 = None
    PS4 = None
    SAVE_VARS_TO_JSON_CMD = None
    TRIM_PROMPT = '>>>'

    def prompt_search_terms(self):
        """
        Search first for the prompt (or prompts) following a line ending.
        Also optionally allow matching the prompt with no preceding line ending.
        """

        if self.PROMPT_REGEX:
            prompts = [self.PROMPT_REGEX]
        elif hasattr(self, 'PROMPT'):
            prompts = [self.PROMPT]
        else:
            prompts = self.PROMPTS

        if self.ALLOW_MATCH_PROMPT_WITHOUT_NEWLINE:
            return ["%s%s" % (self.LINE_ENDING, p) for p in prompts] + prompts
        else:
            return ["%s%s" % (self.LINE_ENDING, p) for p in prompts]

    def lines_for_section(self, section_text):
        """
        Take the section text and split it into lines which will be sent to the
        interpreter. This can be overridden if lines need to be defined
        differently, or if you don't want the extra newline at the end.
        """
        return section_text.splitlines() + ["\n"]

    def strip_trailing_prompts(self, section_transcript):
        lines = section_transcript.splitlines()
        while len(lines) > 0 and re.match("^\s*(%s)\s*$|^\s*$" % self.TRIM_PROMPT, lines[-1]):
            lines = lines[0:-1]
        return self.LINE_ENDING.join(lines)

    def strip_newlines(self, line):
        return line.replace(" \r", "")

    def process_dict(self, input_dict):
        output_dict = OrderedDict()

        # If we want to automatically record values of local variables in the
        # script we are running, we add a section at the end of script
        do_record_vars = self.artifact.args.has_key('record-vars') and self.artifact.args['record-vars']
        if do_record_vars:
            if not self.SAVE_VARS_TO_JSON_CMD:
                raise Exception("Can't record vars since SAVE_VARS_TO_JSON_CMD not set.")
            artifact = self.artifact.add_additional_artifact(self.artifact.key + "-vars.json", 'json')
            self.log.debug("Added additional artifact %s (hashstring %s) to store variables" % (artifact.key, artifact.hashstring))
            section_text = self.SAVE_VARS_TO_JSON_CMD % artifact.filename()
            input_dict['dexy--save-vars'] = section_text
            # TODO this may cause unexpected results if original script only had 1 section

        search_terms = self.prompt_search_terms()

        env = self.setup_env()
    	if not env:
    	    env = os.environ

        if env.has_key('PS1') and self.PS1:
            env['PS1'] = self.PS1
        if env.has_key('PS2') and self.PS2:
            env['PS2'] = self.PS2
        if env.has_key('PS3') and self.PS3:
            env['PS3'] = self.PS3
        if env.has_key('PS4') and self.PS4:
            env['PS4'] = self.PS4

        timeout = self.setup_timeout()

        # Spawn the process
        proc = pexpect.spawn(
                self.executable(),
                cwd=self.artifact.artifacts_dir,
                env=env)

        # Capture the initial prompt
        if self.INITIAL_PROMPT:
            proc.expect(self.INITIAL_PROMPT, timeout=timeout)
        elif self.PROMPT_REGEX:
            proc.expect(search_terms, timeout=timeout)
        else:
            proc.expect_exact(search_terms, timeout=timeout)

        start = proc.before + proc.after
        for section_key, section_text in input_dict.items():
            section_transcript = start
            start = ""

            lines = self.lines_for_section(section_text)
            for l in lines:
                section_transcript += start
                proc.send(l.rstrip() + "\n")
                try:
                    if self.PROMPT_REGEX:
                        proc.expect(search_terms, timeout=timeout)
                    else:
                        proc.expect_exact(search_terms, timeout=timeout)

                        section_transcript += self.strip_newlines(proc.before)
                        start = proc.after
                except pexpect.EOF:
                    if not self.ignore_errors():
                        raise DexyEOFException()

            # Save this section's output
            output_dict[section_key] = self.strip_trailing_prompts(section_transcript)

        try:
            proc.close()
        except pexpect.ExceptionPexpect:
            raise Exception("process %s may not have closed" % proc.pid)

        if proc.exitstatus and self.CHECK_RETURN_CODE:
            self.handle_subprocess_proc_return(self.executable() , proc.exitstatus, str(output_dict))

        return output_dict

class RubyPexpectReplFilter(PexpectReplFilter):
    ALIASES = ['irb', 'rbrepl']
    EXECUTABLE = 'irb --simple-prompt'
    CHECK_RETURN_CODE = False
    INITIAL_PROMPT = "^>>"
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".rbcon"]
    PROMPTS = [">>", "?>"]
    TRIM_PROMPT = '>>'
    VERSION_COMMAND = 'irb --version'

class PythonPexpectReplFilter(PexpectReplFilter):
    ALIASES = ['pycon', 'pyrepl']
    CHECK_RETURN_CODE = False
    EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".pycon"]
    TAGS = ['python', 'interpreter', 'language']
    VERSION_COMMAND = 'python --version'

    SAVE_VARS_TO_JSON_CMD = """
import json
dexy__vars_file = open("%s", "w")
dexy__x = {}
for dexy__k, dexy__v in locals().items():
    dexy__x[dexy__k] = str(dexy__v)

json.dump(dexy__x, dexy__vars_file)
dexy__vars_file.close()
"""

class IpythonPexpectReplFilter(PythonPexpectReplFilter):
    # TODO test for version of ipython that supports --classic
    ALIASES = ['ipython']
    EXECUTABLE = 'ipython --classic'
    CHECK_RETURN_CODE = False # TODO try to figure out why we are getting nonzero exit codes
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".pycon"]
    VERSION_COMMAND = 'ipython -Version'

# untested below here

class RPexpectReplFilter(PexpectReplFilter):
    ALIASES = ['r', 'rint']
    CHECK_RETURN_CODE = False
    EXECUTABLE = "R --quiet --vanilla"
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = ['.Rout']
    PROMPTS = [">", "+"]
    TAGS = ['r', 'interpreter', 'language']
    TRIM_PROMPT = ">"
    INITIAL_PROMPT = "^>"
    VERSION_COMMAND = "R --version"
    SAVE_VARS_TO_JSON_CMD = """
if ("rjson" %%in%% installed.packages()) {
    library(rjson)
    dexy__json_file <- file("%s", "w")
    writeLines(toJSON(as.list(environment())), dexy__json_file)
    close(dexy__json_file)
} else {
   cat("Can't automatically save environment to JSON since rjson package not installed.")
}
"""

class RhinoInteractiveFilter(PexpectReplFilter):
    """
    Runs rhino JavaScript interpeter.
    """
    EXECUTABLE = "rhino"
    INPUT_EXTENSIONS = [".js", ".txt"]
    OUTPUT_EXTENSIONS = [".jscon"]
    ALIASES = ['jsint', 'rhinoint']
    PROMPTS = ['js>', '  >']
    TRIM_PROMPT = "js>"

class PhpInteractiveFilter(PexpectReplFilter):
    """
    Runs PHP in interpeter mode.
    """
    CHECK_RETURN_CODE = False
    EXECUTABLE = "php -a"
    INPUT_EXTENSIONS = [".php", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['phpint']
    PROMPTS = ['php > ']
    TRIM_PROMPT = "php > "

class KshInteractiveFilter(PexpectReplFilter):
    """
    Runs ksh. Use to run bash scripts.
    """
    ALIASES = ['shint']
    EXECUTABLE = "ksh -i -r -e"
    INPUT_EXTENSIONS = [".txt", ".sh"]
    OUTPUT_EXTENSIONS = ['.sh-session']
    INITIAL_PROMPT = "^(#|\$)"
    PROMPTS = ["$", "#"]
    TRIM_PROMPT = "\$|#"
    PS1 = "$ "
    # TODO Fix hanging on # comments in code

class ClojureInteractiveFilter(PexpectReplFilter):
    """
    Runs clojure.
    """
    EXECUTABLE = 'clojure -r'
    INPUT_EXTENSIONS = [".clj", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['clj', 'cljint']
    PROMPT = "user=> "
    CHECK_RETURN_CODE = False

    def lines_for_section(self, input_text):
        input_lines = []
        current_line = []
        in_indented_block = False
        for l in input_text.splitlines():
            if re.match("^\s+", l):
                in_indented_block = True
                current_line.append(l)
            else:
                if len(current_line) > 0:
                    input_lines.append("\n".join(current_line))
                if in_indented_block:
                    # we have reached the end of this indented block
                    in_indented_block = False
                current_line = [l]
        input_lines.append("\n".join(current_line))
        return input_lines

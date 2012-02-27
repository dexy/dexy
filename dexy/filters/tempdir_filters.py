from dexy.filters.pexpect_filters import KshInteractiveFilter
from dexy.filters.process_filters import DexyEOFException
from ordereddict import OrderedDict
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers.other import BashSessionLexer
import json
import os
import pexpect
import shutil
import tarfile
import tempfile

class KshTempdirInteractiveFilter(KshInteractiveFilter):
    """
    Runs ksh in a temporary directory, recording state of that directory.
    """
    ALIASES = ['shtmp']
    EXECUTABLE = "ksh -i -e"
    OUTPUT_EXTENSIONS = [".json"]

    def process_dict(self, input_dict):
        # Set up syntax highlighting
        html_formatter = HtmlFormatter()
        latex_formatter = LatexFormatter()
        lexer = BashSessionLexer()

        output_dict = OrderedDict()
        search_terms = self.prompt_search_terms()

        # Create a temporary directory where we will run our script.
        work_dir = tempfile.mkdtemp()

        for input_artifact in self.artifact.inputs().values():
            filename = os.path.join(work_dir, input_artifact.canonical_filename())
            if os.path.exists(input_artifact.filepath()):
                local_path = os.path.relpath(input_artifact.canonical_filename(), os.path.dirname(self.artifact.canonical_filename()))
                input_artifact.write_to_file(os.path.join(work_dir, local_path))
                self.log.debug("Populating temp dir for %s with %s" % (self.artifact.key, local_path))
            else:
                self.log.warn("Skipping file %s for temp dir for %s, file does not exist (yet)" % (filename, self.artifact.key))

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

        self.log.debug("About to spawn '%s' in %s" % (self.executable(), work_dir))
        proc = pexpect.spawn(
                self.executable(),
                cwd=work_dir,
                env=env)
        timeout = self.setup_timeout()

        self.log.debug("Waiting to capture initial prompt...")
        if self.INITIAL_PROMPT:
            proc.expect(self.INITIAL_PROMPT, timeout=timeout)
        elif self.PROMPT_REGEX:
            proc.expect(search_terms, timeout=timeout)
        else:
            proc.expect_exact(search_terms, timeout=timeout)

        self.log.debug("Initial prompt captured.")
        start = proc.before + proc.after

        for section_key, section_text in input_dict.items():
            section_transcript = start
            start = ""

            lines = self.lines_for_section(section_text)
            for l in lines:
                self.log.debug("sending: '%s'" % l)
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

            section_info = {}
            section_info['transcript'] = self.clean_nonprinting(self.strip_trailing_prompts(section_transcript))
            section_info['transcript-html'] = highlight(section_info['transcript'], lexer, html_formatter)
            section_info['transcript-latex'] = highlight(section_info['transcript'], lexer, latex_formatter)

            section_info['files'] = {}

            tar_artifact = self.artifact.add_additional_artifact("%s.tgz" % section_key, ".tgz")
            tar = tarfile.open(tar_artifact.filepath(), mode="w:gz")

            for root, dirs, files in os.walk(work_dir):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    local_path = os.path.relpath(filepath, work_dir)

                    tar.add(filepath, arcname=local_path)

                    with open(filepath, "r") as f:
                        contents = f.read()
                        try:
                            json.dumps(contents)
                            section_info['files'][local_path] = contents
                        except UnicodeDecodeError:
                            section_info['files'][local_path] = None

            tar.close()

            # Save this section's output
            output_dict[section_key] = section_info

        try:
            proc.close()
        except pexpect.ExceptionPexpect:
            raise Exception("process %s may not have closed" % proc.pid)

        if proc.exitstatus and self.CHECK_RETURN_CODE:
            self.handle_subprocess_proc_return(self.executable(), proc.exitstatus, str(output_dict))

        for i in self.artifact.inputs().values():
            src = os.path.join(work_dir, i.filename())
            if (i.virtual or i.additional) and os.path.exists(src):
                shutil.copy(src, i.filepath())

        shutil.rmtree(work_dir)
        x = OrderedDict()
        x['1'] = json.dumps(output_dict)
        return x

from dexy.filters.pexpect_filters import KshInteractiveStrictFilter
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

class KshTempdirInteractiveFilter(KshInteractiveStrictFilter):
    """
    Runs ksh in a temporary directory, recording state of that directory.
    """
    ALIASES = ['shtmp']
    OUTPUT_EXTENSIONS = [".json"]

    def setup_cwd(self):
        self.log.debug("in setup_cwd in KshTempdirInteractiveFilter")
        if not hasattr(self, '_cwd'):
            self._cwd = tempfile.mkdtemp()
        if not os.path.exists(self._cwd):
            raise Exception("path %s should exist!" % self._cwd)
        self.log.debug("tempdir is %s" % self._cwd)
        return self._cwd

    def process_dict(self, input_dict):
        # Set up syntax highlighting
        html_formatter = HtmlFormatter()
        latex_formatter = LatexFormatter()
        lexer = BashSessionLexer()

        output_dict = OrderedDict()

        work_dir = self.setup_cwd()

        # Populate the temporary directory.
        for input_artifact in self.artifact.inputs().values():
            filename = os.path.join(work_dir, input_artifact.canonical_filename())
            if os.path.exists(input_artifact.filepath()):
                local_path = os.path.relpath(input_artifact.canonical_filename(), os.path.dirname(self.artifact.canonical_filename()))
                workdir_path = os.path.join(work_dir, local_path)
                input_artifact.write_to_file(workdir_path)
                self.log.debug("Writing file %s in temp dir for %s" % (workdir_path, self.artifact.key))
            else:
                self.log.debug("Skipping file %s for temp dir for %s, file does not exist (yet)" % (filename, self.artifact.key))

        self.log.debug("Starting to process code..")
        for section_key, section_transcript in self.section_output(input_dict):
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

        # Collect any artifacts which were generated in the tempdir, that need
        # to be moved to their final locations.
        for i in self.artifact.inputs().values():
            src = os.path.join(work_dir, i.filename())
            self.log.debug("Checking input %s at %s" % (i.key, src))
            if (i.virtual or i.additional) and os.path.exists(src):
                self.log.debug("Copying %s to %s" % (src, i.filepath()))
                shutil.copy(src, i.filepath())
            else:
                self.log.debug("Not copying %s" % src)

        #shutil.rmtree(work_dir)
        x = OrderedDict()
        x['1'] = json.dumps(output_dict)
        return x

from dexy.filters.process import SubprocessFilter
from dexy.utils import file_exists
import codecs
import dexy.exceptions
import dexy.utils
import os
import subprocess

class LatexFilter(SubprocessFilter):
    """
    Generates a PDF file from LaTeX source.
    """
    aliases = ['latex', 'pdflatex']
    _settings = {
            'executable' : 'pdflatex',
            'output' : True,
            'input-extensions' : ['.tex', '.txt'],
            'output-extensions' : ['.pdf'],
            'run-bibtex' : ("Should we run bibtex if a .bib file is an input?", True),
            'times-to-run-latex' : ("""How many times to run latex? (Latex is
                run one additional time if bibtex runs.)""", 2),
            'command-string' : "%(prog)s -interaction=nonstopmode -halt-on-error %(args)s %(script_file)s"
            }

    def process(self):
        self.populate_workspace()

        wd = self.parent_work_dir()
        env = self.setup_env()

        latex_command = self.command_string()

        if any(doc.output_data().ext == '.bib' for doc in self.doc.walk_input_docs()):
            bibtex_command = "bibtex %s" % os.path.splitext(self.output_data.basename())[0]
        else:
            bibtex_command = None

        def run_cmd(command):
            self.log_debug("running %s in %s" % (command, os.path.abspath(wd)))
            proc = subprocess.Popen(command, shell=True,
                                    cwd=wd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    env=env)

            stdout, stderr = proc.communicate()
            self.log_debug(stdout)

        if bibtex_command and self.setting('run-bibtex'):
            run_cmd(latex_command) #generate aux
            run_cmd(bibtex_command) #generate bbl

        n = self.setting('times-to-run-latex')
        for i in range(n):
            self.log_debug("running latex time %s (out of %s)" % (i+1, n))
            run_cmd(latex_command)

        if not file_exists(os.path.join(wd, self.output_data.basename())):
            log_file_path = os.path.join(wd, self.output_data.basename().replace(".pdf", ".log"))

            if file_exists(log_file_path):
                msg = "Latex file not generated. Look for information in latex log %s"
                msgargs = log_file_path
            else:
                msg = "Latex file not generated. Look for information in latex log in %s directory."
                msgargs = os.path.abspath(wd)

            raise dexy.exceptions.UserFeedback(msg % msgargs)

        if self.setting('add-new-files'):
            self.log_debug("adding new files found in %s for %s" % (wd, self.key))
            self.add_new_files()

        self.copy_canonical_file()

class TikzPdfFilter(LatexFilter):
    """
    Renders Tikz code to PDF.
    """
    aliases = ['tikz']

    def process(self):
        latex_filename = self.output_data.basename().replace(self.ext, ".tex")

        # TODO allow setting tikz libraries per-document, or just include all of them?
        # TODO how to create a page size that just includes the content
        latex_header = r"""\documentclass[tikz]{standalone}
\usetikzlibrary{shapes.multipart}
\begin{document}
        """
        latex_footer = "\n\end{document}"

        self.populate_workspace()
        wd = self.parent_work_dir()

        work_path = os.path.join(wd, latex_filename)
        self.log_debug("writing latex header + tikz content to %s" % work_path)
        with codecs.open(work_path, "w", encoding="utf-8") as f:
            f.write(latex_header)
            f.write(str(self.input_data))
            f.write(latex_footer)

        latex_command = "%s -interaction=batchmode %s" % (self.setting('executable'), latex_filename)

        def run_cmd(command):
            self.log_debug("about to run %s in %s" % (command, os.path.abspath(wd)))
            proc = subprocess.Popen(command, shell=True,
                                    cwd=wd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    env=self.setup_env())

            stdout, stderr = proc.communicate()

            if proc.returncode > 2: # Set at 2 for now as this is highest I've hit, better to detect whether PDF has been generated?
                raise dexy.exceptions.UserFeedback("latex error, look for information in %s" %
                                latex_filename.replace(".tex", ".log"))
            elif proc.returncode > 0:
                self.log_warn("""A non-critical latex error has occurred running %s,
                status code returned was %s, look for information in %s""" % (
                self.key, proc.returncode,
                latex_filename.replace(".tex", ".log")))

        run_cmd(latex_command)

        self.copy_canonical_file()

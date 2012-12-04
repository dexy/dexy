from dexy.plugins.process_filters import SubprocessFilter
import codecs
import dexy.exceptions
import dexy.utils
import os
import subprocess

class LatexFilter(SubprocessFilter):
    """
    Generates a PDF file from LaTeX source.
    """
    INPUT_EXTENSIONS = [".tex", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf", ".png"]
    EXECUTABLES = ['pdflatex', 'latex']
    ALIASES = ['latex']
    FRAGMENT = False

    def command_string(self):
        clargs = self.command_line_args() or ''

        self.log.debug("Command line args specified by user '%s'" % clargs)

        if "-interaction=" in clargs:
            interaction_args = ''
        else:
            interaction_args = '-interaction=batchmode'

        args = {
            'prog' : self.executable(),
            'inter' : interaction_args,
            'args' : clargs,
            'input_file' : self.input().basename()
        }
        return "%(prog)s %(inter)s %(args)s %(input_file)s" % args

    def process(self):
        wd = self.setup_wd()
        env = self.setup_env()

        latex_command = self.command_string()

        bibtex_command = None
        if dexy.utils.command_exists("bibtex"):
            bibtex_command = "bibtex %s" % os.path.splitext(self.output().basename())[0]

        def run_cmd(command):
            self.log.info("running %s in %s" % (command, wd))
            proc = subprocess.Popen(command, shell=True,
                                    cwd=wd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    env=env)

            stdout, stderr = proc.communicate()
            self.log.debug(stdout)

        if bibtex_command:
            run_cmd(latex_command) #generate aux
            run_cmd(bibtex_command) #generate bbl

        run_cmd(latex_command) # first run
        run_cmd(latex_command) # second run - fix references
        run_cmd(latex_command) # third run - just to be sure

        if not os.path.exists(os.path.join(wd, self.output().basename())):
            msg = "Latex file not generated. Look for information in latex log in %s directory." % wd
            raise dexy.exceptions.UserFeedback(msg)

        if self.do_add_new_files():
            self.log.debug("adding new files found in %s for %s" % (self.artifact.tmp_dir(), self.artifact.key))
            self.add_new_files()

        self.copy_canonical_file()

class XelatexFilter(LatexFilter):
    """
    Runs .tex files using xelatex.
    """
    ALIASES = ['xetex', 'xelatex']
    EXECUTABLE = 'xelatex'

class TikzPgfFilter(LatexFilter):
    """
    Takes a snippet of Tikz code, wraps it in a LaTeX document, and renders it to PDF.
    """
    ALIASES = ['tikz']

    def process(self):
        latex_filename = self.output().basename().replace(self.artifact.ext, ".tex")

        # TODO allow setting tikz libraries per-document, or just include all of them?
        # TODO how to create a page size that just includes the content
        latex_header = """\documentclass[tikz]{standalone}
\usetikzlibrary{shapes.multipart}
\\begin{document}
        """
        latex_footer = "\n\end{document}"

        wd = self.setup_wd()

        work_path = os.path.join(wd, latex_filename)
        self.log.debug("writing latex header + tikz content to %s" % work_path)
        with codecs.open(work_path, "w", encoding="utf-8") as f:
            f.write(latex_header)
            f.write(self.input().as_text())
            f.write(latex_footer)

        latex_command = "%s -interaction=batchmode %s" % (self.executable(), latex_filename)

        def run_cmd(command):
            self.log.info("about to run %s in %s" % (command, wd))
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
                self.log.warn("""A non-critical latex error has occurred running %s,
                status code returned was %s, look for information in %s""" % (
                self.artifact.key, proc.returncode,
                latex_filename.replace(".tex", ".log")))

        run_cmd(latex_command)

        self.copy_canonical_file()

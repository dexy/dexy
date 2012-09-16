from dexy.plugins.process_filters import SubprocessFilter
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
    BINARY = True
    FINAL = True

    def process(self):
        wd = self.setup_wd()
        env = self.setup_env()

        latex_command = "%s -interaction=batchmode %s" % (self.executable(), self.input().basename())

        bibtex_command = None
        if dexy.utils.command_exists("bibtex"):
            bibtex_command = "bibtex %s" % os.path.splitext(self.result().basename())[0]

        self.artifact.stdout = ""

        def run_cmd(command):
            self.log.info("running %s in %s" % (command, wd))
            proc = subprocess.Popen(command, shell=True,
                                    cwd=wd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    env=env)

            stdout, stderr = proc.communicate()
            self.artifact.stdout += stdout

            if proc.returncode > 2: # Set at 2 for now as this is highest I've hit, better to detect whether PDF has been generated?
                raise dexy.commands.UserFeedback("latex error, look for information in %s" % wd)
            elif proc.returncode > 0:
                self.log.warn("""A non-critical latex error has occurred running %s,
                status code returned was %s, look for information in %s""" % (
                self.artifact.key, proc.returncode, wd))

        if bibtex_command:
            run_cmd(latex_command) #generate aux
            run_cmd(bibtex_command) #generate bbl
        run_cmd(latex_command) #first run
        run_cmd(latex_command) #second run - fix references

        self.copy_canonical_file()


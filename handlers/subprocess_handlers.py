from dexy.dexy_filter import DexyFilter
import os
import subprocess

class LatexHandler(DexyFilter):
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
        latex_filename = self.artifact.filename().replace(self.artifact.ext, ".tex")
        self.artifact.generate_workfile(latex_filename)

        if self.artifact.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.args['env'])
        else:
            env = None

        latex_command = "%s -interaction=batchmode %s" % (self.__class__.executable(), latex_filename)
        self.log.info(latex_command)

        if self.__class__.executable_present("bibtex"):
            bibtex_command = "bibtex %s" % (latex_filename)
        else:
            bibtex_command = None

        self.artifact.stdout = ""
        def run_cmd(command):
            proc = subprocess.Popen(command, shell=True,
                                    cwd=self.artifact.artifacts_dir,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    env=env)

            stdout, stderr = proc.communicate()
            self.artifact.stdout += stdout
            if proc.returncode > 1:
                raise Exception("latex error, look for information in %s" %
                                latex_filename.replace(".tex", ".log"))


        runbibtex = bibtex_command # TODO allow opting out of running bibtex in args
        if runbibtex:
            run_cmd(latex_command) #generate aux
            run_cmd(bibtex_command) #generate bbl
        run_cmd(latex_command) #first run
        run_cmd(latex_command) #second run - fix references


class EmbedFonts(DexyFilter):
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    EXECUTABLE = 'ps2pdf'
    ALIASES = ['embedfonts', 'prepress']
    FINAL = True
    BINARY = True

    def process(self):
        pf = self.artifact.previous_artifact_filename
        af = self.artifact.filename()

        env = None

        command = "%s -dPDFSETTINGS=/prepress %s %s" % (self.EXECUTABLE, pf, af)
        self.log.info(command)

        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout

        command = "%s %s" % ("pdffonts", af)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout += stdout

class Rd2PdfHandler(DexyFilter):
    INPUT_EXTENSIONS = [".Rd"]
    OUTPUT_EXTENSIONS = [".pdf", ".dvi"]
    EXECUTABLE = 'R CMD Rd2pdf'
    VERSION = 'R CMD Rd2pdf -v'
    ALIASES = ['rd2pdf', 'Rd2pdf']
    FINAL = True

    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename()
        af = self.artifact.filename()
        title = os.path.splitext(self.artifact.name)[0].replace("_", " ")
        command = "%s --output=%s --title=\"%s\" %s" % (self.executable(), af,
                                                    title, wf)
        self.log.info(command)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout

class RBatchHandler(DexyFilter):
    """Runs R code in batch mode."""
    EXECUTABLE = 'R CMD BATCH --vanilla --quiet --no-timing'
    VERSION = "R --version"
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rintbatch']

    def process(self):
        self.artifact.generate_workfile()
        work_file = os.path.basename(self.artifact.work_filename())
        artifact_file = os.path.basename(self.artifact.filename())
        command = "%s %s %s" % (self.EXECUTABLE, work_file, artifact_file)
        self.log.info(command)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout
        self.artifact.set_data_from_artifact()

class ROutputBatchHandler(DexyFilter):
    """Runs R code in batch mode. Uses the --slave flag so doesn't echo commands, just returns output."""
    EXECUTABLE = 'R CMD BATCH --vanilla --quiet --slave --no-timing'
    VERSION = "R --version"
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['routbatch']

    def process(self):
        self.artifact.generate_workfile()
        work_file = os.path.basename(self.artifact.work_filename())
        artifact_file = os.path.basename(self.artifact.filename())
        command = "%s %s %s" % (self.EXECUTABLE, work_file, artifact_file)
        self.log.info(command)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout
        self.artifact.set_data_from_artifact()

class DotHandler(DexyFilter):
    """
    Renders .dot files to either PNG or PDF images.
    """
    INPUT_EXTENSIONS = [".dot"]
    OUTPUT_EXTENSIONS = [".png", ".pdf"]
    EXECUTABLE = 'dot'
    VERSION = 'dot -V'
    ALIASES = ['dot', 'graphviz']
    FINAL = True
    BINARY = True

    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename()
        af = self.artifact.filename()
        ex = self.artifact.ext.replace(".", "")
        command = "%s -T%s -o%s %s" % (self.executable(), ex, af, wf)
        self.log.info(command)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout
        self.artifact.set_data_from_artifact()

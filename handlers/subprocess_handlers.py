from dexy.handler import DexyHandler
import os
import subprocess

class LatexHandler(DexyHandler):
    """
    Generates a PDF file from LaTeX source.
    """
    INPUT_EXTENSIONS = [".tex", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf", ".png"]
    ALIASES = ['latex']
    BINARY = True
    FINAL = True

    def process(self):
        latex_filename = self.artifact.filename().replace(".pdf", ".tex")
        self.artifact.generate_workfile(latex_filename)

        if self.doc.args.has_key('env'):
            env = os.environ
            env.update(self.doc.args['env'])
        else:
            env = None

        # Detect which LaTeX compiler we have...
        latex_bin = None
        for e in ["pdflatex", "latex"]:
            which_cmd = ['which', e]
            if subprocess.call(which_cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
                latex_bin = e
                self.log.info("%s LaTeX command found" % e)
                break
            else:
                self.log.info("%s LaTeX command not found" % e)
                latex_bin = None

        if not latex_bin:
            raise Exception("no executable found for latex")

        command = "%s %s" % (e, latex_filename)
        self.log.info(command)

        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout

        # Run LaTeX again for TOC numbering etc.
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout += stdout

class EmbedFonts(DexyHandler):
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    EXECUTABLE = 'ps2pdf'
    ALIASES = ['embedfonts', 'prepress']
    FINAL = True

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

class Rd2PdfHandler(DexyHandler):
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
        title = os.path.splitext(self.doc.name)[0].replace("_", " ")
        command = "%s --output=%s --title=\"%s\" %s" % (self.executable(), af,
                                                    title, wf)
        self.log.info(command)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout

class RBatchHandler(DexyHandler):
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

class ROutputBatchHandler(DexyHandler):
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

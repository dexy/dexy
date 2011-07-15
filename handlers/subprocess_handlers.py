from dexy.dexy_filter import DexyFilter
import os
import re
import subprocess

class RagelRubyHandler(DexyFilter):
    """
    Runs ragel for ruby.
    """
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".rb"]
    ALIASES = ['rlrb', 'ragelruby']
    VERSION = 'ragel --version'
    EXECUTABLE = 'ragel -R'

    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename()
        command = "%s %s -o %s" % (self.executable(), wf, self.artifact.filename())

        if self.artifact.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.args['env'])
        else:
            env = None

        self.log.info("running: %s" % command)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout

class BibHandler(DexyFilter):
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['bib']

    """Filter which replaces a hard-coded bibtex file with a .bib file specified as an input."""
    def process_text(self, input_text):
        for k, a in self.artifact.inputs().items():
            if a.filename().endswith("bib"):
                bib_file_basename = os.path.splitext(os.path.basename(a.name))[0]

                input_text = re.sub("bibliography{[^}]+}", "bibliography{%s}" % a.filename(), input_text)

        return input_text

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

        if self.__class__.executable_present("bibtex"):
            bibtex_command = "bibtex %s" % os.path.splitext(self.artifact.filename())[0]
        else:
            bibtex_command = None

        self.artifact.stdout = ""
        def run_cmd(command):
            self.log.info("running: %s" % command)
            proc = subprocess.Popen(command, shell=True,
                                    cwd=self.artifact.artifacts_dir,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    env=env)

            stdout, stderr = proc.communicate()
            self.artifact.stdout += stdout
            if proc.returncode > 2: # Set at 2 for now as this is highest I've hit, better to detect whether PDF has been generated?
                raise Exception("latex error, look for information in %s" %
                                latex_filename.replace(".tex", ".log"))
            elif proc.returncode > 0:
                print """A non-critical latex error has occurred running %s,
                status code returned was %s, look for information in %s""" % (
                self.artifact.key, proc.returncode,
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

class RubyInteractiveHandler(DexyFilter):
    """Run Ruby, takign input from input files."""
    VERSION = "ruby --version"
    EXECUTABLE = "ruby"
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rbint']

    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename()
        command = "%s %s" % (self.EXECUTABLE, wf)
        self.log.debug(command)
        for k, a in self.artifact.inputs().items():
            for s, t in a.data_dict.items():
                proc = subprocess.Popen(command, shell=True,
                                        cwd=self.artifact.artifacts_dir,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                       )
                stdout, stderr = proc.communicate(t)
                self.artifact.data_dict[s] = stdout
                self.artifact.stdout = stdout + "\n" + stderr


from dexy.dexy_filter import DexyFilter
import os
import re
import shutil
import subprocess

class BibFilter(DexyFilter):
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['bib']

    """Filter which replaces a hard-coded bibtex file with a .bib file specified as an input."""
    def process_text(self, input_text):
        for k, a in self.artifact.inputs().items():
            if a.filename().endswith("bib"):
                input_text = re.sub("bibliography{[^}]+}", "bibliography{%s}" % a.filename(), input_text)

        return input_text

class SedFilter(DexyFilter):
    EXECUTABLES = ['sed']
    ALIASES = ['sed']

    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename()

        if self.artifact.args.has_key('sed'):
            sed_script = self.artifact.args['sed']
            command = "%s -e %s %s" % (self.__class__.executable(), sed_script, wf)
        else:
            sed_file = None
            for k, a in self.artifact.inputs().items():
                if a.filename().endswith("sed"):
                    sed_file = a.filename()
                    self.log.debug("Found sed script %s" % sed_file)
                    break
            if not sed_file:
                raise Exception("must pass a 'sed' argument or have an input with .sed file extension")
            command = "%s -f %s %s" % (self.__class__.executable(), sed_file, wf)

        env = None
        self.log.debug(command)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)
        stdout, stderr = proc.communicate()
        self.artifact.set_data(stdout)

class HtLatexFilter(DexyFilter):
    """
    Generates HTML from LaTeX source.
    """
    INPUT_EXTENSIONS = [".tex", ".txt"]
    OUTPUT_EXTENSIONS = [".html"]
    EXECUTABLES = ['htlatex']
    ALIASES = ['htlatex']
    FINAL = True

    def process(self):
        self.artifact.create_temp_dir()
        wf = os.path.join(self.artifact.temp_dir(), os.path.basename(self.artifact.name))

        f = open(wf, "w")
        f.write(self.artifact.input_text())
        f.close()

        if self.artifact.args.has_key('htlatex'):
            htlatex_args = self.artifact.args['htlatex']
        else:
            htlatex_args = ""


        command = "%s %s %s" % (self.__class__.executable(), os.path.basename(self.artifact.name), htlatex_args)
        self.log.info("running: %s" % command)
        env = None
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.temp_dir(),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)
        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout

        html_filename = wf.replace(".tex", ".html")

        # The main HTML file generated.
        f = open(html_filename, "r")
        self.artifact.set_data(f.read())
        f.close()

        for f in os.listdir(self.artifact.temp_dir()):
            basefilepath = os.path.dirname(self.artifact.name)
            f_ext = os.path.splitext(f)[1]

            # handle text-based output
            if (f_ext in [".css", ".html"]) and f != self.artifact.name.replace(".tex", ".html"):
                f_key = os.path.join(basefilepath, f)
                new_artifact = self.artifact.add_additional_artifact(f_key, f_ext)
                with open(os.path.join(self.artifact.temp_dir(), f), "r") as generated_file:
                    new_artifact.set_data(generated_file.read())

            # handle binary output
            if f_ext in [".png"]:
                f_key = os.path.join(basefilepath, f)
                new_artifact = self.artifact.add_additional_artifact(f_key, f_ext)
                shutil.copyfile(os.path.join(self.artifact.temp_dir(), f), new_artifact.filepath())

class LatexFilter(DexyFilter):
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
                self.log.warn("""A non-critical latex error has occurred running %s,
                status code returned was %s, look for information in %s""" % (
                self.artifact.key, proc.returncode,
                latex_filename.replace(".tex", ".log")))


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

class SubprocessFilter(DexyFilter):
    ALIASES = None
    BINARY = True
    FINAL = True

    def command_string(self):
        """
        Should return a command string that, when run, should result in filter
        output being present in the artifact file.
        """
        wf = self.artifact.previous_artifact_filename
        of = self.artifact.filename()
        return "%s %s %s" % (self.executable(), wf, of)

    def setup_env(self):
        if self.artifact.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.args['env'])
        else:
            env = None
        return env

    def process(self):
        command = self.command_string()
        proc = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(proc.returncode, self.artifact.stdout)

    def run_command(self, command, env):
        """
        Runs a command using subprocess.Popen.
        """
        self.log.debug("about to run '%s'" % command)
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout
        return proc

class ROutputBatchFilter(SubprocessFilter):
    """Runs R code in batch mode. Uses the --slave flag so doesn't echo commands, just returns output."""
    ALIASES = ['rout', 'routbatch']
    EXECUTABLE = 'R CMD BATCH --vanilla --quiet --slave --no-timing'
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "R --version"
    BINARY = False
    FINAL = False

class RBatchFilter(SubprocessFilter):
    """Runs R code in batch mode."""
    ALIASES = ['rintbatch']
    EXECUTABLE = 'R CMD BATCH --vanilla --quiet --no-timing'
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".Rout", '.txt']
    VERSION = "R --version"
    BINARY = False
    FINAL = False

class Rd2PdfFilter(SubprocessFilter):
    INPUT_EXTENSIONS = [".Rd"]
    OUTPUT_EXTENSIONS = [".pdf", ".dvi"]
    EXECUTABLE = 'R CMD Rd2pdf'
    VERSION = 'R CMD Rd2pdf -v'
    ALIASES = ['rd2pdf', 'Rd2pdf']

    def command_string(self):
        title = os.path.splitext(self.artifact.name)[0].replace("_", " ")
        args = {
            'prog' : self.executable(),
            'out' : self.artifact.filename(),
            'in' : self.artifact.previous_artifact_filename,
            'title' : title
        }
        return "%(prog)s --output=%(out)s --title=\"%(title)s\" %(in)s" % args

class RagelRubyFilter(SubprocessFilter):
    """
    Runs ragel for ruby.
    """
    ALIASES = ['rlrb', 'ragelruby']
    BINARY = False
    EXECUTABLE = 'ragel -R'
    FINAL = False
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".rb"]
    VERSION = 'ragel --version'

    def command_string(self):
        wf = self.artifact.previous_artifact_filename
        of = self.artifact.filename()
        return "%s %s -o %s" % (self.executable(), wf, of)

class Ps2PdfFilter(SubprocessFilter):
    """
    Converts a postscript file to PDF format.
    """
    ALIASES = ['ps2pdf']
    EXECUTABLE = 'ps2pdf'
    INPUT_EXTENSIONS = [".ps", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf"]

class Html2PdfFilter(SubprocessFilter):
    """
    Renders HTML to PDF using wkhtmltopdf
    """
    ALIASES = ['html2pdf', 'wkhtmltopdf']
    EXECUTABLE = 'wkhtmltopdf'
    INPUT_EXTENSIONS = [".html", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf"]
    VERSION = 'wkhtmltopdf --version'

    def command_string(self):
        # Create a temporary directory and populate it with all inputs.
        self.artifact.create_temp_dir(populate=True)
        workfile = os.path.join(self.artifact.hashstring, self.artifact.previous_canonical_filename)

        args = {
            'prog' : self.executable(),
            'in' : workfile,
            'out' : self.artifact.filename()
        }
        return "%(prog)s %(in)s %(out)s" % args

class DotFilter(SubprocessFilter):
    """
    Renders .dot files to either PNG or PDF images.
    """
    INPUT_EXTENSIONS = [".dot"]
    OUTPUT_EXTENSIONS = [".png", ".pdf"]
    EXECUTABLE = 'dot'
    VERSION = 'dot -V'
    ALIASES = ['dot', 'graphviz']

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'format' : self.artifact.ext.replace(".",""),
            'workfile' : self.artifact.previous_artifact_filename,
            'outfile' : self.artifact.filename()
        }
        return "%(prog)s -T%(format)s -o%(outfile)s %(workfile)s" % args

class Pdf2ImgFilter(SubprocessFilter):
    """
    Converts a PDF file to a PNG image using ghostscript (subclass this to
    convert to other image types).

    Returns the image generated by page 1 of the PDF by default, the optional
    'page' parameter can be used to specify other pages.
    """
    ALIASES = ['pdf2img', 'pdf2png']
    EXECUTABLE = "gs"
    GS_DEVICE = 'png16m -r300'
    INPUT_EXTENSIONS = ['.pdf']
    OUTPUT_EXTENSIONS = ['.png']
    VERSION = "gs --version"

    def command_string(self):
        s = "%(prog)s -dSAFER -dNOPAUSE -dBATCH -sDEVICE=%(device)s -sOutputFile=%%d-%(out)s %(in)s"
        args = {
            'prog' : self.executable(),
            'device' : self.GS_DEVICE,
            'in' : self.artifact.previous_artifact_filename,
            'out' : self.artifact.filename()
        }
        return s % args

    def process(self):
        command = self.command_string()
        proc = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(proc.returncode, self.artifact.stdout)

        if self.artifact.args.has_key('page'):
            page = self.artifact.args['page']
        else:
            page = 1

        page_file = os.path.join(self.artifact.artifacts_dir, "%s-%s" % (page, self.artifact.filename()))
        shutil.copyfile(page_file, self.artifact.filepath())

class Pdf2JpgFilter(Pdf2ImgFilter):
    ALIASES = ['pdf2jpg']
    GS_DEVICE = 'jpeg'
    OUTPUT_EXTENSIONS = ['.jpg']

class RubyInteractiveFilter(SubprocessFilter):
    """Run Ruby, taking input from input files."""
    ALIASES = ['rbint']
    BINARY = False
    EXECUTABLE = "ruby"
    FINAL = False
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "ruby --version"

    def process(self):
        command = "%s %s" % (self.EXECUTABLE, self.artifact.previous_artifact_filename)
        self.log.debug(command)

        self.artifact.stdout = ""

        # Loop over all inputs
        for k, a in self.artifact.inputs().items():

            # For each input, loop over all sections
            for s, t in a.data_dict.items():
                proc = subprocess.Popen(command, shell=True,
                                        cwd=self.artifact.artifacts_dir,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        env=self.setup_env()
                                       )
                stdout, stderr = proc.communicate(t)
                self.artifact.data_dict[s] = stdout
                self.artifact.stdout += stderr

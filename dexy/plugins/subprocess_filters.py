from dexy.common import OrderedDict
from dexy.plugins.process_filters import SubprocessFilter
from dexy.plugins.process_filters import SubprocessInputFilter
import dexy.exceptions
import json
import os
import shutil

class PythonInput(SubprocessInputFilter):
    """
    Runs python code and passes input.
    """
    EXECUTABLE = 'python'
    ALIASES = ['pyin']
    VERSION_COMMAND = 'python --version'
    OUTPUT_EXTENSIONS = ['.txt']

class Pdfcrop(SubprocessFilter):
    """
    Runs the PDFcrop script http://pdfcrop.sourceforge.net/
    """
    ALIASES = ['pdfcrop']
    EXECUTABLE = 'pdfcrop'
    INPUT_EXTENSIONS = ['.pdf']
    OUTPUT_EXTENSIONS = ['.pdf']

class CalibreFilter(SubprocessFilter):
    """
    Invokes ebook-convert command line tool (part of calibre) to generate various output formats (including .mobi for Kindle)

    http://manual.calibre-ebook.com/cli/ebook-convert.html
    """
    ADD_NEW_FILES = False
    ALIASES = ['calibre', 'ebook']
    EXECUTABLE = "ebook-convert"
    FRAGMENT = False
    INPUT_EXTENSIONS = ['.html', '.epub', '.azw', '.chm', '.comic', '.djvu',
            '.pdf', '.mobi', '.lit', '.fb2']
    OUTPUT_EXTENSIONS = ['.mobi', '.epub', '.fb2', '.htmlz', '.lit', '.lrf',
            '.pdf', '.rtf', '.snb', '.tcr', '.txt', '.txtz', '.html', '.pml']
    PATH_EXTENSIONS = ['/Applications/calibre.app/Contents/MacOS']
    VERSION_COMMAND = "ebook-convert --version"

#    TODO: output oeb (outputs a directory)
#    TODO: output azw
#    TODO: test with html, pml plugins

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'input_file' : self.input_filename(),
            'output_file' : self.output_filename()
        }
        return """%(prog)s "%(input_file)s" "%(output_file)s" %(args)s""" % args

class LyxFilter(SubprocessFilter):
    """
    Invokes lyx on the command line. By default generates a latex file.
    """
    EXECUTABLE = 'lyx'
    ALIASES = ['lyx']
    VERSION_COMMAND = 'lyx -version'
    OUTPUT_EXTENSIONS = ['.tex', '.pdf', '.lyx']

    def command_string(self):
        cl_args = self.command_line_args()
        if cl_args and ("-e" in cl_args):
            format_string = ''
        else:
            format_string = "-e latex"

        args = {
            'format_string' : format_string,
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'input_file' : self.input_filename(),
        }
        return "%(prog)s %(format_string)s %(args)s %(input_file)s" % args

class PandocFilter(SubprocessFilter):
    """
    Converts documents using pandoc.
    """
    EXECUTABLE = "pandoc"
    VERSION_COMMAND = "pandoc --version"
    ALIASES = ['pandoc']
    OUTPUT_EXTENSIONS = ['.html', '.txt', '.tex', '.pdf', '.rtf', '.json', '.docx', '.odt', '.epub']
    FRAGMENT = False
    ADD_NEW_FILES = False

    # TODO Support all these + test them.
    #Output formats: native, json, html, html5, html+lhs, html5+lhs, s5, slidy,
    #                dzslides, docbook, opendocument, latex, latex+lhs, beamer,
    #                context, texinfo, man, markdown, markdown+lhs, plain, rst,
    #                rst+lhs, mediawiki, textile, rtf, org, asciidoc, odt, docx,
    #                epub

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'script_file' : self.input_filename(),
            'output_file' : self.output_filename()
        }
        return "%(prog)s %(args)s %(script_file)s -o %(output_file)s" % args

class EspeakFilter(SubprocessFilter):
    """
    Runs espeak text to speech.
    """
    EXECUTABLE = "espeak"
    INP2UT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".wav"]
    ALIASES = ['espeak']

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'scriptargs' : self.command_line_scriptargs() or "",
            'script_file' : self.input_filename(),
            'output_file' : self.output_filename()
        }
        return "%(prog)s %(args)s -w %(output_file)s %(script_file)s" % args

class AsciidocFilter(SubprocessFilter):
    """
    Converts ASCIIDOC input.
    """
    VERSION_COMMAND = "asciidoc --version"
    EXECUTABLE = "asciidoc"
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".html", ".xml"]
    ALIASES = ['asciidoc']

    def command_string(self):
        if self.args().has_key('backend'):
            backend = self.arg_value('backend')
            # TODO check file extension is valid for backend
        else:
            if self.artifact.ext == ".html":
                if self.version() >= "asciidoc 8.6.5":
                    backend = 'html5'
                else:
                    backend = 'html4'
            elif self.artifact.ext == ".xml":
                backend = "docbook45"
            elif self.artifact.ext == ".tex":
                backend = "latex"
            else:
                raise Exception("unexpected file extension in asciidoc filter %s" % self.artifact.ext)

        args = {
            'backend' : backend,
            'infile' : self.input_filename(),
            'outfile' : self.output_filename(),
            'prog' : self.executable(),
            'args' : self.command_line_args() or ""
        }

        return "%(prog)s -b %(backend)s %(args)s -o %(outfile)s %(infile)s" % args

class BlackWhitePdfFilter(SubprocessFilter):
    """
    Converts color pdf to black and white.
    """
    EXECUTABLE = "gs"
    ALIASES = ['bw', 'bwconv']
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'in' : self.input_filename(),
            'out' : self.output_filename()
        }
        s = "%(prog)s -dSAFER -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sColorConversionStrategy=Gray -dProcessColorModel=/DeviceGray -sOutputFile=%(out)s %(in)s"
        return s % args

class Pdf2ImgSubprocessFilter(SubprocessFilter):
    """
    Converts a PDF file to a PNG image using ghostscript.

    Returns the image generated by page 1 of the PDF by default, the
    'page' parameter can be used to specify other pages.
    """
    ALIASES = ['pdf2img', 'pdf2png']
    EXECUTABLE = "gs"
    GS_DEVICE = 'png16m -r300'
    INPUT_EXTENSIONS = ['.pdf']
    OUTPUT_EXTENSIONS = ['.png']
    VERSION_COMMAND = "gs --version"

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'device' : self.GS_DEVICE,
            'in' : self.input_filename(),
            'out' : self.output_filename()
        }
        s = "%(prog)s -dSAFER -dNOPAUSE -dBATCH -sDEVICE=%(device)s -sOutputFile=%%d-%(out)s %(in)s"
        return s % args

    def process(self):
        command = self.command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)


        page = self.args().get('page', 1)
        page_file = "%s-%s" % (page, self.output().basename())

        wd = self.setup_wd()
        page_path = os.path.join(wd, page_file)
        shutil.copyfile(page_path, self.output_filepath())

class Pdf2JpgSubprocessFilter(Pdf2ImgSubprocessFilter):
    """
    Converts a PDF file to a jpg image using ghostscript.

    Returns the image generated by page 1 of the PDF by default, the
    'page' parameter can be used to specify other pages.
    """
    ALIASES = ['pdf2jpg']
    GS_DEVICE = 'jpeg'
    OUTPUT_EXTENSIONS = ['.jpg']

class DotFilter(SubprocessFilter):
    """
    Renders .dot files to either PNG or PDF images.
    """
    INPUT_EXTENSIONS = [".dot"]
    OUTPUT_EXTENSIONS = [".png", ".pdf"]
    EXECUTABLE = 'dot'
    VERSION_COMMAND = 'dot -V'
    ALIASES = ['dot', 'graphviz']

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'format' : self.artifact.ext.replace(".",""),
            'workfile' : self.input_filename(),
            'outfile' : self.output_filename()
        }
        return "%(prog)s -T%(format)s -o%(outfile)s %(workfile)s" % args

class Html2PdfSubprocessFilter(SubprocessFilter):
    """
    Renders HTML to PDF using wkhtmltopdf. If the HTML relies on assets such as
    CSS or image files, these should be specified as inputs.

    If you have an older version of wkhtmltopdf, and are running on a server,
    you may get XServer errors. You can install xvfb and run Dexy as
    "xvfb-run dexy". Or upgrade to the most recent wkhtmltopdf which only needs
    X11 client libs.
    """
    ALIASES = ['html2pdf', 'wkhtmltopdf']
    EXECUTABLE = 'wkhtmltopdf'
    INPUT_EXTENSIONS = [".html", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf"]
    VERSION_COMMAND = 'wkhtmltopdf --version'

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'in' : self.input_filename(),
            'out' : self.output_filename()
        }
        return "%(prog)s %(in)s %(out)s" % args

class Ps2PdfSubprocessFilter(SubprocessFilter):
    """
    Converts a postscript file to PDF format.
    """
    ALIASES = ['ps2pdf']
    EXECUTABLE = 'ps2pdf'
    INPUT_EXTENSIONS = [".ps", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf"]

class RagelRubySubprocessFilter(SubprocessFilter):
    """
    Generates ruby source code from a ragel file.
    """
    ALIASES = ['rlrb', 'ragelruby']
    EXECUTABLE = 'ragel -R'
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".rb"]
    VERSION_COMMAND = 'ragel --version'

    def command_string(self):
        wf = self.input_filename()
        of = self.output_filename()
        return "%s %s -o %s" % (self.executable(), wf, of)

class Rd2PdfFilter(SubprocessFilter):
    """
    Generates a pdf from R documentation file.
    """
    INPUT_EXTENSIONS = [".Rd"]
    OUTPUT_EXTENSIONS = [".pdf", ".dvi"]
    EXECUTABLE = 'R CMD Rd2pdf'
    VERSION_COMMAND = 'R CMD Rd2pdf -v'
    ALIASES = ['rd2pdf', 'Rd2pdf']

    def command_string(self):
        title = self.baserootname().replace("_", " ")
        args = {
            'prog' : self.executable(),
            'out' : self.output_filename(),
            'in' : self.input_filename(),
            'title' : title
        }
        return "%(prog)s --output=%(out)s --title=\"%(title)s\" %(in)s" % args

class RBatchFilter(SubprocessFilter):
    """Runs R code in batch mode."""
    ADD_NEW_FILES = True
    ALIASES = ['rintbatch']
    EXECUTABLE = 'R CMD BATCH --quiet --no-timing'
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".Rout", '.txt']
    VERSION_COMMAND = "R --version"

class RIntBatchSectionsFilter(SubprocessFilter):
    """
    Experimental filter to run R in sections without using pexpect.
    """
    ADD_NEW_FILES = True
    ALIASES = ['rintmock']
    EXECUTABLE = 'R CMD BATCH --quiet --no-timing'
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".Rout", '.txt']
    VERSION_COMMAND = "R --version"
    WRITE_STDERR_TO_STDOUT = False
    OUTPUT_DATA_TYPE = 'sectioned'

    def command_string(self, section_name, section_text, wd):
        br = self.input().baserootname()
        work_file = "%s-%s%s" % (br, section_name, self.input().ext)
        outfile = "%s-%s-out%s" % (br, section_name, self.output().ext)

        work_filepath = os.path.join(wd, work_file)

        with open(work_filepath, "wb") as f:
            f.write(section_text)

        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'script_file' : work_file,
            'scriptargs' : self.command_line_scriptargs() or "",
            'output_file' : outfile
        }

        command = """%(prog)s %(args)s "%(script_file)s" %(scriptargs)s "%(output_file)s" """ % args
        return command, outfile

    def process(self):
        wd = self.setup_wd()

        result = OrderedDict()

        for section_name, section_text in self.input().as_sectioned().iteritems():
            command, outfile = self.command_string(section_name, section_text, wd)
            proc, stdout = self.run_command(command, self.setup_env())
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)

            with open(os.path.join(wd, outfile), "rb") as f:
                result[section_name] = f.read()

        if self.do_walk_working_directory():
            self.walk_working_directory()

        if self.do_add_new_files():
            self.add_new_files()

        self.output().set_data(result)

class ROutputBatchFilter(SubprocessFilter):
    """Runs R code in batch mode. Uses the --slave flag so doesn't echo commands, just returns output."""
    ADD_NEW_FILES = True
    ALIASES = ['rout', 'routbatch']
    EXECUTABLE = 'R CMD BATCH --vanilla --quiet --slave --no-timing'
    INPUT_EXTENSIONS = ['.R', '.r', '.txt']
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = "R --version"

class EmbedFonts(SubprocessFilter):
    """
    Use to embed fonts and do other prepress as required for some types of printing.
    """
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    EXECUTABLE = 'ps2pdf'
    ALIASES = ['embedfonts', 'prepress']

    def preprocess_command_string(self):
        pf = self.input_filename()
        af = self.output_filename()
        return "%s -dPDFSETTINGS=/prepress %s %s" % (self.EXECUTABLE, pf, af)

    def pdffonts_command_string(self):
        return "%s %s" % ("pdffonts", self.result().name)

    def process(self):
        env = self.setup_env()

        command = self.preprocess_command_string()
        proc, stdout = self.run_command(command, env)
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        command = self.pdffonts_command_string()
        proc, stdout = self.run_command(command, env)
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        self.copy_canonical_file()

class HtLatexFilter(SubprocessFilter):
    """
    Generates HTML from LaTeX source.
    """
    INPUT_EXTENSIONS = [".tex", ".txt"]
    OUTPUT_EXTENSIONS = [".html"]
    EXECUTABLES = ['htlatex']
    ALIASES = ['htlatex']
    ADD_NEW_FILES = [".html", ".png", ".css"]

    def command_string(self):
        latexargs = self.args().get('latexargs', '')

        if not '-interaction=' in latexargs:
            latexargs = latexargs + ' -interaction=batchmode'

        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or '',
            'tex4htargs' : self.args().get('tex4htargs', ''),
            't4htargs' : self.args().get('t4htargs', ''),
            'latexargs' : latexargs,
            'script_file' : self.input_filename()
        }
        return """%(prog)s %(script_file)s "%(args)s" "%(tex4htargs)s" "%(t4htargs)s" "%(latexargs)s" """ % args

class AbcFilter(SubprocessFilter):
    """
    Runs abc to convert abc music notation to one of the available output formats.
    """
    ADD_NEW_FILES = False
    ALIASES = ['abc']
    EXECUTABLE = 'abcm2ps'
    FRAGMENT = False
    INPUT_EXTENSIONS = ['.abc']
    OUTPUT_EXTENSIONS = ['.svg', '.html', '.xhtml', '.eps']

    def command_string(self):
        clargs = self.command_line_args() or ''

        if not any(x in clargs for x in ['-E', '-g', '-v', '-X']):
            if self.artifact.ext in ('.eps'):
                output_flag = '-E'
            elif self.artifact.ext in ('.svg'):
                output_flag = '-g'
            elif self.artifact.ext in ('.html', '.xhtml'):
                output_flag = '-X'
            else:
                raise dexy.exceptions.UserFeedback("File extension %s is not supported for abc filter. Supported extensions are %s" % (self.artifact.ext, ", ".join(self.OUTPUT_EXTENSIONS)))
        else:
            output_flag = ''

        args = {
            'prog' : self.executable(),
            'args' : clargs,
            'output_flag' : output_flag,
            'script_file' : self.input_filename(),
            'output_file' : self.output_filename()
        }
        return "%(prog)s %(args)s %(output_flag)s -O %(output_file)s %(script_file)s" % args

    def process(self):
        command = self.command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        if self.artifact.ext in ('.svg', '.eps'):
            # Fix for abcm2ps adding 001 to file name.
            nameparts = os.path.splitext(self.output().name)
            output_filename = "%s001%s" % (nameparts[0], nameparts[1])
            output_filepath = os.path.join(self.artifact.tmp_dir(), output_filename)
            self.output().copy_from_file(output_filepath)
        else:
            self.copy_canonical_file()

        if self.do_add_new_files():
            self.log.debug("adding new files found in %s for %s" % (self.artifact.tmp_dir(), self.artifact.key))
            self.add_new_files()

class AbcMultipleFormatsFilter(SubprocessFilter):
    """
    Runs abc to convert abc music notation to all of the available output formats.
    """
    ALIASES = ['abcm']
    INPUT_EXTENSIONS = ['.abc']
    OUTPUT_EXTENSIONS = ['.json']
    EXECUTABLE = 'abcm2ps'
    ADD_NEW_FILES = False

    def command_string(self, ext):
        clargs = self.command_line_args() or ''

        if any(x in clargs for x in ['-E', '-g', '-v', '-X']):
            raise dexy.exceptions.UserFeedback("Please do not pass any output format flags!")

        if ext in ('.eps'):
            output_flag = '-E'
        elif ext in ('.svg'):
            output_flag = '-g'
        elif ext in ('.html', '.xhtml'):
            output_flag = '-X'
        else:
            raise dexy.exceptions.InternalDexyProblem("bad ext '%s'" % ext)

        args = {
            'prog' : self.executable(),
            'args' : clargs,
            'output_flag' : output_flag,
            'script_file' : self.input_filename(),
            'output_file' : self.output_workfile(ext)
        }
        return "%(prog)s %(args)s %(output_flag)s -O %(output_file)s %(script_file)s" % args

    def output_workfile(self, ext):
        return "%s%s" % (self.artifact.output_data.baserootname(), ext)

    def process(self):
        output = {}

        for ext in ('.eps', '.svg', '.html', '.xhtml'):
            command = self.command_string(ext)
            proc, stdout = self.run_command(command, self.setup_env())
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)

            if ext in ('.svg', '.eps'):
                # Fix for abcm2ps adding 001 to file name.
                nameparts = os.path.splitext(self.output_workfile(ext))
                output_filename = "%s001%s" % (nameparts[0], nameparts[1])
                output_filepath = os.path.join(self.artifact.tmp_dir(), output_filename)
            else:
                output_filename = self.output_workfile(ext)
                output_filepath = os.path.join(self.artifact.tmp_dir(), output_filename)

            with open(output_filepath, "r") as f:
                output[ext] = f.read()

        self.output().set_data(json.dumps(output))

class RdConv(SubprocessFilter):
    """Convert R documentation to other formats."""
    EXECUTABLE = "R CMD Rdconv"
    VERSION_COMMAND = "R CMD Rdconv -v"
    INPUT_EXTENSIONS = ['.Rd']
    OUTPUT_EXTENSIONS = ['.txt', '.html', '.tex', '.R']
    ALIASES = ['rdconv']
    EXTENSION_TO_FORMAT = {
        '.txt' : 'txt',
        '.html' : 'html',
        '.tex' : 'latex',
        '.R' : 'example'
    }

    def command_string(self):
        args = {
                'exe' : self.executable(),
                'clargs' : self.command_line_args() or "",
                'fmt' : self.EXTENSION_TO_FORMAT[self.artifact.ext],
                'input' : self.input_filename(),
                'output' : self.output_filename()
                }
        return "%(exe)s %(clargs)s --type=%(fmt)s --output=%(output)s %(input)s" % args

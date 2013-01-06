from dexy.plugins.process_filters import SubprocessFilter
from dexy.plugins.process_filters import SubprocessStdoutFilter
import os

class CasperJsSvg2PdfFilter(SubprocessFilter):
    """
    Converts an SVG file to PDF by running it through casper js.
    # TODO convert this to phantomjs, no benefit to using casper here (js is not user facing) and more restrictive
    """
    ADD_NEW_FILES = True
    ALIASES = ['svg2pdf']
    EXECUTABLE = 'casperjs'
    INPUT_EXTENSIONS = ['.svg']
    OUTPUT_EXTENSIONS = ['.pdf']
    VERSION_COMMAND = 'casperjs --version'

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or ""
        }
        return "%(prog)s %(args)s script.js" % args

    def script_js(self, width, height):
        args = {
                'width' : width,
                'height' : height,
                'svgfile' : self.input_filename(),
                'pdffile' : self.output_filename()
                }
        return """
        var casper = require('casper').create({
             viewportSize : {width : %(width)s, height : %(height)s}
        });
        casper.start('%(svgfile)s', function() {
            this.capture('%(pdffile)s');
        });

        casper.run();
        """ % args

    def setup_wd(self):
        wd = self.artifact.working_dir()
        if not os.path.exists(wd):
            for doc, filename in self.artifact.setup_wd(self.input_filename()):
                self.write_to_wd(wd, doc, filename)

        width = self.args().get('width', 200)
        height = self.args().get('height', 200)
        js = self.script_js(width, height)

        wd = os.path.join(self.artifact.tmp_dir(), self.input().parent_dir())
        scriptfile = os.path.join(wd, "script.js")
        self.log.debug("scriptfile: %s" % scriptfile)
        with open(scriptfile, "w") as f:
            f.write(js)

        return wd

class CasperJsStdoutFilter(SubprocessStdoutFilter):
    """
    Runs scripts using casper js. Saves cookies.
    """
    ALIASES = ['casperjs']
    ADD_NEW_FILES = True
    EXECUTABLE = 'casperjs'
    INPUT_EXTENSIONS = ['.js', '.txt']
    OUTPUT_EXTENSIONS = ['.txt']
    VERSION_COMMAND = 'casperjs --version'

    def command_string_stdout(self):
        args = {
            'cookie_file' : 'cookies.txt',
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'scriptargs' : self.command_line_scriptargs() or "",
            'script_file' : self.input_filename()
        }
        return "%(prog)s --cookies-file=%(cookie_file)s %(args)s %(script_file)s %(scriptargs)s" % args

class PhantomJsStdoutFilter(SubprocessStdoutFilter):
    """
    Runs scripts using phantom js.
    """
    ADD_NEW_FILES = True
    ALIASES = ['phantomjs']
    EXECUTABLE = 'phantomjs'
    INPUT_EXTENSIONS = ['.js', '.txt']
    OUTPUT_EXTENSIONS = ['.txt']
    VERSION_COMMAND = 'phantomjs --version'
    # TODO ensure phantom.exit() is called in script?

class PhantomJsRenderSubprocessFilter(SubprocessFilter):
    """
    Renders HTML to PNG/PDF using phantom.js. If the HTML relies on local
    assets such as CSS or image files, these should be specified as inputs.
    """
    ADD_NEW_FILES = True
    ALIASES = ['phrender']
    EXECUTABLE = 'phantomjs'
    INPUT_EXTENSIONS = [".html", ".htm", ".txt"]
    OUTPUT_EXTENSIONS = [".png", ".pdf"]
    VERSION_COMMAND = 'phantomjs --version'
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 768

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or ""
        }
        return "%(prog)s %(args)s script.js" % args

    def setup_wd(self):
        wd = self.artifact.working_dir()
        if not os.path.exists(wd):
            for doc, filename in self.artifact.setup_wd(self.input_filename()):
                self.write_to_wd(wd, doc, filename)

        width = self.arg_value('width', self.DEFAULT_WIDTH)
        height = self.arg_value('height', self.DEFAULT_HEIGHT)

        timeout = self.setup_timeout()
        if not timeout:
            timeout = 200

        args = {
                'address' : self.input_filename(),
                'output' : self.output_filename(),
                'width' : width,
                'height' : height,
                'timeout' : timeout
                }

        js = """
        address = '%(address)s'
        output = '%(output)s'
        var page = new WebPage(),
            address, output, size;

        page.viewportSize = { width: %(width)s, height: %(height)s };
        page.open(address, function (status) {
            if (status !== 'success') {
                console.log('Unable to load the address!');
            } else {
                window.setTimeout(function () {
                page.render(output);
                phantom.exit();
                }, %(timeout)s);
            }
        });
        """ % args

        scriptfile = os.path.join(wd, "script.js")
        self.log.debug("scriptfile: %s" % scriptfile)
        with open(scriptfile, "w") as f:
            f.write(js)

        return wd

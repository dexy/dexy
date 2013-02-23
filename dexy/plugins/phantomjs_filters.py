from dexy.plugins.process_filters import SubprocessFilter
import os

class CasperJsSvg2PdfFilter(SubprocessFilter):
    """
    Converts an SVG file to PDF by running it through casper js.
    # TODO convert this to phantomjs, no benefit to using casper here (js is not user facing) and more restrictive
    """
    ALIASES = ['svg2pdf']
    _SETTINGS = {
            'add-new-files' : True,
            'executable' : 'casperjs',
            'version-command' : 'casperjs --version',
            "input-extensions" : ['.svg'],
            "output-extensions" : ['.pdf'],
            "width" : ("Width of page to capture.", 200),
            "height" : ("Height of page to capture.", 200),
            "command-string" : "%(prog)s %(args)s script.js"
            }

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

        width = self.setting('width')
        height = self.setting('height')
        js = self.script_js(width, height)

        wd = os.path.join(self.artifact.tmp_dir(), self.input().parent_dir())
        scriptfile = os.path.join(wd, "script.js")
        self.log.debug("scriptfile: %s" % scriptfile)
        with open(scriptfile, "w") as f:
            f.write(js)

        return wd

class PhantomJsRenderSubprocessFilter(SubprocessFilter):
    """
    Renders HTML to PNG/PDF using phantom.js. If the HTML relies on local
    assets such as CSS or image files, these should be specified as inputs.
    """
    ALIASES = ['phrender']
    _SETTINGS = {
            'add-new-files' : True,
            'executable' :  'phantomjs',
            "width" : ("Width of page to capture.", 1024),
            "height" : ("Height of page to capture.", 768),
            'version-command' : 'phantomjs --version',
            'command-string' : "%(prog)s %(args)s script.js",
            'input-extensions' : [".html", ".htm", ".txt"],
            'output-extensions' : [".png", ".pdf"]
            }

    def setup_wd(self):
        wd = self.artifact.working_dir()
        if not os.path.exists(wd):
            for doc, filename in self.artifact.setup_wd(self.input_filename()):
                self.write_to_wd(wd, doc, filename)

        width = self.setting('width')
        height = self.setting('height')

        timeout = self.setup_timeout()
        if not timeout:
            raise Exception("must have timeout")

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

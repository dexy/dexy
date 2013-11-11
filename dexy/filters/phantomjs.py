from dexy.filters.process import SubprocessFilter
import os

class CasperJsSvg2PdfFilter(SubprocessFilter):
    """
    Converts an SVG file to PDF by running it through casper js.

    # TODO convert this to phantomjs, no benefit to using casper here (js is
    # not user facing) and more restrictive
    """
    aliases = ['svg2pdf']
    _settings = {
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
                'svgfile' : self.work_input_filename(),
                'pdffile' : self.work_output_filename()
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

    def custom_populate_workspace(self):
        width = self.setting('width')
        height = self.setting('height')
        js = self.script_js(width, height)

        wd = self.parent_work_dir()
        scriptfile = os.path.join(wd, "script.js")

        self.log_debug("scriptfile: %s" % scriptfile)
        self.log_debug("js for scriptfile: %s" % js)

        with open(scriptfile, "w") as f:
            f.write(js)

class PhantomJsRenderSubprocessFilter(SubprocessFilter):
    """
    Renders HTML to PNG/PDF using phantom.js.
    
    If the HTML relies on local assets such as CSS or image files, these should
    be specified as inputs.
    """
    aliases = ['phrender']
    _settings = {
            'add-new-files' : True,
            'examples' : ['phrender'],
            'executable' :  'phantomjs',
            "width" : ("Width of page to capture.", 1024),
            "height" : ("Height of page to capture.", 768),
            'version-command' : 'phantomjs --version',
            'command-string' : "%(prog)s %(args)s script.js",
            'input-extensions' : [".html", ".htm", ".txt"],
            'output-extensions' : [".png", ".pdf"]
            }

    def custom_populate_workspace(self):
        width = self.setting('width')
        height = self.setting('height')

        timeout = self.setup_timeout()
        if not timeout:
            raise Exception("must have timeout")

        args = {
                'address' : self.work_input_filename(),
                'output' : self.work_output_filename(),
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

        wd = self.parent_work_dir()
        scriptfile = os.path.join(wd, "script.js")
        self.log_debug("scriptfile: %s" % scriptfile)
        self.log_debug("js for scriptfile: %s" % js)
        with open(scriptfile, "w") as f:
            f.write(js)

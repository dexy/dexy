from dexy.filters.process_filters import SubprocessFilter
from ordereddict import OrderedDict
import os
import re
import shutil

class PhantomJsRenderJavascriptInteractiveFilter(SubprocessFilter):
    """
    Filter which runs javascript code against a web page, capturing a
    screenshot after every section is run.
    """
    ALIASES = ['phsecshot']
    EXECUTABLE = 'phantomjs'
    INPUT_EXTENSIONS = ['.js', '.txt']
    OUTPUT_EXTENSIONS = ['.json']
    VERSION_COMMAND = 'phantomjs --version'
    BINARY = False

    def setup_cwd(self):
        return os.path.join(self.artifact.artifacts_dir, self.artifact.hashstring)

    def script_js(self, url, data_dict):
        """
        Construct the javascript which will actually be run by phantomjs.
        """
        js = """
        var page = new WebPage();

        var consoleObject = {};

        page.onConsoleMessage = function (msg) {
           consoleObject[sectionName] += msg;
        };

        page.open("%s", function (status) {
        """ % url

        for section_name, code in data_dict.iteritems():
            if code and not re.match("^\s*$", code):
                page_screenshot_artifact = self.artifact.add_additional_artifact("%s-screenshot.png" % section_name, ".png")
                page_fn = page_screenshot_artifact.filename()
                js += """
                sectionName = "%(section_name)s";
                consoleObject[sectionName] = "";

                page.evaluate(function () {
                    %(code)s
                });
                page.render("%(page_fn)s");
                """ % locals()

        # Closing bracket for page.open
        js += """
            console.log(JSON.stringify(consoleObject));
            phantom.exit();
        });
        """
        return js

    def process(self):
        self.artifact.create_temp_dir(populate=True)
        url = self.artifact.args['phsecshot']['url']

        js = self.script_js(url, self.artifact.input_data_dict)

        workfile = "script.js"
        workfile_path = os.path.join(self.artifact.artifacts_dir, self.artifact.hashstring, workfile)
        with open(workfile_path, "w") as f:
            f.write(js)

        command = "phantomjs %s" % workfile
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        self.artifact.data_dict['1'] = stdout

        work_dir = os.path.join(self.artifact.artifacts_dir, self.artifact.hashstring)

        # Collect any artifacts which were generated in the tempdir, that need
        # to be moved to their final locations.
        for i in self.artifact.inputs().values():
            src = os.path.join(work_dir, i.filename())
            if (i.virtual or i.additional) and os.path.exists(src):
                shutil.copy(src, i.filepath())

from dexy.exceptions import UserFeedback
from dexy.filters.process import SubprocessFilter
import os
import subprocess

try:
    import IPython.nbformat.current
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class IPythonCasper(SubprocessFilter):
    """
    Launch IPython notebook and run a casperjs script against the server.
    """
    aliases = ['ipynbcasper']

    _settings = {
            'input-extensions' : ['.ipynb'],
            'output-extensions' : ['.txt'],
            'script' : ("Canonical name of input document to use as casper script.", "default.js"),
            'add-new-files' : True,
            "width" : ("Width of page to capture.", 800),
            "height" : ("Height of page to capture.", 5000),
            'executable' : 'casperjs',
            'version-command' : 'casperjs --version',
            'ipython-port' : ("Port for the ipython notebook web app to run on.", 8987),
            'ipython-args' : ("Additional args to pass to ipython notebook command (list of string args).", None),
            "command-string" : "%(prog)s %(args)s %(script)s",
            }

    def is_active(self):
        return AVAILABLE

    default_js = """
        var casper = require('casper').create({
             viewportSize : {width : %(width)s, height: %(height)s }
        });

        casper.start("http://localhost:%(port)s", function() {
            this.waitForSelector("#notebook_list");
        });

        casper.then(function() {
            this.capture('notebook-list.png');
        });

        casper.run();
        """

    def configure_casper_script(self, wd):
        scriptfile = os.path.join(wd, self.setting('script'))

        # Write default script if necessary.
        if self.setting('script') == 'default.js' and not os.path.exists(scriptfile):
            js = self.default_js
        else:
            with open(scriptfile, "r") as f:
                js = f.read()

        args = {
                'width' : self.setting('width'),
                'height' : self.setting('height'),
                'port' : self.setting('ipython-port')
                }

        with open(scriptfile, "w") as f:
            f.write(js % args)

    def launch_ipython(self, wd, env):
        # Another way to handle ports would be to let ipython launch on a
        # random port and parse the port from the ipython process's stdout.
        port_string = "--port=%s" % self.setting('ipython-port')

        command = ['ipython', 'notebook', '--log-level=0', port_string, '--no-browser']
        command.extend(self.parse_additional_ipython_args())
        self.log_debug("About to run ipython command: '%s'" % ' '.join(command))
        proc = subprocess.Popen(command, shell=False,
                                    cwd=wd,
                                    stdin=None,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    env=env)
        return proc

    def parse_additional_ipython_args(self):
        raw_ipython_args = self.setting('ipython-args')
        if raw_ipython_args:
            if isinstance(raw_ipython_args, basestring):
                user_ipython_args = raw_ipython_args.split()
            elif isinstance(raw_ipython_args, list):
                assert isinstance(raw_ipython_args[0], basestring)
                user_ipython_args = raw_ipython_args
            else:
                raise UserFeedback("ipython-args must be a string or list of strings")
            return user_ipython_args
        else:
            return []

    def process(self):
        env = self.setup_env()
        wd = self.parent_work_dir()

        ws = self.workspace()
        if os.path.exists(ws):
            self.log_debug("already have workspace '%s'" % os.path.abspath(ws))
        else:
            self.populate_workspace()

        # launch ipython notebook
        ipython_proc = self.launch_ipython(wd, env)

        ## run casper script
        self.configure_casper_script(wd)

        command = self.command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.output_data.set_data(stdout)

        if self.setting('add-new-files'):
            self.add_new_files()

        # shut down ipython notebook
        os.kill(ipython_proc.pid, 9)

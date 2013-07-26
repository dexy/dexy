from dexy.exceptions import UserFeedback
import re
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
            'args' : '--web-security=false --ignore-ssl-errors=true',
            'timeout' : ("Timeout for the casperjs subprocess.", 10000),
            'image-ext' : ("File extension of images to capture.", ".png"),
            'script' : ("Canonical name of input document to use as casper script.", "default.js"),
            'add-new-files' : True,
            "width" : ("Width of page to capture.", 800),
            "height" : ("Height of page to capture.", 5000),
            'executable' : 'casperjs',
            'cell-timeout' : ("Timeout (in microseconds) for running individual notebook cells.", 5000),
            'version-command' : 'casperjs --version',
            'ipython-args' : ("Additional args to pass to ipython notebook command (list of string args).", None),
            "command-string" : "%(prog)s %(args)s %(script)s",
            }

    def is_active(self):
        return AVAILABLE

    def configure_casper_script(self, wd, port):
        scriptfile = os.path.join(wd, self.setting('script'))

        default_scripts_dir = os.path.join(os.path.dirname(__file__), "ipynbcasper")

        if not os.path.exists(scriptfile):
            # look for a matching default script
            script_setting = self.setting('script')

            filepath = os.path.join(default_scripts_dir, script_setting)
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    js = f.read()
            else:
                default_scripts = os.listdir(default_scripts_dir)
                args = (self.setting('script'), ", ".join(default_scripts),)
                raise UserFeedback("No script file named '%s' found.\nAvailable built-in scripts: %s" % args)

        else:
            with open(scriptfile, "r") as f:
                js = f.read()

        args = {
                'width' : self.setting('width'),
                'height' : self.setting('height'),
                'port' : port,
                'ext' : self.setting('image-ext'),
                'cell_timeout' : self.setting('cell-timeout')
                }

        with open(scriptfile, "w") as f:
            f.write(js % args)

    def launch_ipython(self, wd, env):
        command = ['ipython', 'notebook', '--no-browser']
        command.extend(self.parse_additional_ipython_args())

        self.log_debug("About to run ipython command: '%s'" % ' '.join(command))
        proc = subprocess.Popen(command, shell=False,
                                    cwd=wd,
                                    stdin=None,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    env=env)

        self.log_debug("Reading from stderr of ipython command...")
        while True:
            line = proc.stderr.readline()
            self.log_debug(line)

            if "The IPython Notebook is running" in line:
                m = re.search("([0-9\.]+):([0-9]{4})", line)
                port = m.groups()[1]

            if "Use Control-C to stop this server" in line:
                break

        # TODO if process is not running => throw exception
        return proc, port

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
        ipython_proc, port = self.launch_ipython(wd, env)

        try:
            self.configure_casper_script(wd, port)
    
            ## run casper script
            command = self.command_string()
            proc, stdout = self.run_command(command, self.setup_env())
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        finally:
            # shut down ipython notebook
            os.kill(ipython_proc.pid, 9)

        self.output_data.set_data(stdout)

        if self.setting('add-new-files'):
            self.add_new_files()

from dexy.filter import Filter
import dexy.exceptions
import os
import subprocess

class SubprocessFilter(Filter):
    ALIASES = []
    ENV = None
    CHECK_RETURN_CODE = False

    def setup_wd(self):
        """
        Sets up and populates the working directory as required.
        """
        self.artifact.create_working_dir(True)
        return self.artifact.tmp_dir()

    def command_line_args(self):
        return self.args().get('args')

    def command_line_scriptargs(self):
        return self.args().get('scriptargs')

    def command_string_stdout(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'scriptargs' : self.command_line_scriptargs() or "",
            'script_file' : os.path.basename(self.artifact.prior.name)
        }
        return "%(prog)s %(args)s %(script_file)s %(scriptargs)s" % args

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'scriptargs' : self.command_line_scriptargs() or "",
            'script_file' : os.path.basename(self.artifact.previous_canonical_filename),
            'output_file' : self.artifact.canonical_basename()
        }
        return "%(prog)s %(args)s %(script_file)s %(scriptargs)s %(output_file)s" % args

    def handle_subprocess_proc_return(self, command, exitcode, stderr):
        if exitcode is None:
            raise Exception("no return code, proc not finished!")
        elif exitcode != 0 and self.CHECK_RETURN_CODE:
            if self.ignore_errors():
                self.artifact.log.warn("Nonzero exit status %s" % exitcode)
                self.artifact.log.warn("output from process: %s" % stderr)
            else:
                raise dexy.exceptions.NonzeroExit(command, exitcode, stderr)

    def setup_env(self):
        env = os.environ

        # Add parameters set in class's ENV variable.
        if self.ENV:
            env.update(self.ENV)

        # Add parameters set in filter arguments.
        env.update(self.args().get('env', {}))

        return env

    def process(self):
        command = self.command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        # TODO store stdout somewhere

        self.copy_canonical_file()
        #self.copy_additional_inputs()

class SubprocessStdoutFilter(SubprocessFilter):
    def run_command(self, command, env, input_text = None):
        wd = self.setup_wd()

        if input_text:
            stdin = subprocess.PIPE
        else:
            stdin = None

        proc = subprocess.Popen(command, shell=True,
                                cwd=wd,
                                stdin=stdin,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)

        if input_text:
            self.log.debug("about to send input '%s'" % input_text)

        stdout, stderr = proc.communicate(input_text)
        return (proc, stdout)

    def process(self):
        command = self.command_string_stdout()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.artifact.output_data.set_data(stdout)

        # TODO store stdout somewhere
#        self.copy_additional_inputs()

class PythonSubprocessStdoutFilter(SubprocessStdoutFilter):
    ALIASES = ['py', 'pyout']
    EXECUTABLE = 'python'
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = 'python --version'

from dexy.doc import Doc
from dexy.filter import Filter
import dexy.exceptions
import json
import os
import platform
import subprocess

class SubprocessFilter(Filter):
    ALIASES = []
    ENV = None
    CHECK_RETURN_CODE = True
    VERSION_COMMAND = None
    WINDOWS_VERSION_COMMAND = None
    WRITE_STDERR_TO_STDOUT = False

    @classmethod
    def executables(self):
        if platform.system() == 'Windows' and hasattr(self, 'WINDOWS_EXECUTABLE'):
            return [self.WINDOWS_EXECUTABLE]
        else:
            if hasattr(self, 'EXECUTABLE'):
                return [self.EXECUTABLE]
            elif hasattr(self, 'EXECUTABLES'):
                return self.EXECUTABLES

    @classmethod
    def executable(self):
        """
        Returns the executable to use, or None if no executable found on the system.
        """
        for exe in self.executables():
            if exe:
                cmd = exe.split()[0] # remove any --arguments
                if dexy.utils.command_exists(cmd):
                    return exe

    @classmethod
    def is_active(klass):
        return klass.executable() and True or False

    @classmethod
    def version_command(klass):
        if platform.system() == 'Windows':
            return klass.WINDOWS_VERSION_COMMAND or klass.VERSION_COMMAND
        else:
            return klass.VERSION_COMMAND

    @classmethod
    def version(klass):
        command = klass.version_command()
        if command:
            proc = subprocess.Popen(
                       command,
                       shell=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT
                   )

            stdout, stderr = proc.communicate()
            if proc.returncode > 0:
                return False
            else:
                return stdout.strip().split("\n")[0]

    def process(self):
        command = self.command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.copy_canonical_file()

    ## Undocumented...

    def setup_wd(self):
        return self.artifact.create_working_dir(True)

    def command_line_args(self):
        return self.args().get('args')

    def command_line_scriptargs(self):
        return self.args().get('scriptargs')

    def command_string_stdout(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'scriptargs' : self.command_line_scriptargs() or "",
            'script_file' : os.path.basename(self.input().name)
        }
        return "%(prog)s %(args)s %(script_file)s %(scriptargs)s" % args

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'script_file' : os.path.basename(self.input().name),
            'scriptargs' : self.command_line_scriptargs() or "",
            'output_file' : os.path.basename(self.result().name)
        }
        return "%(prog)s %(args)s %(script_file)s %(scriptargs)s %(output_file)s" % args

    def ignore_nonzero_exit(self):
        return self.artifact.wrapper.ignore_nonzero_exit

    def handle_subprocess_proc_return(self, command, exitcode, stderr):
        if exitcode is None:
            raise Exception("no return code, proc not finished!")
        elif exitcode != 0 and self.CHECK_RETURN_CODE:
            if self.ignore_nonzero_exit():
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

    def walk_working_directory(self, wd, section_name=None):
        """
        Walk the passed working directory and copy all found file contents into a dict.
        """
        d = {}
        for dirpath, dirnames, filenames in os.walk(wd):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                relpath = os.path.relpath(filepath, wd)

                with open(filepath, "rb") as f:
                    contents = f.read()
                try:
                    json.dumps(contents)
                    d[relpath] = contents
                except UnicodeDecodeError as e:
                    d[relpath] = 'binary'

        if section_name:
            doc_key = "%s-%s-files" % (self.result().long_name(), section_name)
        else:
            doc_key = "%s-files" % self.result().long_name()

        doc = Doc(doc_key, contents=d)
        self.artifact.add_doc(doc)

    def write_stderr_to_stdout(self):
        # TODO allow customizing this in args
        return self.WRITE_STDERR_TO_STDOUT

    def do_walk_working_directory(self):
        return False

    def run_command(self, command, env, input_text=None):
        wd = self.setup_wd()

        stdout = subprocess.PIPE

        if input_text:
            stdin = subprocess.PIPE
        else:
            stdin = None

        if self.write_stderr_to_stdout():
            stderr = stdout
        else:
            stderr = subprocess.PIPE

        self.log.debug("About to run '%s' in '%s'" % (command, wd))
        proc = subprocess.Popen(command, shell=True,
                                cwd=wd,
                                stdin=stdin,
                                stdout=stdout,
                                stderr=stderr,
                                env=env)

        stdout, stderr = proc.communicate(input_text)
        self.log.debug("stdout is '%s'" % stdout)
        self.log.debug("stderr is '%s'" % stderr)

        if self.do_walk_working_directory():
            self.walk_working_directory(wd)

        return (proc, stdout)

    def copy_canonical_file(self):
        canonical_file = os.path.join(self.artifact.tmp_dir(), self.result().name)
        if not self.result().is_cached() and os.path.exists(canonical_file):
            self.result().copy_from_file(canonical_file)

class SubprocessStdoutFilter(SubprocessFilter):
    WRITE_STDERR_TO_STDOUT = False

    def process(self):
        command = self.command_string_stdout()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.result().set_data(stdout)

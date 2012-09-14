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
    CHECK_RETURN_CODE = False
    VERSION_COMMAND = None
    WINDOWS_VERSION_COMMAND = None

    @classmethod
    def executables(self):
        """
        Returns list of executables defined for this filter, in order of preference. If empty, no executable is required.
        """
        executables = []

        if platform.system() == 'Windows' and hasattr(self, 'WINDOWS_EXECUTABLE'):
            executables.append(self.WINDOWS_EXECUTABLE)
        else:
            if hasattr(self, 'EXECUTABLE'):
                executables.append(self.EXECUTABLE)
            elif hasattr(self, 'EXECUTABLES'):
                executables += self.EXECUTABLES

        return executables

    @classmethod
    def executable(self):
        """
        Returns the executable to use. Looks in WINDOWS_EXECUTABLE if on
        windows. Otherwise looks at EXECUTABLE or EXECUTABLES. If specified
        executables are not detected on the system, returns None.
        """
        for exe in self.executables():
            if exe:
                cmd = exe.split()[0] # remove any --arguments
                if dexy.utils.command_exists(cmd):
                    return exe

    @classmethod
    def version_command(klass):
        if platform.system() == 'Windows':
            return klass.WINDOWS_VERSION_COMMAND or klass.VERSION_COMMAND
        else:
            return klass.VERSION_COMMAND

    @classmethod
    def version(klass, log=None):
        vc = klass.version_command()

        if vc:
            # TODO make custom env available here...
            proc = subprocess.Popen(vc, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            stdout, stderr = proc.communicate()

            if proc.returncode > 0:
                err_msg = """An error occurred running %s""" % vc
                if log:
                    log.debug(err_msg)
                return False
            else:
                return stdout.strip().split("\n")[0]
        else:
            return None

    @classmethod
    def is_active(klass):
        """Allow filters to be disabled."""
        return klass.executable() and True or False

    def setup_wd(self):
        """
        Sets up and populates the working directory as required.
        """
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

    def run_command(self, command, env):
        wd = self.setup_wd()

        self.log.debug("About to run '%s' in '%s'" % (command, wd))
        proc = subprocess.Popen(command, shell=True,
                                cwd=wd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)

        stdout, stderr = proc.communicate()
        self.log.debug("stdout is '%s'" % stdout)
        self.log.debug("stderr is '%s'" % stderr)

        self.walk_working_directory(wd)

        return (proc, stdout)

    def process(self):
        command = self.command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        # TODO store stdout somewhere

        self.copy_canonical_file()

    def copy_canonical_file(self):
        canonical_file = os.path.join(self.artifact.tmp_dir(), self.result().name)
        if not self.result().is_cached() and os.path.exists(canonical_file):
            self.result().copy_from_file(canonical_file)

class SubprocessStdoutFilter(SubprocessFilter):
    def run_command(self, command, env, input_text = None):
        wd = self.setup_wd()

        if input_text:
            stdin = subprocess.PIPE
        else:
            stdin = None

        self.log.debug("About to run '%s' in '%s'" % (command, wd))
        proc = subprocess.Popen(command, shell=True,
                                cwd=wd,
                                stdin=stdin,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)

        if input_text:
            self.log.debug("about to send input '%s'" % input_text)

        stdout, stderr = proc.communicate(input_text)
        self.log.debug("stdout is '%s'" % stdout)
        self.log.debug("stderr is '%s'" % stderr)

        self.walk_working_directory(wd)

        return (proc, stdout)

    def process(self):
        command = self.command_string_stdout()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.artifact.output_data.set_data(stdout)


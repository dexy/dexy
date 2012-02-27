from dexy.dexy_filter import DexyFilter
import os
import subprocess

class DexyScriptErrorException(Exception):
    pass

class DexyNonzeroExitException(DexyScriptErrorException):
    def __init__(self, command, exitcode, stderr):
        msg = "'%s' returned nonzero exit code %s." % (command, exitcode)
        msg += " Set --loglevel DEBUG to troubleshoot or run with --ignore or set ignore-errors : true for this document to skip error-checking."
        if stderr and not stderr=='':
            msg += " Error info: %s" % stderr
        Exception.__init__(self,  msg)

class DexyEOFException(DexyScriptErrorException):
    pass

class ProcessFilter(DexyFilter):
    """
    Base class for all classes that do external processing, via subprocess or pexpect.
    """
    ALIASES = ['processfilter']
    CHECK_RETURN_CODE = True

    def ignore_errors(self):
        """
        By default, dexy filters should raise an exception when a script they
        run has a nonzero exit code or an EOF. Sometimes you want to document
        code that has an error, so you can disable this error checking.

        For software which does not consistently return nonzero error codes,
        you can set CHECK_RETURN_CODE to False.
        """
        artifact_ignore = self.artifact.args.has_key('ignore-errors') and self.artifact.args['ignore-errors']
        controller_ignore = self.artifact.controller_args['ignore']
        return artifact_ignore or controller_ignore

    def handle_subprocess_proc_return(self, command, exitcode, stderr):
        if exitcode is None:
            raise Exception("no return code, proc not finished!")
        elif exitcode != 0 and self.CHECK_RETURN_CODE:
            if self.ignore_errors():
                self.artifact.log.warn("Nonzero exit status %s" % exitcode)
                self.artifact.log.warn("output from process: %s" % stderr)
            else:
                raise DexyNonzeroExitException(command, exitcode, stderr)

    def setup_env(self):
        if self.artifact.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.args['env'])
        else:
            env = None
        return env

    def setup_timeout(self):
        if self.artifact.args.has_key('timeout'):
            timeout = self.artifact.args['timeout']
            self.log.info("using custom timeout %s for %s" % (timeout, self.artifact.key))
        else:
            timeout = None
        return timeout

    def setup_cwd(self):
        cwd = self.artifact.artifacts_dir
        if self.artifact.args.has_key('cwd'):
            cwd = os.path.join(cwd, self.artifact.args['cwd'])
            self.log.debug("Changing into directory %s" % os.path.abspath(cwd))
        return cwd

    def command_line_args(self):
        """
        Allow specifying command line arguments which are passed to the filter
        with the given key. Note that this does not currently allow
        differentiating between 2 calls to the same filter in a single document.
        """
        if self.artifact.args.has_key('args'):
            args = self.artifact.args['args']
            last_key = self.artifact.key.rpartition("|")[-1]
            if args.has_key(last_key):
                return args[last_key]

    def command_line_scriptargs(self):
        """
        Allow specifying command line arguments which are passed to the filter
        with the given key, to be passed as arguments to the script being run
        rather than the executable.
        """
        if self.artifact.args.has_key('scriptargs'):
            args = self.artifact.args['scriptargs']
            last_key = self.artifact.key.rpartition("|")[-1]
            if args.has_key(last_key):
                return args[last_key]

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'scriptargs' : self.command_line_scriptargs() or "",
            'script_file' : self.artifact.previous_artifact_filename,
            'output_file' : self.artifact.filename()
        }
        return "%(prog)s %(args)s %(script_file)s %(scriptargs)s %(output_file)s" % args

    def command_string_stdout(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'scriptargs' : self.command_line_scriptargs() or "",
            'script_file' : self.artifact.previous_artifact_filename
        }
        return "%(prog)s %(args)s %(script_file)s %(scriptargs)s" % args

    def clean_nonprinting(self, text):
        proc = subprocess.Popen('col -b | strings', shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

        stdout, stderr = proc.communicate(text)
        return stdout

class SubprocessFilter(ProcessFilter):
    ALIASES = ['subprocessfilter']
    BINARY = True
    FINAL = True

    def process(self):
        command = self.command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.artifact.stdout = stdout

    def run_command(self, command, env, input_text = None):
        cwd = self.setup_cwd()
        self.log.debug("about to run '%s' in %s" % (command, cwd))
        proc = subprocess.Popen(command, shell=True,
                                cwd=cwd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        if input_text:
            self.log.debug("about to send input '%s'" % input_text)

        stdout, stderr = proc.communicate(input_text)
        self.log.debug(stdout)
        return (proc, stdout)

class SubprocessStdoutFilter(SubprocessFilter):
    ALIASES = ['subprocessstdoutfilter']
    BINARY = False
    FINAL = False

    def process(self):
        command = self.command_string_stdout()
        proc, stdout = self.run_command(command, self.setup_env())
        if self.CHECK_RETURN_CODE:
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.artifact.set_data(stdout)

class SubprocessStdoutInputFilter(SubprocessFilter):
    ALIASES = ['subprocessstdoutinputfilter']
    BINARY = False
    FINAL = False

    def process(self):
        command = self.command_string_stdout()

        if len(self.artifact.inputs()) == 0:
            raise Exception("Trying to call an input filter without supplying any inputs!")

        elif len(self.artifact.inputs()) == 1:
            artifact = self.artifact.inputs().values()[0]
            for section_name, section_text in artifact.data_dict.iteritems():
                proc, stdout = self.run_command(command, self.setup_env(), section_text)
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                self.artifact.data_dict[section_name] = stdout

        else:
            for artifact in self.artifact.inputs().values():
                proc, stdout = self.run_command(command, self.setup_env(), artifact.output_text())
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                rel_key = self.artifact.relative_key_for_input(artifact)
                self.artifact.data_dict[rel_key] = stdout

class SubprocessStdoutInputFileFilter(SubprocessFilter):
    ALIASES = ['subprocessstdoutinputfilefilter']
    BINARY = False
    FINAL = False

    def command_string_stdout_input(self, input_artifact):
        script_file = self.artifact.previous_artifact_filename
        input_file = input_artifact.filename()
        args = self.command_line_args() or ""
        return "%s %s %s %s" % (self.executable(), args, script_file, input_file)

    def process(self):
        for artifact in self.artifact.inputs().values():
            command = self.command_string_stdout_input(artifact)
            proc, stdout = self.run_command(command, self.setup_env())
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)
            rel_key = self.artifact.relative_key_for_input(artifact)
            self.artifact.data_dict[rel_key] = stdout

class SubprocessCompileFilter(SubprocessFilter):
    """
    Base class for filters which need to compile code, then run the compiled executable.
    """
    ALIASES = ['subprocesscompilefilter']
    BINARY = False
    FINAL = False
    COMPILED_EXTENSION = ".o"
    CHECK_RETURN_CODE = False # Whether to check return code when running compiled executable.

    def compile_command_string(self):
        wf = self.artifact.previous_artifact_filename
        of = self.artifact.temp_filename(self.COMPILED_EXTENSION)
        return "%s %s -o %s" % (self.executable(), wf, of)

    def run_command_string(self):
        of = self.artifact.temp_filename(self.COMPILED_EXTENSION)
        return "./%s" % of

    def process(self):
        # Compile the code
        command = self.compile_command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        # This tests exitcode from the *compiler*
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        # Run the compiled code
        command = self.run_command_string()
        proc, stdout = self.run_command(command, self.setup_env())

        # This tests exitcode from the compiled script.
        if self.CHECK_RETURN_CODE:
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        self.artifact.set_data(stdout)

class SubprocessCompileInputFilter(SubprocessCompileFilter):
    ALIASES = ['subprocesscompileinputfilter']
    CHECK_RETURN_CODE = False

    def process(self):
        # Compile the code
        command = self.compile_command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        command = self.run_command_string()

        if len(self.artifact.inputs()) == 1:
            artifact = self.artifact.inputs().values()[0]
            for section_name, section_text in artifact.data_dict.iteritems():
                proc, stdout = self.run_command(command, self.setup_env(), section_text)
                if self.CHECK_RETURN_CODE:
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                self.artifact.data_dict[section_name] = stdout
        else:
            for artifact in self.artifact.inputs().values():
                proc, stdout = self.run_command(command, self.setup_env(), artifact.output_text())
                if self.CHECK_RETURN_CODE:
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                rel_key = self.artifact.relative_key_for_input(artifact)
                self.artifact.data_dict[rel_key] = stdout

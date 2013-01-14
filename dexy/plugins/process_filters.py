from dexy.common import OrderedDict
from dexy.filter import Filter
import dexy.exceptions
import fnmatch
import json
import os
import platform
import subprocess

class SubprocessFilter(Filter):
    """
    Parent class for all filters which use the subprocess module to run external programs.
    """
    ADD_NEW_FILES = False # whether to add new files by defaut
    ALIASES = []
    CHECK_RETURN_CODE = True
    ENV = None
    INITIAL_TIMEOUT = None
    PATH_EXTENSIONS = []
    REQUIRED_EXECUTABLES = []
    TIMEOUT = None
    VERSION_COMMAND = None
    WALK_WORKING_DIRECTORY = False
    WINDOWS_VERSION_COMMAND = None
    WRITE_STDERR_TO_STDOUT = True

    @classmethod
    def executables(self):
        if platform.system() == 'Windows' and hasattr(self, 'WINDOWS_EXECUTABLE'):
            return [self.WINDOWS_EXECUTABLE]
        else:
            if hasattr(self, 'EXECUTABLE'):
                if not isinstance(self.EXECUTABLE, basestring):
                    msg = "Executable must be a string, not a %s. '%s'"
                    args = (self.EXECUTABLE.__class__.__name__, self.EXECUTABLE)
                    raise dexy.exceptions.InternalDexyProblem(msg%args)
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
    def required_executables_present(klass):
        return all(dexy.utils.command_exists(exe) for exe in klass.REQUIRED_EXECUTABLES)

    @classmethod
    def is_active(klass):
        return klass.executable() and klass.required_executables_present()

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

        if self.do_add_new_files():
            self.log.debug("adding new files found in %s for %s" % (self.artifact.tmp_dir(), self.artifact.key))
            self.add_new_files()

    def command_line_args(self):
        return self.args().get('args') or self.args().get('clargs')

    def command_line_scriptargs(self):
        return self.args().get('scriptargs')

    def command_string_stdout(self):
        clargs = self.command_line_args() or ''
        self.log.debug("command line args specified by user are '%s'" % clargs)
        args = {
            'prog' : self.executable(),
            'args' : clargs,
            'scriptargs' : self.command_line_scriptargs() or "",
            'script_file' : self.input_filename()
        }
        return """%(prog)s %(args)s "%(script_file)s" %(scriptargs)s""" % args

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'script_file' : self.input_filename(),
            'scriptargs' : self.command_line_scriptargs() or "",
            'output_file' : self.output_filename()
        }
        return """%(prog)s %(args)s "%(script_file)s" %(scriptargs)s "%(output_file)s" """ % args

    def ignore_nonzero_exit(self):
        return self.artifact.wrapper.ignore_nonzero_exit

    def clear_cache(self):
        self.output().clear_cache()

    def handle_subprocess_proc_return(self, command, exitcode, stderr):
        if exitcode is None:
            raise dexy.exceptions.InternalDexyProblem("no return code, proc not finished!")
        elif exitcode != 0 and self.CHECK_RETURN_CODE:
            if self.ignore_nonzero_exit():
                self.artifact.log.warn("Nonzero exit status %s" % exitcode)
                self.artifact.log.warn("output from process: %s" % stderr)
            else:
                err_msg = "The command '%s' for %s exited with nonzero exit status %s." % (command, self.artifact.key, exitcode)
                if stderr:
                    err_msg += " Here is stderr:\n%s" % stderr
                self.output().clear_cache()
                raise dexy.exceptions.UserFeedback(err_msg)

    def setup_timeout(self):
        return self.args().get('timeout', self.TIMEOUT)

    def setup_initial_timeout(self):
        return self.args().get('initial_timeout', self.INITIAL_TIMEOUT)

    def setup_env(self):
        env = os.environ

        # Add parameters set in class's ENV variable.
        if self.ENV:
            env.update(self.ENV)

        # Add parameters set in filter arguments.
        env.update(self.args().get('env', {}))

        # Add parameters in wrapper's env dict
        if self.is_part_of_script_bundle():
            for key, value in self.script_storage().iteritems():
                if key.startswith("DEXY_"):
                    self.log.debug("Adding %s to env value is %s" % (key, value))
                    env[key] = value

        # Add any path extensions to PATH
        if self.PATH_EXTENSIONS:
            paths = [env['PATH']] + self.PATH_EXTENSIONS
            env['PATH'] = ":".join(paths)

        return env

    def add_new_files(self):
        wd = self.artifact.tmp_dir()

        do_add_new = self.do_add_new_files()

        for dirpath, dirnames, filenames in os.walk(wd):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                filesize = os.path.getsize(filepath)
                relpath = os.path.relpath(filepath, wd)

                already_have_file = (relpath in self.artifact.wrapper.batch.doc_names())
                empty_file = (filesize == 0)

                if isinstance(do_add_new, list):
                    is_valid_file_extension = False
                    for pattern in do_add_new:
                        if "*" in pattern:
                            if fnmatch.fnmatch(relpath, pattern):
                                is_valid_file_extension = True
                                continue
                        else:
                            if filename.endswith(pattern):
                                is_valid_file_extension = True
                                continue
                elif isinstance(do_add_new, basestring):
                    is_valid_file_extension = False
                    for pattern in [do_add_new]:
                        if "*" in pattern:
                            if fnmatch.fnmatch(relpath, pattern):
                                is_valid_file_extension = True
                                continue
                        else:
                            if filename.endswith(pattern):
                                is_valid_file_extension = True
                                continue
                elif isinstance(do_add_new, bool):
                    if not do_add_new:
                        raise dexy.exceptions.InternalDexyProblem("should not get here")
                    is_valid_file_extension = True
                else:
                    raise dexy.exceptions.InternalDexyProblem("type is %s value is %s" % (do_add_new.__class__, do_add_new))

                if (not already_have_file) and is_valid_file_extension and (not empty_file):
                    with open(filepath, 'rb') as f:
                        contents = f.read()
                    self.add_doc(relpath, contents)

    def do_walk_working_directory(self):
        if self.args().has_key('walk-working-dir'):
            return self.args()['walk-working-dir']
        else:
            return self.WALK_WORKING_DIRECTORY

    def walk_working_directory(self, doc=None, section_name=None):
        if not doc:
            if section_name:
                doc_key = "%s-%s-files" % (self.output().long_name(), section_name)
            else:
                doc_key = "%s-files" % self.output().long_name()

            doc = self.add_doc(doc_key, {})

        wd = self.artifact.tmp_dir()
        for dirpath, dirnames, filenames in os.walk(wd):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                relpath = os.path.relpath(filepath, wd)

                with open(filepath, "rb") as f:
                    contents = f.read()
                try:
                    json.dumps(contents)
                    doc.output().append(relpath, contents)
                except UnicodeDecodeError:
                    doc.output().append(relpath, 'binary')

        return doc

    def write_stderr_to_stdout(self):
        # TODO allow customizing this in args
        return self.WRITE_STDERR_TO_STDOUT

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

        self.log.debug("about to run '%s' in '%s'" % (command, wd))
        proc = subprocess.Popen(command, shell=True,
                                    cwd=wd,
                                    stdin=stdin,
                                    stdout=stdout,
                                    stderr=stderr,
                                    env=env)

        if input_text:
            self.log.debug("about to send input_text '%s'" % input_text)

        stdout, stderr = proc.communicate(input_text)
        self.log.debug(u"stdout is '%s'" % stdout.decode('utf-8'))
        self.log.debug(u"stderr is '%s'" % stderr.decode('utf-8'))

        return (proc, stdout)

    def copy_canonical_file(self):
        canonical_file = os.path.join(self.artifact.tmp_dir(), self.output().name)
        if not self.output().is_cached() and os.path.exists(canonical_file):
            self.output().copy_from_file(canonical_file)

class SubprocessStdoutFilter(SubprocessFilter):
    """
    Subclass of SubprocessFilter which runs a command and returns the stdout generated by that command as its output.
    """
    WRITE_STDERR_TO_STDOUT = False
    REQUIRE_OUTPUT = False

    def process(self):
        command = self.command_string_stdout()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.output().set_data(stdout)

        if self.do_walk_working_directory():
            self.walk_working_directory()

        if self.do_add_new_files():
            self.log.debug("adding new files found in %s for %s" % (self.artifact.tmp_dir(), self.artifact.key))
            self.add_new_files()

class SubprocessCompileFilter(SubprocessFilter):
    """
    Base class for filters which need to compile code, then run the compiled executable.
    """
    ADD_NEW_FILES = True
    COMPILED_EXTENSION = ".o"
    CHECK_RETURN_CODE = False # Whether to check return code when running compiled executable.
    EXECUTABLES = []

    def compile_command_string(self):
        wf = os.path.basename(self.input().name)
        of = self.compiled_filename()
        compiler_args = self.args().get("compiler-args", "")
        return "%s %s %s -o %s" % (self.executable(), compiler_args, wf, of)

    def compiled_filename(self):
        basename = os.path.basename(self.input().name)
        nameroot = os.path.splitext(basename)[0]
        return "%s%s" % (nameroot, self.COMPILED_EXTENSION)

    def run_command_string(self):
        return "./%s" % self.compiled_filename()

    def process(self):
        env = self.setup_env()

        # Compile the code
        command = self.compile_command_string()
        proc, stdout = self.run_command(command, env)

        # test exitcode from the *compiler*
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        # Run the compiled code
        command = self.run_command_string()
        proc, stdout = self.run_command(command, env)

        # This tests exitcode from the compiled script.
        if self.CHECK_RETURN_CODE:
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        self.output().set_data(stdout)

        if self.do_add_new_files():
            self.log.debug("adding new files found in %s for %s" % (self.artifact.tmp_dir(), self.artifact.key))
            self.add_new_files()

class SubprocessInputFilter(SubprocessFilter):
    """
    Filters which run a task in subprocess while also writing content to stdin for that process.
    """
    CHECK_RETURN_CODE = False
    WRITE_STDERR_TO_STDOUT = False
    OUTPUT_DATA_TYPE = 'sectioned'

    def process(self):
        command = self.command_string()

        inputs = list(self.artifact.doc.node.walk_input_docs())

        output = OrderedDict()

        if len(inputs) == 1:
            doc = inputs[0]
            for section_name, section_text in doc.output().as_sectioned().iteritems():
                proc, stdout = self.run_command(command, self.setup_env(), section_text)
                if self.CHECK_RETURN_CODE:
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[section_name] = stdout
        else:
            for doc in inputs:
                proc, stdout = self.run_command(command, self.setup_env(), unicode(doc.output()))
                if self.CHECK_RETURN_CODE:
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[doc.key] = stdout

        self.output().set_data(output)

class SubprocessInputFileFilter(SubprocessFilter):
    """
    Filters which run one or more input files through the script via filenames.
    """
    CHECK_RETURN_CODE = False
    WRITE_STDERR_TO_STDOUT = False
    OUTPUT_DATA_TYPE = 'sectioned'

    def command_string_for_input(self, input_doc):
        return "%s %s %s" % (self.executable(), self.input_filename(), input_doc.output().name)

    def process(self):
        inputs = list(self.artifact.doc.node.walk_input_docs())

        output = OrderedDict()

        for doc in inputs:
            command = self.command_string_for_input(doc)
            proc, stdout = self.run_command(command, self.setup_env())
            if self.CHECK_RETURN_CODE:
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
            output[doc.key] = stdout

        self.output().set_data(output)

class SubprocessCompileInputFilter(SubprocessCompileFilter):
    """
    Filters which compile code, then run it with input.
    """
    CHECK_RETURN_CODE = False
    WRITE_STDERR_TO_STDOUT = False
    OUTPUT_DATA_TYPE = 'sectioned'

    def process(self):
        # Compile the code
        command = self.compile_command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        command = self.run_command_string()

        inputs = list(self.artifact.doc.node.walk_input_docs())

        output = OrderedDict()

        if len(inputs) == 1:
            doc = inputs[0]
            for section_name, section_text in doc.output().as_sectioned().iteritems():
                proc, stdout = self.run_command(command, self.setup_env(), section_text)
                if self.CHECK_RETURN_CODE:
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[section_name] = stdout
        else:
            for doc in inputs:
                proc, stdout = self.run_command(command, self.setup_env(), doc.output().as_text())
                if self.CHECK_RETURN_CODE:
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[doc.key] = stdout

        self.output().set_data(output)

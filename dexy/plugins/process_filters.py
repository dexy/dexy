from dexy.common import OrderedDict
from dexy.doc import Doc
from dexy.filter import Filter
import dexy.exceptions
import json
import os
import platform
import subprocess

class SubprocessFilter(Filter):
    ADD_NEW_FILES = True # whether to add new files by defaut
    ALIASES = []
    CHECK_RETURN_CODE = True
    ENV = None
    TIMEOUT = None
    INITIAL_TIMEOUT = None
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

        if self.do_add_new_files():
            self.add_new_files()

    def setup_wd(self):
        tmpdir = self.artifact.tmp_dir()

        if not os.path.exists(tmpdir):
            self.artifact.create_working_dir(
                    input_filepath=self.input_filepath(),
                    populate=True
                )

        return tmpdir

    def input_filepath(self):
        return self.artifact.input_filepath()

    def command_line_args(self):
        return self.args().get('args')

    def command_line_scriptargs(self):
        return self.args().get('scriptargs')

    def command_string_stdout(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'scriptargs' : self.command_line_scriptargs() or "",
            'script_file' : self.input_filepath()
        }
        return "%(prog)s %(args)s %(script_file)s %(scriptargs)s" % args

    def command_string(self):
        args = {
            'prog' : self.executable(),
            'args' : self.command_line_args() or "",
            'script_file' : self.input_filepath(),
            'scriptargs' : self.command_line_scriptargs() or "",
            'output_file' : self.result().name
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

        return env

    def do_add_new_files(self):
        return self.ADD_NEW_FILES or self.args().get('add-new-files', False)

    def add_new_files(self):
        wd = self.artifact.tmp_dir()
        for dirpath, dirnames, filenames in os.walk(wd):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                filesize = os.path.getsize(filepath)
                relpath = os.path.relpath(filepath, wd)
                ext = os.path.splitext(filepath)[1]

                already_have_file = (relpath in self.artifact.wrapper.registered_doc_names())
                empty_file = (filesize == 0)

                if hasattr(self.ADD_NEW_FILES, 'len'):
                    is_valid_file_extension = ext in self.ADD_NEW_FILES
                else:
                    is_valid_file_extension = True

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
                doc_key = "%s-%s-files" % (self.result().long_name(), section_name)
            else:
                doc_key = "%s-files" % self.result().long_name()

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
                    doc.result().append(relpath, contents)
                except UnicodeDecodeError as e:
                    doc.result().append(relpath, 'binary')

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

        self.log.debug("About to run '%s' in '%s'" % (command, wd))
        proc = subprocess.Popen(command, shell=True,
                                cwd=wd,
                                stdin=stdin,
                                stdout=stdout,
                                stderr=stderr,
                                env=env)

        stdout, stderr = proc.communicate(input_text)
        self.log.debug(u"stdout is '%s'" % stdout.decode('utf-8'))
        self.log.debug(u"stderr is '%s'" % stderr.decode('utf-8'))

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

        if self.do_walk_working_directory():
            self.walk_working_directory()

        if self.do_add_new_files():
            self.add_new_files()

class SubprocessCompileFilter(SubprocessFilter):
    """
    Base class for filters which need to compile code, then run the compiled executable.
    """
    ALIASES = ['subprocesscompilefilter']
    BINARY = False
    FINAL = False
    COMPILED_EXTENSION = ".o"
    CHECK_RETURN_CODE = False # Whether to check return code when running compiled executable.
    EXECUTABLES = []

    def compile_command_string(self):
        wf = self.input().name
        of = self.compiled_filename()
        return "%s %s -o %s" % (self.executable(), wf, of)

    def compiled_filename(self):
        nameroot = os.path.splitext(self.input().name)[0]
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

        self.result().set_data(stdout)

class SubprocessCompileInputFilter(SubprocessCompileFilter):
    ALIASES = ['subprocesscompileinputfilter']
    CHECK_RETURN_CODE = False
    WRITE_STDERR_TO_STDOUT = False
    OUTPUT_DATA_TYPE = 'sectioned'

    def process(self):
        # Compile the code
        command = self.compile_command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        command = self.run_command_string()

        inputs = self.artifact.doc.completed_children

        output = OrderedDict()

        if len(inputs) == 1:
            doc = inputs.values()[0]
            for section_name, section_text in doc.as_sectioned().iteritems():
                proc, stdout = self.run_command(command, self.setup_env(), section_text)
                if self.CHECK_RETURN_CODE:
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[section_name] = stdout
        else:
            for key, doc in inputs.iteritems():
                if isinstance(doc, dexy.doc.Doc):
                    proc, stdout = self.run_command(command, self.setup_env(), doc.output().as_text())
                    if self.CHECK_RETURN_CODE:
                        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                    output[doc.key] = stdout

        self.result().set_data(output)

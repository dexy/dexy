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
    ALIASES = []
    WALK_WORKING_DIRECTORY = False

    _SETTINGS = {
            'path-extensions' : ("strings to extend path with", []),
            'write-stderr-to-stdout' : ("Should stderr be piped to stdout?", True),
            'check-return-code' : ("Whether to look for nonzero return code.", True),
            'record-vars' : ("Whether to add code that will automatically record values of variables.", False),
            'env' : ("Dictionary of key-value pairs to be added to environment for runs.", {}),
            'args' : ("Arguments to be passed to the executable.", ''),
            'clargs' : ("Arguments to be passed to the executable (same as 'args').", ''),
            'command-string' : ("The full command string.",
                """%(prog)s %(args)s "%(script_file)s" %(scriptargs)s "%(output_file)s" """),
            'executable' : ('The executable to be run', None),
            'executables' : ('The executables to be run', None),
            'initial-timeout' : ('', 10),
            'scriptargs' : ("Arguments to be passed to the executable.", ''),
            'timeout' : ('', 10),
            'version-command': ( "Command to call to return version of installed software.", None),
            'windows-version-command': ( "Command to call on windows to return version of installed software.", None),
            'walk-working-dir' : ("Automatically register extra files that are found in working dir.", False),
            'required-executables' : ("Other executables that must be present on system.", [])
            }

    def executables(self):
        if platform.system() == 'Windows' and self._settings.has_key('windows-executable'):
            return [self.setting('windows-executable')]
        else:
            if self.setting('executable'):
                executable = self.setting('executable')
                if not isinstance(executable, basestring):
                    msg = "Executable for %s must be a string, not a %s. '%s'"
                    args = (self.__class__.__name__, executable.__class__.__name__, executable)
                    raise dexy.exceptions.InternalDexyProblem(msg%args)
                return [executable]
            elif self.setting('executables'):
                return self.setting('executables')
            else:
                return []

    def executable(self):
        """
        Returns the executable to use, or None if no executable found on the system.
        """
        for exe in self.executables():
            if exe:
                cmd = exe.split()[0] # remove any --arguments
                if dexy.utils.command_exists(cmd):
                    return exe

    def required_executables_present(self):
        return all(dexy.utils.command_exists(exe) for exe in self.setting('required-executables'))

    def is_active(klass):
        return klass.executable() and klass.required_executables_present()

    def version_command(klass):
        if platform.system() == 'Windows':
            return klass.setting('windows-version-command') or klass.setting('version-command')
        else:
            return klass.setting('version-command')

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

    def command_string_args(self):
        return self.default_command_string_args()

    def default_command_string_args(self):
        args = {
                'args' : " ".join([self.setting('args'), self.setting('clargs')]),
                'prog' : self.executable(),
                'script_file' : self.input_filename(),
                'output_file' : self.output_filename()
                }
        skip = ['args', 'clargs']
        args.update(self.setting_values(skip))
        return args

    def command_string(self):
        return self.setting('command-string') % self.command_string_args()

    def ignore_nonzero_exit(self):
        return self.artifact.wrapper.ignore_nonzero_exit

    def clear_cache(self):
        self.output().clear_cache()

    def handle_subprocess_proc_return(self, command, exitcode, stderr):
        if exitcode is None:
            raise dexy.exceptions.InternalDexyProblem("no return code, proc not finished!")
        elif exitcode != 0 and self.setting('check-return-code'):
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
        return self.setting('timeout')

    def setup_initial_timeout(self):
        return self.setting('initial-timeout')

    def setup_env(self):
        env = os.environ

        env.update(self.setting('env'))

        # Add parameters in wrapper's env dict
        if self.is_part_of_script_bundle():
            for key, value in self.script_storage().iteritems():
                if key.startswith("DEXY_"):
                    self.log.debug("Adding %s to env value is %s" % (key, value))
                    env[key] = value

        # Add any path extensions to PATH
        if self.setting('path-extensions'):
            paths = [env['PATH']] + self.setting('path-extensions')
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
        return self.setting('walk-working-dir')

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

    def run_command(self, command, env, input_text=None):
        wd = self.setup_wd()

        stdout = subprocess.PIPE

        if input_text:
            stdin = subprocess.PIPE
        else:
            stdin = None

        if self.setting('write-stderr-to-stdout'):
            stderr = stdout
        else:
            stderr = subprocess.PIPE

        self.log.debug("about to run '%s' in '%s'" % (command, os.path.abspath(wd)))
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
    _SETTINGS = {
            'write-stderr-to-stdout' : False,
            'require-output' : False,
            'command-string' : '%(prog)s %(args)s "%(script_file)s" %(scriptargs)s'
            }

    def process(self):
        command = self.command_string()
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
    _SETTINGS = {
            'add-new-files' : True,
            'check-return-code' : False,
            'compiled-extension' : ("Extension which compiled files end with.", ".o"),
            'compiler-command-string' : (
                "Command string to call compiler.",
                "%(prog)s %(compiler_args)s %(script_file)s -o %(compiled_filename)s"
                ),
            'compiler-args' : ("Args to pass to compiler.", '')
            }

    def compile_command_string(self):
        args = self.default_command_string_args()
        args['compiler_args'] = self.setting('compiler-args')
        args['compiled_filename'] = self.compiled_filename()
        return self.setting('compiler-command-string') % args

    def compiled_filename(self):
        basename = os.path.basename(self.input().name)
        nameroot = os.path.splitext(basename)[0]
        return "%s%s" % (nameroot, self.setting('compiled-extension'))

    def run_command_string(self):
        args = self.default_command_string_args()
        args['compiled_filename'] = self.compiled_filename()
        return "./%(compiled_filename)s %(args)s" % args

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
        if self.setting('check-return-code'):
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        self.output().set_data(stdout)

        if self.do_add_new_files():
            self.log.debug("adding new files found in %s for %s" % (self.artifact.tmp_dir(), self.artifact.key))
            self.add_new_files()

class SubprocessInputFilter(SubprocessFilter):
    """
    Filters which run a task in subprocess while also writing content to stdin for that process.
    """
    _SETTINGS = {
            'output-data-type' : 'sectioned',
            'check-return-code' : False,
            'write-stderr-to-stdout' : False
            }

    def process(self):
        command = self.command_string()

        inputs = list(self.artifact.doc.node.walk_input_docs())

        output = OrderedDict()

        if len(inputs) == 1:
            doc = inputs[0]
            for section_name, section_text in doc.output().as_sectioned().iteritems():
                proc, stdout = self.run_command(command, self.setup_env(), section_text)
                if self.setting('check-return-code'):
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[section_name] = stdout
        else:
            for doc in inputs:
                proc, stdout = self.run_command(command, self.setup_env(), unicode(doc.output()))
                if self.setting('check-return-code'):
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[doc.key] = stdout

        self.output().set_data(output)

class SubprocessInputFileFilter(SubprocessFilter):
    """
    Filters which run one or more input files through the script via filenames.
    """
    _SETTINGS = {
            'output-data-type' : 'sectioned',
            'check-return-code' : False,
            'write-stderr-to-stdout' : False,
            'command-string' : """%(prog)s %(args)s %(input_text)s "%(script_file)s" """
            }

    def command_string_args(self, input_doc):
        args = self.default_command_string_args()
        args['input_text'] = input_doc.output().name
        return args
    
    def command_string_for_input(self, input_doc):
        return self.setting('command-string') % self.command_string_args(input_doc)

    def process(self):
        inputs = list(self.artifact.doc.node.walk_input_docs())

        output = OrderedDict()

        for doc in inputs:
            command = self.command_string_for_input(doc)
            proc, stdout = self.run_command(command, self.setup_env())
            if self.setting('check-return-code'):
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
            output[doc.key] = stdout

        self.output().set_data(output)

class SubprocessCompileInputFilter(SubprocessCompileFilter):
    """
    Filters which compile code, then run it with input.
    """
    _SETTINGS = {
            'output-data-type' : 'sectioned',
            'check-return-code' : False,
            'write-stderr-to-stdout' : False
            }

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
                if self.setting('check-return-code'):
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[section_name] = stdout
        else:
            for doc in inputs:
                proc, stdout = self.run_command(command, self.setup_env(), doc.output().as_text())
                if self.setting('check-return-code'):
                    self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[doc.key] = stdout

        self.output().set_data(output)

class SubprocessFormatFlagFilter(SubprocessFilter):
    """
    Subprocess filters which have to pass a format flag (like ragel -R for ruby).
    """
    _SETTINGS = {
            'ext-to-format' : ("A dict of mappings from file extensions to format flags that need to be passed on the command line, e.g. for ragel with ruby host language .rb => -R", {})
            }

    def command_string_args(self):
        args = self.default_command_string_args()

        flags = self.setting('ext-to-format')

        if any(f in args['args'] for f in flags):
            # Already have specified the format manually.
            fmt = ''
        else:
            fmt = flags[self.artifact.ext]

        args['format'] = fmt
        return args

class SubprocessExtToFormatFilter(SubprocessFilter):
    """
    Subprocess filters which have ext-to-format param.
    """
    _SETTINGS = {
            'format-specifier' : ("The string used to specify the format switch, include trailing space if needed.", None),
            'ext-to-format' : ("A dict of mappings from file extensions to format parameters that need to be passed on the command line, e.g. for ghostscript .png => png16m", {})
            }

    def command_string_args(self):
        args = self.default_command_string_args()

        fmt_specifier = self.setting('format-specifier')
        if fmt_specifier and (fmt_specifier in args['args']):
            # Already have specified the format manually.
            fmt = ''
        else:
            fmt_setting = self.setting('ext-to-format')[self.artifact.ext]
            if fmt_setting:
                fmt = "%s%s" % (fmt_specifier, fmt_setting)
            else:
                fmt = ''

        args['format'] = fmt
        return args

class SubprocessStdoutTextFilter(SubprocessStdoutFilter):
    _SETTINGS = {
            'command-string' : "%(prog)s %(args)s \"%(text)s\"",
            'input-extensions' : ['.txt'],
            'output-extensions' : ['.txt']
            }

    def command_string_args(self):
        args = self.default_command_string_args()
        args['text'] = self.input().as_text()
        return args

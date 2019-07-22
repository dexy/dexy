from dexy.filter import Filter
from dexy.utils import file_exists
import dexy.exceptions
import fnmatch
import os
import platform
import subprocess

class SubprocessFilter(Filter):
    """
    Parent class for all filters which use the subprocess module.
    """
    aliases = []
    _settings = {
            'args' : ("Arguments to be passed to the executable.", ''),
            'check-return-code' : ("Whether to look for nonzero return code.", True),
            'clargs' : ("Arguments to be passed to the executable (same as 'args').", ''),
            'command-string' : ("The full command string.", """%(prog)s %(args)s "%(script_file)s" %(scriptargs)s "%(output_file)s" """),
            'make-dummy-output' : ("Whether to make a dummy output file when one is not generated and add-new-files is True.", False),
            'env' : ("Dictionary of key-value pairs to be added to environment for runs.", {}),
            'executable' : ('The executable to be run', None),
            'initial-timeout' : ('', 10),
            'path-extensions' : ("strings to extend path with", []),
            'record-vars' : ("Whether to add code that will automatically record values of variables.", False),
            'scriptargs' : ("Arguments to be passed to the executable.", ''),
            'tags' : [],
            'timeout' : ('', 10),
            'use-wd' : ("Whether to use a custom working directory when running filter.", True),
            'version-command': ( "Command to call to return version of installed software.", None),
            'windows-version-command': ( "Command to call on windows to return version of installed software.", None),
            'write-stderr-to-stdout' : ("Should stderr be piped to stdout?", True),
            }

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
                return stdout.decode('utf-8').strip().split("\n")[0]

    def process(self):
        command = self.command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.copy_canonical_file()

        if self.setting('add-new-files'):
            self.log_debug("adding new files found in %s for %s" % (self.workspace(), self.key))
            self.add_new_files()

    def command_string_args(self):
        return self.default_command_string_args()

    def default_command_string_args(self):
        args = {
                'args' : " ".join([self.setting('args'), self.setting('clargs')]),
                'prog' : self.setting('executable'),
                'script_file' : self.work_input_filename(),
                'output_file' : self.work_output_filename()
                }
        skip = ['args', 'clargs']
        args.update(self.setting_values(skip))
        return args

    def command_string(self):
        return self.setting('command-string') % self.command_string_args()

    def ignore_nonzero_exit(self):
        return self.doc.wrapper.ignore_nonzero_exit

    def clear_cache(self):
        self.output_data.clear_cache()

    def handle_subprocess_proc_return(self, command, exitcode, stderr, compiled=False):
        self.log_debug("exit code is: %s" % exitcode)
        if exitcode is None:
            raise dexy.exceptions.InternalDexyProblem("no return code, proc not finished!")
        elif exitcode == 127 and not compiled:
            raise dexy.exceptions.InactivePlugin(self.alias)
        elif exitcode != 0 and self.setting('check-return-code'):
            if self.ignore_nonzero_exit():
                self.log_warn("Nonzero exit status %s" % exitcode)
                self.log_warn("output from process: %s" % stderr)
            else:
                err_msg = "The command '%s' for %s exited with nonzero exit status %s." % (command, self.key, exitcode)
                if stderr:
                    err_msg += " Here is stderr:\n%s" % stderr
                self.output_data.clear_cache()
                raise dexy.exceptions.UserFeedback(err_msg)

    def setup_timeout(self):
        return self.setting('timeout')

    def setup_initial_timeout(self):
        return self.setting('initial-timeout')

    def setup_env(self):
        env = os.environ

        env.update(self.setting('env'))

        env['DEXY_ROOT'] = os.path.abspath(".")

        # Add parameters in wrapper's env dict
        if self.is_part_of_script_bundle():
            for key, value in self.script_storage().items():
                if key.startswith("DEXY_"):
                    self.log_debug("Adding %s to env value is %s" % (key, value))
                    env[key] = value

        # Add any path extensions to PATH
        if self.setting('path-extensions'):
            paths = [env['PATH']] + self.setting('path-extensions')
            env['PATH'] = ":".join(paths)

        return env

    def add_new_files(self):
        """
        Walk working directory and add a new dexy document for every newly
        created file found.
        """
        wd = self.workspace()
        self.log_debug("adding new files found in %s for %s" % (wd, self.key))

        add_new_files = self.setting('add-new-files')
        if isinstance(add_new_files, str):
            add_new_files = [add_new_files]

        exclude = self.setting('exclude-add-new-files')
        skip_dirs = self.setting('exclude-new-files-from-dir')

        if isinstance(exclude, str):
            raise dexy.exceptions.UserFeedback("exclude-add-new-files should be a list, not a string")

        new_files_added = 0
        for dirpath, subdirs, filenames in os.walk(wd):
            # Prune subdirs which match exclude.
            subdirs[:] = [d for d in subdirs if d not in skip_dirs]

            # Iterate over files in directory.
            for filename in filenames:
                filepath = os.path.normpath(os.path.join(dirpath, filename))
                relpath = os.path.relpath(filepath, wd)
                self.log_debug("Processing %s" % filepath)

                if relpath in self._files_workspace_populated_with:
                    # already have this file
                    continue

                if isinstance(add_new_files, list):
                    is_valid_file_extension = False
                    for pattern in add_new_files:
                        if "*" in pattern:
                            if fnmatch.fnmatch(relpath, pattern):
                                is_valid_file_extension = True
                                continue
                        else:
                            if filename.endswith(pattern):
                                is_valid_file_extension = True
                                continue

                    if not is_valid_file_extension:
                        msg = "Not adding filename %s, does not match patterns: %s"
                        args = (filepath, ", ".join(add_new_files))
                        self.log_debug(msg % args)
                        continue

                elif isinstance(add_new_files, bool):
                    if not add_new_files:
                        msg = "add_new_files method should not be called if setting is False"
                        raise dexy.exceptions.InternalDexyProblem(msg)
                    is_valid_file_extension = True

                else:
                    msg = "add-new-files setting should be list or boolean. Type is %s value is %s"
                    args = (add_new_files.__class__, add_new_files,)
                    raise dexy.exceptions.InternalDexyProblem(msg % args)

                # Check if should be excluded.
                skip_because_excluded = False
                for skip_pattern in exclude:
                    if skip_pattern in filepath:
                        msg = "skipping adding new file %s because it matches exclude %s"
                        args = (filepath, skip_pattern,)
                        self.log_debug(msg % args)
                        skip_because_excluded = True
                        continue

                if skip_because_excluded:
                    continue

                if not is_valid_file_extension:
                    raise Exception("Should not get here unless is_valid_file_extension")

                self.log_debug("Adding %s" % filepath)
                with open(filepath, 'rb') as f:
                    raw_contents = f.read()

                try:
                    contents = raw_contents.decode('utf-8')
                except UnicodeDecodeError:
                    contents = raw_contents

                self.add_doc(relpath, contents)
                new_files_added += 1

        if new_files_added > 10:
            self.log_warn("%s additional files added" % (new_files_added))

    def run_command(self, command, env, input_text=None):
        if self.setting('use-wd'):
            ws = self.workspace()
            if os.path.exists(ws):
                self.log_debug("already have workspace '%s'" % os.path.abspath(ws))
            else:
                self.populate_workspace()

        stdout = subprocess.PIPE

        if input_text:
            stdin = subprocess.PIPE
        else:
            stdin = None

        if self.setting('write-stderr-to-stdout'):
            stderr = subprocess.STDOUT
        else:
            stderr = subprocess.PIPE

        if self.setting('use-wd'):
            wd = self.parent_work_dir()
        else:
            wd = os.getcwd()

        self.log_debug("about to run '%s' in '%s'" % (command, os.path.abspath(wd)))
        proc = subprocess.Popen(command, shell=True,
                                    cwd=wd,
                                    stdin=stdin,
                                    stdout=stdout,
                                    stderr=stderr,
                                    env=env)

        if input_text:
            self.log_debug("about to send input_text '%s'" % input_text)
            stdout, stderr = proc.communicate(input_text.encode())
        else:
            stdout, stderr = proc.communicate()

        self.log_debug("stdout is '%s'" % stdout.decode('utf-8'))

        if stderr:
            self.log_debug("stderr is '%s'" % stderr.decode('utf-8'))

        return (proc, stdout.decode('utf-8'))

    def copy_canonical_file(self):
        canonical_file = os.path.join(self.workspace(), self.output_data.name)
        if not self.output_data.is_cached() and file_exists(canonical_file):
            self.output_data.copy_from_file(canonical_file)

        if self.setting('add-new-files') and self.setting('make-dummy-output'):
            if not self.output_data.is_cached():
                self.output_data.set_data("ok")
                self.output_data.update_settings({"canonical-output": False})

class SubprocessStdoutFilter(SubprocessFilter):
    """
    Runs a command and returns the resulting stdout.
    """
    _settings = {
            'write-stderr-to-stdout' : False,
            'require-output' : False,
            'command-string' : '%(prog)s %(args)s "%(script_file)s" %(scriptargs)s'
            }

    def process(self):
        command = self.command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.output_data.set_data(stdout)

        if self.setting('add-new-files'):
            self.add_new_files()

class SubprocessCompileFilter(SubprocessFilter):
    """
    Compiles code and runs the compiled executable.
    """
    _settings = {
            'add-new-files' : False,
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
        basename = os.path.basename(self.input_data.name)
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
        self.handle_subprocess_proc_return(command, proc.returncode, stdout, compiled=True)

        self.output_data.set_data(stdout)

        if self.setting('add-new-files'):
            msg = "adding new files found in %s for %s" 
            msgargs = (self.workspace(), self.key)
            self.log_debug(msg % msgargs)
            self.add_new_files()

class SubprocessInputFilter(SubprocessFilter):
    """
    Runs code which expects stdin.
    """
    _settings = {
            'data-type' : 'sectioned',
            'check-return-code' : False,
            'write-stderr-to-stdout' : False
            }

    def process(self):
        command = self.command_string()

        inputs = list(self.doc.walk_input_docs())

        if len(inputs) == 1:
            doc = inputs[0]
            for section_name, section_input in doc.output_data().items():
                proc, stdout = self.run_command(command, self.setup_env(), str(section_input))
                self.output_data[section_name] = stdout
        else:
            for doc in inputs:
                proc, stdout = self.run_command(command, self.setup_env(), str(doc.output_data()))
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                self.output_data[doc.key] = stdout

        self.output_data.save()

class SubprocessInputFileFilter(SubprocessFilter):
    """
    Runs code which expects input files.
    """
    _settings = {
            'data-type' : 'sectioned',
            'check-return-code' : False,
            'write-stderr-to-stdout' : False,
            'command-string' : """%(prog)s %(args)s %(input_text)s "%(script_file)s" """
            }

    def command_string_args(self, input_doc):
        args = self.default_command_string_args()
        args['input_text'] = input_doc.name
        return args
    
    def command_string_for_input(self, input_doc):
        return self.setting('command-string') % self.command_string_args(input_doc)

    def process(self):
        self.populate_workspace()

        for doc in self.doc.walk_input_docs():
            command = self.command_string_for_input(doc)
            proc, stdout = self.run_command(command, self.setup_env())
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)
            self.output_data[doc.key] = stdout

        self.output_data.save()

class SubprocessCompileInputFilter(SubprocessCompileFilter):
    """
    Compiles code and runs executable with stdin.
    """
    _settings = {
            'data-type' : 'sectioned',
            'check-return-code' : False,
            'write-stderr-to-stdout' : False
            }

    def process(self):
        # Compile the code
        command = self.compile_command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        command = self.run_command_string()

        inputs = list(self.doc.walk_input_docs())

        if len(inputs) == 1:
            doc = inputs[0]
            for section_name, section_input in doc.output_data().items():
                proc, stdout = self.run_command(command, self.setup_env(), section_input)
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                self.output_data[section_name] = stdout
        else:
            for doc in inputs:
                proc, stdout = self.run_command(command, self.setup_env(), str(doc.output_data()))
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                self.output_data[doc.key] = stdout

        self.output_data.save()

class SubprocessFormatFlagFilter(SubprocessFilter):
    """
    Special handling of format flags based on file extensions.

    For example, ragel -R for ruby.
    """
    _settings = {
            'ext-to-format' : ("A dict of mappings from file extensions to format flags that need to be passed on the command line, e.g. for ragel with ruby host language .rb => -R", {})
            }

    def command_string_args(self):
        args = self.default_command_string_args()

        flags = self.setting('ext-to-format')

        if any(f in args['args'] for f in flags):
            # Already have specified the format manually.
            fmt = ''
        else:
            fmt = flags[self.ext]

        args['format'] = fmt
        return args

class SubprocessExtToFormatFilter(SubprocessFilter):
    """
    Subprocess filters which have ext-to-format param.
    """
    _settings = {
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
            fmt_setting = self.setting('ext-to-format')[self.ext]
            if fmt_setting:
                fmt = "%s%s" % (fmt_specifier, fmt_setting)
            else:
                fmt = ''

        args['format'] = fmt
        return args

class SubprocessStdoutTextFilter(SubprocessStdoutFilter):
    """
    Runs command with input passed on command line.
    """
    _settings = {
            'command-string' : "%(prog)s %(args)s \"%(text)s\"",
            'input-extensions' : ['.txt'],
            'output-extensions' : ['.txt']
            }

    def command_string_args(self):
        args = self.default_command_string_args()
        args['text'] = str(self.input_data)
        return args

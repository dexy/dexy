from dexy.common import OrderedDict
from dexy.filter import Filter
import dexy.exceptions
import fnmatch
import json
import os
import platform
import subprocess
from dexy.utils import file_exists

class SubprocessFilter(Filter):
    """
    Parent class for all filters which use the subprocess module to run external programs.
    """
    aliases = []
    _settings = {
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
            'initial-timeout' : ('', 10),
            'scriptargs' : ("Arguments to be passed to the executable.", ''),
            'timeout' : ('', 10),
            'use-wd' : ("Whether to use a custom working directory when running filter.", True),
            'version-command': ( "Command to call to return version of installed software.", None),
            'windows-version-command': ( "Command to call on windows to return version of installed software.", None),
            'walk-working-dir' : ("Automatically register extra files that are found in working dir.", False),
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
                return stdout.strip().split("\n")[0]

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

    def handle_subprocess_proc_return(self, command, exitcode, stderr):
        self.log_debug("exit code is '%s'" % exitcode)
        if exitcode is None:
            raise dexy.exceptions.InternalDexyProblem("no return code, proc not finished!")
        elif exitcode == 127:
            raise dexy.exceptions.InactiveFilter(self)
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
            for key, value in self.script_storage().iteritems():
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

        do_add_new = self.setting('add-new-files')
        exclude = self.setting('exclude-add-new-files')

        new_files_added = 0
        for dirpath, dirnames, filenames in os.walk(wd):
            for filename in filenames:
                filepath = os.path.normpath(os.path.join(dirpath, filename))
                relpath = os.path.relpath(filepath, wd)

                already_have_file = (relpath in self._files_workspace_populated_with)

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


                skip_because_excluded = False
                if exclude:
                    if isinstance(exclude, list):
                        for exclude_item in exclude:
                            if exclude_item in filepath:
                                skip_because_excluded = True
                                break
                    elif isinstance(exclude, basestring):
                        skip_because_excluded = exclude in filepath
                    else:
                        msg = "unexpected exclude type %s (%s)"
                        msgargs = (exclude.__class__.__name__, exclude)
                        raise dexy.exceptions.InternalDexyProblem(msg % msgargs)

                if (not already_have_file) and is_valid_file_extension and not skip_because_excluded:
                    with open(filepath, 'rb') as f:
                        contents = f.read()
                    self.add_doc(relpath, contents)
                    new_files_added += 1

        if new_files_added > 10:
            self.log_warn("%s additional files added" % (new_files_added))

    def walk_working_directory(self, doc=None, section_name=None):
        """
        Walk working directory and read contents of multiple files into a
        single new document.
        """
        if not doc:
            if section_name:
                doc_key = "%s-%s-files" % (self.output_data.long_name(), section_name)
            else:
                doc_key = "%s-files" % self.output_data.long_name()

            doc = self.add_doc(doc_key, {})

        doc.output_data().setup()
        doc.output_data().storage.connect()
        wd = self.workspace()

        for dirpath, dirnames, filenames in os.walk(wd):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                relpath = os.path.relpath(filepath, wd)

                with open(filepath, "rb") as f:
                    contents = f.read()
                try:
                    json.dumps(contents)
                    doc.output_data().append(relpath, contents)
                except UnicodeDecodeError:
                    doc.output_data().append(relpath, 'binary')

        return doc

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
            stderr = stdout
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

        stdout, stderr = proc.communicate(input_text)
        self.log_debug(u"stdout is '%s'" % stdout.decode('utf-8'))
        self.log_debug(u"stderr is '%s'" % stderr.decode('utf-8'))

        return (proc, stdout)

    def copy_canonical_file(self):
        canonical_file = os.path.join(self.workspace(), self.output_data.name)
        if not self.output_data.is_cached() and file_exists(canonical_file):
            self.output_data.copy_from_file(canonical_file)

class SubprocessStdoutFilter(SubprocessFilter):
    """
    Subclass of SubprocessFilter which runs a command and returns the stdout generated by that command as its output.
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

        if self.setting('walk-working-dir'):
            self.walk_working_directory()

        if self.setting('add-new-files'):
            self.add_new_files()

class SubprocessCompileFilter(SubprocessFilter):
    """
    Base class for filters which need to compile code, then run the compiled executable.
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
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        self.output_data.set_data(stdout)

        if self.setting('add-new-files'):
            msg = "adding new files found in %s for %s" 
            msgargs = (self.workspace(), self.key)
            self.log_debug(msg % msgargs)
            self.add_new_files()

class SubprocessInputFilter(SubprocessFilter):
    """
    Filters which run a task in subprocess while also writing content to stdin for that process.
    """
    _settings = {
            'output-data-type' : 'sectioned',
            'check-return-code' : False,
            'write-stderr-to-stdout' : False
            }

    def process(self):
        command = self.command_string()

        inputs = list(self.doc.walk_input_docs())

        output = OrderedDict()

        if len(inputs) == 1:
            doc = inputs[0]
            for section_name, section_text in doc.output_data().as_sectioned().iteritems():
                proc, stdout = self.run_command(command, self.setup_env(), section_text)
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[section_name] = stdout
        else:
            for doc in inputs:
                proc, stdout = self.run_command(command, self.setup_env(), unicode(doc.output_data()))
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[doc.key] = stdout

        self.output_data.set_data(output)

class SubprocessInputFileFilter(SubprocessFilter):
    """
    Filters which run one or more input files through the script via filenames.
    """
    _settings = {
            'output-data-type' : 'sectioned',
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
        output = OrderedDict()

        for doc in self.doc.walk_input_docs():
            command = self.command_string_for_input(doc)
            proc, stdout = self.run_command(command, self.setup_env())
            self.handle_subprocess_proc_return(command, proc.returncode, stdout)
            output[doc.key] = stdout

        self.output_data.set_data(output)

class SubprocessCompileInputFilter(SubprocessCompileFilter):
    """
    Filters which compile code, then run it with input.
    """
    _settings = {
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

        inputs = list(self.doc.walk_input_docs())

        output = OrderedDict()

        if len(inputs) == 1:
            doc = inputs[0]
            for section_name, section_text in doc.output_data().as_sectioned().iteritems():
                proc, stdout = self.run_command(command, self.setup_env(), section_text)
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[section_name] = stdout
        else:
            for doc in inputs:
                proc, stdout = self.run_command(command, self.setup_env(), doc.output_data().as_text())
                self.handle_subprocess_proc_return(command, proc.returncode, stdout)
                output[doc.key] = stdout

        self.output_data.set_data(output)

class SubprocessFormatFlagFilter(SubprocessFilter):
    """
    Subprocess filters which have to pass a format flag (like ragel -R for ruby).
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
    _settings = {
            'command-string' : "%(prog)s %(args)s \"%(text)s\"",
            'input-extensions' : ['.txt'],
            'output-extensions' : ['.txt']
            }

    def command_string_args(self):
        args = self.default_command_string_args()
        args['text'] = self.input_data.as_text()
        return args

from dexy.plugins.pexpect_filters import PexpectReplFilter
from dexy.plugins.process_filters import SubprocessCompileFilter
from dexy.plugins.process_filters import SubprocessStdoutFilter
import os
import platform

class JrubyFilter(SubprocessStdoutFilter):
    """
    Run jruby code and return stdout.
    """
    ALIASES = ['jruby']
    EXECUTABLE = "jruby"
    INPUT_EXTENSIONS = [".rb", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = "jruby --version"

class JirbFilter(PexpectReplFilter):
    """
    Run jruby code in jirb.
    """
    ALIASES = ['jirb']
    ALLOW_MATCH_PROMPT_WITHOUT_NEWLINE = True
    CHECK_RETURN_CODE = False
    EXECUTABLE = "jirb --prompt-mode simple"
    INITIAL_PROMPT_TIMEOUT = 30
    INPUT_EXTENSIONS = [".rb", ".txt"]
    OUTPUT_EXTENSIONS = [".rbcon"]
    PROMPTS = ['>>', '?>']
    VERSION_COMMAND = "jirb --version"

class JythonFilter(SubprocessStdoutFilter):
    """
    jython
    """
    ALIASES = ['jython']
    EXECUTABLE = "jython"
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = "jython --version"

    @classmethod
    def is_active(klass):
        if platform.system() in ('Linux', 'Windows'):
            return klass.executable() and True or False
        elif platform.system() in ('Darwin'):
            if hasattr(klass, 'log'):
                klass.log.warn("The jython dexy filter should not be run on MacOS due to a serious bug. This filter is being disabled.")
            return False
        else:
            if hasattr(klass, 'log'):
                klass.log.warn("""Can't detect your system. If you see this message please report this to the dexy project maintainer, your platform.system() value is '%s'. The jython dexy filter should not be run on MacOS due to a serious bug.""" % platform.system())
            return klass.executable() and True or False

class JythonInteractiveFilter(PexpectReplFilter):
    """
    jython in REPL
    """
    ALIASES = ['jythoni']
    CHECK_RETURN_CODE = False
    EXECUTABLE = "jython -i"
    INITIAL_PROMPT_TIMEOUT = 30
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".pycon"]
    VERSION_COMMAND = "jython --version"

    @classmethod
    def is_active(klass):
        if platform.system() in ('Linux', 'Windows'):
            return klass.executable() and True or False
        elif platform.system() in ('Darwin'):
            print "The jythoni dexy filter should not be run on MacOS due to a serious bug. This filter is being disabled."
            return False
        else:
            print """Can't detect your system. If you see this message please report this to the dexy project maintainer, your platform.system() value is '%s'. The jythoni dexy filter should not be run on MacOS due to a serious bug.""" % platform.system()
            return klass.executable() and True or False

class JavaFilter(SubprocessCompileFilter):
    """
    Compiles java code and runs main method.
    """
    ALIASES = ['java']
    CHECK_RETURN_CODE = True # Whether to check return code when running compiled executable.
    COMPILED_EXTENSION = ".class"
    EXECUTABLE = "javac"
    INPUT_EXTENSIONS = [".java"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = "java -version"

    def setup_cp(self):
        """
        Makes sure the current working directory is on the classpath, also adds
        any specified CLASSPATH elements. Assumes that CLASSPATH elements are either
        absolute paths, or paths relative to the artifacts directory. Also, if
        an input has been passed through the javac filter, its directory is
        added to the classpath.
        """
        self.log.debug("in setup_cp for %s" % self.artifact.key)

        classpath_elements = []

        working_dir = os.path.join(self.artifact.tmp_dir(), self.output().parent_dir())
        abs_working_dir = os.path.abspath(working_dir)
        self.log.debug("Adding working dir %s to classpath" % abs_working_dir)
        classpath_elements.append(abs_working_dir)

        for doc in self.processed():
            if (doc.output().ext == ".class") and ("javac" in doc.key):
                classpath_elements.append(doc.output().parent_dir())

        for item in self.args().get('classpath', []):
            for x in item.split(":"):
                classpath_elements.append(x)

        env = self.setup_env()
        if env and env.has_key("CLASSPATH"):
            for x in env['CLASSPATH'].split(":"):
                classpath_elements.append(x)

        cp = ":".join(classpath_elements)
        self.log.debug("Classpath %s" % cp)
        return cp

    def compile_command_string(self):
        cp = self.setup_cp()
        basename = os.path.basename(self.input().name)
        if len(cp) == 0:
            return "javac %s" % basename
        else:
            return "javac -classpath %s %s" % (cp, basename)

    def run_command_string(self):
        cp = self.setup_cp()
        main_method = self.setup_main_method()
        args = self.command_line_args() or ""
        return "java %s -cp %s %s" % (args, cp, main_method)

    def setup_main_method(self):
        basename = os.path.basename(self.input().name)
        default_main = os.path.splitext(basename)[0]
        return self.args().get('main', default_main)

class JavacFilter(JavaFilter):
    """
    Compiles java code and returns the .class object
    """
    ALIASES = ['javac']
    EXECUTABLE = "javac"
    INPUT_EXTENSIONS = [".java"]
    OUTPUT_EXTENSIONS = [".class"]
    VERSION_COMMAND = "java -version"

    def process(self):
        # Compile the code
        command = self.compile_command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)
        self.copy_canonical_file()

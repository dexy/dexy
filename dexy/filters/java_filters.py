from dexy.dexy_filter import DexyFilter
from dexy.filters.pexpect_filters import PexpectReplFilter
from dexy.filters.process_filters import SubprocessCompileFilter
from dexy.filters.process_filters import SubprocessStdoutFilter
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers.compiled import JavaLexer
import json
import os
import platform
import shutil

class JrubyFilter(SubprocessStdoutFilter):
    ALIASES = ['jruby']
    EXECUTABLE = "jruby"
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = "jruby --version"

class JirbFilter(PexpectReplFilter):
    ALIASES = ['jirb']
    ALLOW_MATCH_PROMPT_WITHOUT_NEWLINE = True
    EXECUTABLE = "jirb --prompt-mode simple"
    CHECK_RETURN_CODE = False
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".rbcon"]
    PROMPTS = ['>>', '?>']
    VERSION_COMMAND = "jirb --version"

class JythonFilter(SubprocessStdoutFilter):
    ALIASES = ['jython']
    EXECUTABLE = "jython"
    INPUT_EXTENSIONS = [".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION_COMMAND = "jython --version"

    @classmethod
    def enabled(self):
        if platform.system() in ('Linux', 'Windows'):
            return True
        elif platform.system() in ('Darwin'):
            if hasattr(self, 'log'):
                self.log.warn("The jython dexy filter should not be run on MacOS due to a serious bug. This filter is being disabled.")
            return False
        else:
            if hasattr(self, 'log'):
                self.log.warn("""Can't detect your system. If you see this message please report this to the dexy project maintainer, your platform.system() value is '%s'. The jython dexy filter should not be run on MacOS due to a serious bug.""" % platform.system())
            return True

class JythonInteractiveFilter(PexpectReplFilter):
    ALIASES = ['jythoni']
    EXECUTABLE = "jython -i"
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".pycon"]
    VERSION_COMMAND = "jython --version"
    CHECK_RETURN_CODE = False

    @classmethod
    def enabled(self):
        if platform.system() in ('Linux', 'Windows'):
            return True
        elif platform.system() in ('Darwin'):
            print "The jythoni dexy filter should not be run on MacOS due to a serious bug. This filter is being disabled."
            return False
        else:
            print """Can't detect your system. If you see this message please report this to the dexy project maintainer, your platform.system() value is '%s'. The jythoni dexy filter should not be run on MacOS due to a serious bug.""" % platform.system()
            return True

class JavaFilter(SubprocessCompileFilter):
    ALIASES = ['java']
    CHECK_RETURN_CODE = True # Whether to check return code when running compiled executable.
    COMPILED_EXTENSION = ".class"
    EXECUTABLE = "javac"
    FINAL = False
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
        env = self.setup_env()

        classpath_elements = []
        classpath_elements.append(os.path.dirname(self.artifact.name))

        for key, input_artifact in self.artifact.inputs().iteritems():
            if input_artifact.ext == ".class" and "javac" in key:
                classpath_elements.append(os.path.dirname(input_artifact.name))

        if env and env.has_key("CLASSPATH"):
            for x in env['CLASSPATH'].split(":"):
                if x.startswith("/"):
                    # absolute path, leave it alone
                    classpath_elements.append(x)
                else:
                    # path relative to artifacts directory, need to adjust
                    # since we are working in a subdir of artifacts
                    classpath_elements.append(os.path.join("..", x))

        cp = ":".join(classpath_elements)

        return cp

    def compile_command_string(self):
        cp = self.setup_cp()
        return "javac -classpath %s %s" % (cp, self.artifact.name)

    def run_command_string(self):
        cp = self.setup_cp()
        main_method = self.setup_main_method()
        args = self.command_line_args() or ""
        return "java %s -cp %s %s" % (args, cp, main_method)

    def setup_cwd(self):
        tempdir = self.artifact.temp_dir()

        # if this is the 2nd time we are calling this, don't want our compiled .class to be deleted
        if not os.path.exists(tempdir):
            self.artifact.create_temp_dir(True)

        return tempdir

    def setup_main_method(self):
        if self.artifact.args.has_key('main'):
            return self.artifact.args['main']
        else:
            return os.path.splitext(os.path.basename(self.artifact.name))[0]

class JavacFilter(JavaFilter):
    ALIASES = ['javac']
    BINARY = True
    EXECUTABLE = "javac"
    INPUT_EXTENSIONS = [".java"]
    OUTPUT_EXTENSIONS = [".class"]
    VERSION_COMMAND = "java -version"

    def process(self):
        # Compile the code
        command = self.compile_command_string()
        proc, stdout = self.run_command(command, self.setup_env())
        self.handle_subprocess_proc_return(command, proc.returncode, stdout)

        # Copy compiled .class file to where it should live
        tempdir = self.artifact.temp_dir()
        compiled_file = os.path.join(tempdir, self.artifact.canonical_filename())
        shutil.copyfile(compiled_file, self.artifact.filepath())

class JavadocsJsonFilter(DexyFilter):
    ALIASES = ['javadoc', 'javadocs']

    def nested_subclasses(self, j, qualified_class_name, nest=None, indent = 0):
        if not nest:
            nest = [[indent, qualified_class_name]]
        package_name, x, class_name = qualified_class_name.rpartition(".")
        if j['packages'][package_name]['classes'][class_name].has_key('subclasses'):
            subclasses = j['packages'][package_name]['classes'][class_name]['subclasses']
            for qualified_subclass_name in subclasses:
                nest.append([indent+1, qualified_subclass_name])
                subclass_package_name, x, subclass_name = qualified_subclass_name.rpartition(".")
                if j['packages'][subclass_package_name]['classes'][subclass_name].has_key('subclasses'):
                    self.nested_subclasses(j, qualified_subclass_name, nest, indent+1)
        return nest

    def process_text(self, input_text):
        j = json.loads(input_text)

        html_formatter = HtmlFormatter()
        latex_formatter = LatexFormatter()
        lexer = JavaLexer()

        for p in j['packages']:
            for k in j['packages'][p]['classes'].keys():

                klass = j['packages'][p]['classes'][k]
                if klass.has_key('superclass'):
                    superclass_package, _, superclass_name = klass['superclass'].rpartition(".")
                    if j['packages'].has_key(superclass_package):
                        if not j['packages'][superclass_package]['classes'].has_key(superclass_name):
                            self.log.warn("Can't find %s in package %s" % (superclass_name, superclass_package))
                        else:
                            superclass = j['packages'][superclass_package]['classes'][superclass_name]
                            if not superclass.has_key('subclasses'):
                                superclass['subclasses'] = []

                            superclass['subclasses'].append("%s.%s" % (p, k))

                if klass.has_key('interfaces'):
                    for iface in klass['interfaces']:
                        iface_package, _, iface_name = iface.rpartition(".")
                        if j['packages'].has_key(iface_package):
                            if not j['packages'][iface_package]['classes'].has_key(iface_name):
                                self.log.warn("Can't find", iface_name, "in package", iface_package)
                            else:
                                iface_dict = j['packages'][iface_package]['classes'][iface_name]
                                if not iface_dict.has_key('implementers'):
                                    iface_dict['implementers'] = []
                                iface_dict['implementers'].append(klass['qualified-name'])
                if klass.has_key('source') and klass['source']:
                    source = klass['source']
                    j['packages'][p]['classes'][k]['source-html'] = str(highlight(source, lexer, html_formatter))
                    j['packages'][p]['classes'][k]['source-latex'] = str(highlight(source, lexer, latex_formatter))

                for m in j['packages'][p]['classes'][k]['methods'].keys():
                    source = j['packages'][p]['classes'][k]['methods'][m]['source']
                    if not source:
                        source = ""

                    # TODO - try running comment text through Textile
                    # interpreter for HTML and LaTeX options
                    comment = j['packages'][p]['classes'][k]['methods'][m]['comment-text']


                    j['packages'][p]['classes'][k]['methods'][m]['comment'] = comment
                    j['packages'][p]['classes'][k]['methods'][m]['source'] = source
                    j['packages'][p]['classes'][k]['methods'][m]['source-html'] = str(highlight(source, lexer, html_formatter))
                    j['packages'][p]['classes'][k]['methods'][m]['source-latex'] = str(highlight(source, lexer, latex_formatter))

                for c in j['packages'][p]['classes'][k]['constructors'].keys():
                    source = j['packages'][p]['classes'][k]['constructors'][c]['source']
                    if not source:
                        source = ""

                    # TODO - try running comment text through Textile
                    # interpreter for HTML and LaTeX options
                    comment = j['packages'][p]['classes'][k]['constructors'][c]['comment-text']

                    j['packages'][p]['classes'][k]['constructors'][c]['comment'] = comment
                    j['packages'][p]['classes'][k]['constructors'][c]['source'] = source
                    j['packages'][p]['classes'][k]['constructors'][c]['source-html'] = str(highlight(source, lexer, html_formatter))
                    j['packages'][p]['classes'][k]['constructors'][c]['source-latex'] = str(highlight(source, lexer, latex_formatter))

        return json.dumps(j)

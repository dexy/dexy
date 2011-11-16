from dexy.dexy_filter import DexyFilter
from dexy.filters.pexpect_filters import PexpectReplFilter
from dexy.filters.process_filters import SubprocessStdoutFilter
from dexy.filters.process_filters import SubprocessCompileFilter
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers.compiled import JavaLexer
import json
import os
import platform
import shutil

class JrubyFilter(SubprocessStdoutFilter):
    VERSION = "jruby --version"
    EXECUTABLE = "jruby"
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jruby']

class JirbFilter(PexpectReplFilter):
    ALIASES = ['jirb']
    ALLOW_MATCH_PROMPT_WITHOUT_NEWLINE = True
    EXECUTABLE = "jirb --prompt-mode simple"
    IGNORE_ERRORS = True # Returns nonzero exit code even when no errors.
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".rbcon"]
    PROMPTS = ['>>', '?>']
    VERSION = "jirb --version"

class JythonFilter(SubprocessStdoutFilter):
    VERSION = "jython --version"
    EXECUTABLE = "jython"
    INPUT_EXTENSIONS = [".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jython']

    @classmethod
    def enabled(self):
        if platform.system() in ('Linux', 'Windows'):
            return True
        elif platform.system() in ('Darwin'):
            self.log.warn("The jython dexy filter should not be run on MacOS due to a serious bug. This filter is being disabled.")
            return False
        else:
            self.log.warn("""Can't detect your system. If you see this message please report this to the dexy project maintainer, your platform.system() value is '%s'. The jython dexy filter should not be run on MacOS due to a serious bug.""" % platform.system())
            return True

class JythonInteractiveFilter(PexpectReplFilter):
    VERSION = "jython --version"
    EXECUTABLE = "jython -i"
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".pycon"]
    ALIASES = ['jythoni']

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
    INPUT_EXTENSIONS = [".java"]
    OUTPUT_EXTENSIONS = [".txt"]
    VERSION = "java -version"

    def setup_cp(self):
        env = self.setup_env()

        cp = "."

        if env and env.has_key("CLASSPATH"):
            # need to add 1 level to classpath since we are working in a subdir of artifacts/
            env['CLASSPATH'] = ":".join(["../%s" % x for x in env['CLASSPATH'].split(":")])
            cp = "%s:%s" % (cp, env['CLASSPATH'])

        return cp

    def compile_command_string(self):
        cp = self.setup_cp()
        return "javac -classpath %s %s" % (cp, os.path.basename(self.artifact.name))

    def run_command_string(self):
        cp = self.setup_cp()
        main_method = self.setup_main_method()
        return "java -cp %s %s" % (cp, main_method)

    def setup_cwd(self):
        tempdir = self.artifact.temp_dir()

        if not os.path.exists(tempdir):
            self.artifact.create_temp_dir()
            previous = self.artifact.previous_artifact_filepath
            workfile = os.path.join(tempdir, os.path.basename(self.artifact.previous_canonical_filename))
            shutil.copyfile(previous, workfile)

        return tempdir

    def setup_main_method(self):
        if self.artifact.args.has_key('main'):
            return self.artifact.args['main']
        else:
            return os.path.splitext(os.path.basename(self.artifact.name))[0]

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

        # Update our JSON array with each input data file.
        def update_dict(o, n):
            for k in o.keys():
                if n.has_key(k):
                    v = o[k]
                    if isinstance(v, dict):
                        o[k] = update_dict(v, n[k])
                    else:
                        o[k].update(n[k])
            return o

        for k, a in self.artifact.inputs().items():
            new_data = json.loads(a.output_text())
            j = update_dict(j, new_data)

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

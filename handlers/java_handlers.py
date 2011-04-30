from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers.compiled import JavaLexer
import dexy.handler
import handlers.pexpect_handlers
import handlers.stdout_handlers
import json
import os
import subprocess

class JrubyHandler(handlers.stdout_handlers.ProcessStdoutHandler):
    VERSION = "jruby --version"
    EXECUTABLE = "jruby"
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jruby']

class JirbHandler(handlers.pexpect_handlers.ProcessLinewiseInteractiveHandler):
    VERSION = "jirb --version"
    EXECUTABLE = "jirb --prompt-mode simple"
    INPUT_EXTENSIONS = [".rb"]
    PROMPT = ">>|\?>"
    OUTPUT_EXTENSIONS = [".rbcon"]
    ALIASES = ['jirb']
    IGNORE_ERRORS = True

class JythonHandler(handlers.stdout_handlers.ProcessStdoutHandler):
    VERSION = "jython --version"
    EXECUTABLE = "jython"
    INPUT_EXTENSIONS = [".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jython']

class JythonInteractiveHandler(handlers.pexpect_handlers.ProcessLinewiseInteractiveHandler):
    VERSION = "jython --version"
    EXECUTABLE = "jython -i"
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".pycon"]
    ALIASES = ['jythoni']

class JavaHandler(dexy.handler.DexyHandler):
    EXECUTABLE = "javac"
    VERSION = "java -version"
    INPUT_EXTENSIONS = [".java"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['java']

    def process(self):
        if self.doc.args.has_key('main'):
            main_method = self.doc.args['main']
        else:
            main_method = os.path.splitext(os.path.basename(self.doc.name))[0]

        if self.artifact.doc.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.doc.args['env'])
        else:
            env = None

        self.artifact.create_temp_dir()

        command = "javac -d %s %s" % (
            self.artifact.temp_dir(), self.doc.name)

        self.log.debug(command)
        proc = subprocess.Popen(command, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)
        stdout, stderr = proc.communicate()
        self.log.debug("stdout from compiler:\n%s" % stdout)
        self.log.debug("stderr from compiler:\n%s" % stderr)
        if proc.returncode > 0:
            raise Exception("a problem occurred running %s.\ndetails:\n%s" % (
                command, stderr))

        cp = self.artifact.temp_dir()
        if self.doc.args.has_key('env'):
            if self.doc.args['env'].has_key('CLASSPATH'):
                cp = "%s:%s" % (self.artifact.temp_dir(),
                                self.doc.args['env']['CLASSPATH'])

        command = "java -cp %s %s" % (cp, main_method)
        self.log.debug(command)
        proc = subprocess.Popen(command, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)
        stdout, stderr = proc.communicate()
        if proc.returncode > 0:
            raise Exception("a problem occurred running %s.\ndetails:\n%s" % (
                command, stderr))

        self.artifact.data_dict['1'] = stdout

class JavadocsJsonFilter(dexy.handler.DexyHandler):
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
                            print "Can't find", superclass_name, "in package", superclass_package
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
                                print "Can't find", iface_name, "in package", iface_package
                            else:
                                iface_dict = j['packages'][iface_package]['classes'][iface_name]
                                if not iface_dict.has_key('implementers'):
                                    iface_dict['implementers'] = []
                                iface_dict['implementers'].append(klass['qualified-name'])

                for m in j['packages'][p]['classes'][k]['methods'].keys():
                    source = j['packages'][p]['classes'][k]['methods'][m]['source']

                    # TODO - try running comment text through Textile
                    # interpreter for HTML and LaTeX options
                    comment = j['packages'][p]['classes'][k]['methods'][m]['comment-text']

                    html_formatter = HtmlFormatter()
                    latex_formatter = LatexFormatter()
                    lexer = JavaLexer()

                    j['packages'][p]['classes'][k]['methods'][m]['comment'] = comment
                    j['packages'][p]['classes'][k]['methods'][m]['source'] = source
                    j['packages'][p]['classes'][k]['methods'][m]['source-html'] = str(highlight(source, lexer, html_formatter))
                    j['packages'][p]['classes'][k]['methods'][m]['source-latex'] = str(highlight(source, lexer, latex_formatter))

        return json.dumps(j)

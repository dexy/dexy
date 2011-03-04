from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers.compiled import JavaLexer
import dexy.handler
import handlers.pexpect_handlers
import handlers.stdout_handlers
import json
import os
import pexpect
import subprocess
import time

### @export "jruby-handler"
class JrubyHandler(handlers.stdout_handlers.ProcessStdoutHandler):
    VERSION = "/usr/bin/env jruby --version"
    EXECUTABLE = "/usr/bin/env jruby"
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jruby']

### @export "jirb-handler"
class JirbHandler(handlers.pexpect_handlers.ProcessLinewiseInteractiveHandler):
    VERSION = "/usr/bin/env jirb --version"
    EXECUTABLE = "/usr/bin/env jirb --prompt-mode simple"
    INPUT_EXTENSIONS = [".rb"]
    PROMPT = ">>|\?>"
    OUTPUT_EXTENSIONS = [".rbcon"]
    ALIASES = ['jirb']

### @export "jython-handler"
class JythonHandler(handlers.stdout_handlers.ProcessStdoutHandler):
    VERSION = "/usr/bin/env jython --version"
    EXECUTABLE = "/usr/bin/env jython"
    INPUT_EXTENSIONS = [".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jython']

### @export "jython-interactive-handler"
class JythonInteractiveHandler(handlers.pexpect_handlers.ProcessLinewiseInteractiveHandler):
    VERSION = "/usr/bin/env jython --version"
    EXECUTABLE = "/usr/bin/env jython -i"
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".pycon"]
    ALIASES = ['jythoni']

### @export "java-handler"
class JavaHandler(dexy.handler.DexyHandler):
    VERSION = "/usr/bin/env java -version"
    INPUT_EXTENSIONS = [".java"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['java']

    def process(self):
        if self.artifact.doc.args.has_key('main'):
            main_method = self.artifact.doc.args['main']
        else:
            raise Exception("""You must specify the fully qualified class name of the 'main' method you wish to run.""")

        if self.artifact.doc.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.doc.args['env'])
        else:
            env = None

        self.artifact.create_temp_dir()

        compile_command = "/usr/bin/env javac -d %s %s" % (
            self.artifact.temp_dir(), self.doc.name)

        self.log.debug(compile_command)
        proc = subprocess.Popen(compile_command, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)
        proc.wait()


        command = "/usr/bin/env java -cp %s %s" % (
            self.artifact.temp_dir(), main_method)
        self.log.debug(command)
        proc = subprocess.Popen(command, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)
        proc.wait()
        self.artifact.data_dict['1'] = proc.stdout.read()

### @export "javadoc-json-handler"
class JavadocsJsonFilter(dexy.handler.DexyHandler):
    ALIASES = ['javadocs']
    def process_text(self, input_text):
        j = json.loads(input_text)
        for p in j['packages']:
            for k in j['packages'][p]['classes'].keys():
                for m in j['packages'][p]['classes'][k]['methods'].keys():
                    source = j['packages'][p]['classes'][k]['methods'][m]['source']
                    html_formatter = HtmlFormatter()
                    latex_formatter = LatexFormatter()
                    lexer = JavaLexer()

                    source_array = source.split("\n")
                    if source_array[-1] == "@Override":
                        source = source_array[:-1].join("\n")

                    j['packages'][p]['classes'][k]['methods'][m]['source'] = source
                    j['packages'][p]['classes'][k]['methods'][m]['source-html'] = str(highlight(source, lexer, html_formatter))
                    j['packages'][p]['classes'][k]['methods'][m]['source-latex'] = str(highlight(source, lexer, latex_formatter))

        return json.dumps(j)

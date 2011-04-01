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
    VERSION = "/usr/bin/env jruby --version"
    EXECUTABLE = "/usr/bin/env jruby"
    INPUT_EXTENSIONS = [".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jruby']

class JirbHandler(handlers.pexpect_handlers.ProcessLinewiseInteractiveHandler):
    VERSION = "/usr/bin/env jirb --version"
    EXECUTABLE = "/usr/bin/env jirb --prompt-mode simple"
    INPUT_EXTENSIONS = [".rb"]
    PROMPT = ">>|\?>"
    OUTPUT_EXTENSIONS = [".rbcon"]
    ALIASES = ['jirb']
    IGNORE_ERRORS = True

class JythonHandler(handlers.stdout_handlers.ProcessStdoutHandler):
    VERSION = "/usr/bin/env jython --version"
    EXECUTABLE = "/usr/bin/env jython"
    INPUT_EXTENSIONS = [".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['jython']

class JythonInteractiveHandler(handlers.pexpect_handlers.ProcessLinewiseInteractiveHandler):
    VERSION = "/usr/bin/env jython --version"
    EXECUTABLE = "/usr/bin/env jython -i"
    INPUT_EXTENSIONS = [".py", ".txt"]
    OUTPUT_EXTENSIONS = [".pycon"]
    ALIASES = ['jythoni']

class JavaHandler(dexy.handler.DexyHandler):
    VERSION = "/usr/bin/env java -version"
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

        command = "/usr/bin/env javac -d %s %s" % (
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

        command = "/usr/bin/env java -cp %s %s" % (cp, main_method)
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

        self.artifact.load_input_artifacts()
        for k, a in self.artifact.input_artifacts_dict.items():
            new_data = json.loads(a['data'])
            j = update_dict(j, new_data)


        for p in j['packages']:
            for k in j['packages'][p]['classes'].keys():
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

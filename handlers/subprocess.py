try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from dexy.handler import DexyHandler

import os
import pexpect
import time

### @export "linewise"
class ProcessLinewiseInteractiveHandler(DexyHandler):
    """
    Intended for use with interactive processes, such as python interpreter,
    where your goal is to have a session transcript divided into same sections
    as input.
    """
    EXECUTABLE = '/usr/bin/env python'
    PROMPT = '>>>|\.\.\.' # Python uses >>> prompt normally and ... when in multi-line structures like loops
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".pycon"]
    ALIASES = ['pycon']

    def process_dict(self, input_dict):
        output_dict = OrderedDict()

        proc = pexpect.spawn(self.EXECUTABLE, cwd=self.artifact.artifacts_dir)
        proc.expect(self.PROMPT)
        start = (proc.before + proc.after)

        for k, s in input_dict.items():
            # TODO Should stop processing if an error is raised.
            section_transcript = start
            start = ""
            for l in s.split("\n"):
                section_transcript += start
                start = ""
                proc.sendline(l)
                if self.artifact.doc.args.has_key('timeout'):
                    timeout = self.artifact.doc.args['timeout']
                    print "using custom timeout %s" % timeout
                else:
                    timeout = None
                proc.expect(self.PROMPT, timeout=timeout)
                section_transcript += proc.before
                start = proc.after
            output_dict[k] = section_transcript
        return output_dict

### @export "sectionwise"
class ProcessSectionwiseInteractiveHandler(DexyHandler):
    EXECUTABLE = '/usr/bin/env R --quiet --vanilla'
    VERSION = "/usr/bin/env R --version"
    PROMPT = '>'
    COMMENT = '#'
    TRAILING_PROMPT = "\r\n> "
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = ['.Rout']
    ALIASES = ['rint']
    
    def process_dict(self, input_dict):
         output_dict = OrderedDict()
 
         proc = pexpect.spawn(self.EXECUTABLE, cwd=self.artifact.artifacts_dir)
         proc.expect(self.PROMPT)
         start = (proc.before + proc.after)
         
         for k, s in input_dict.items():
             section_transcript = start
             start = ""
             proc.send(s)
             proc.sendline(self.COMMENT * 5)
             if self.artifact.doc.args.has_key('timeout'):
                 timeout = self.artifact.doc.args['timeout']
             else:
                 timeout = None

             proc.expect(self.COMMENT * 5, timeout = timeout)
 
             section_transcript += proc.before.rstrip(self.TRAILING_PROMPT)
             output_dict[k] = section_transcript

         return output_dict

### @export "stdout"
class ProcessStdoutHandler(DexyHandler):
    """
    Intended for use with command line processes where your only interest is in
    the contents of stdout.
    """
    EXECUTABLE = '/usr/bin/env python'
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['py', 'python', 'pyout']
    
    def process(self):
        self.artifact.generate_workfile()
        if self.artifact.doc.args.has_key('timeout'):
            timeout = self.artifact.doc.args['timeout']
        else:
            timeout = None
        command = "%s %s" % (self.EXECUTABLE, self.artifact.work_filename(False))
        cla = self.artifact.command_line_args()
        if cla:
            command = "%s %s" % (command, cla)
        self.log.debug(command)
        output, exit_status = pexpect.run(command, withexitstatus = True,
                                          timeout=timeout,
                                          cwd=self.artifact.artifacts_dir)
        self.artifact.data_dict['1'] = output
        if exit_status != 0:
            # TODO rework this - probably want to raise error + not write
            # artifact, or have option to ignore errors.
            self.log.warn("an error occurred:\n%s" % output)
            self.artifact.dirty = True

### @export "bash"
class BashHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env bash'
    INPUT_EXTENSIONS = [".sh", ".bash"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['bash']

### @export "php"
class PhpHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env php'
    INPUT_EXTENSIONS = [".php"]
    OUTPUT_EXTENSIONS = [".html", ".txt"]
    ALIASES = ['php']

### @export "escript"
class EscriptHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env escript'
    INPUT_EXTENSIONS = [".erl"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['escript']

### @export "clojure"
class ClojureInteractiveHandler(ProcessLinewiseInteractiveHandler):
    EXECUTABLE = 'java clojure.main'
    INPUT_EXTENSIONS = [".clj"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['clj', 'cljint']
    PROMPT = "user=> "

### @export "lua"
# TODO Add support for lua-style comments to idiopidae fork
class LuaHandler(ProcessSectionwiseInteractiveHandler):
    EXECUTABLE = '/usr/bin/env lua'
    VERSION = '/usr/bin/env lua -v'
    INPUT_EXTENSIONS = ['.lua', '.txt']
    OUTPUT_EXTENSIONS = ['.txt']
    ALIASES = ['lua']
    PROMPT = '>'
    TRAILING_PROMPT = '>>'

### @export "luaout"
class LuaStdoutHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env lua'
    VERSION = '/usr/bin/env lua -v'
    INPUT_EXTENSIONS = ['.lua']
    OUTPUT_EXTENSIONS = ['.txt']
    ALIASES = ['luaout']

### @export "redcloth"
class RedclothHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env redcloth'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['redcloth', 'textile']

### @export "redclothl"
class RedclothLatexHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env redcloth -o latex'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['redclothl', 'latextile']

### @export "rst2html"
class Rst2HtmlHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env rst2html.py'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['rst2html']

### @export "rst2latex"
class Rst2LatexHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env rst2latex.py'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2latex']

### @export "rst2beamer"
class Rst2BeamerHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env rst2beamer'
    INPUT_EXTENSIONS = [".rst", ".txt"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['rst2beamer']

### @export "sloccount"
class SloccountHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env sloccount'
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['sloc', 'sloccount']

### @export "timing"
class ProcessTimingHandler(DexyHandler):
    """
    Runs code N times and reports timings.
    """
    EXECUTABLE = '/usr/bin/env python'
    VERSION = '/usr/bin/env python --version'
    N = 10
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".times"]
    ALIASES = ['timing', 'pytime']
    
    def process(self):
        self.artifact.generate_workfile()
        times = []
        for i in xrange(self.N):
            start = time.time()
            pexpect.run("%s %s" % (self.EXECUTABLE, self.artifact.work_filename()))
            times.append("%s" % (time.time() - start))
        self.artifact.data_dict['1'] = "\n".join(times)

### @export "rout"
# This is sort of a duplicate of the Sectionwise Interactive Handler
# but the 
class ROutputHandler(DexyHandler):
    """Returns a full transcript, commands and output from each line."""
    EXECUTABLE = '/usr/bin/env R CMD BATCH --vanilla --quiet --no-timing'
    VERSION = "/usr/bin/env R --version"
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".Rout"]
    ALIASES = ['r', 'R']

    def generate(self):
        self.artifact.write_dj()

    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename(False)
        af = self.artifact.filename(False)
        pexpect.run("%s %s %s" % (self.EXECUTABLE, wf, af), cwd=self.artifact.artifacts_dir)
        self.artifact.data_dict['1'] = open(self.artifact.filename(), "r").read()


### @export "rartifact"
class RArtifactHandler(DexyHandler):
    """Uses the --slave flag so doesn't echo commands, just returns output."""
    EXECUTABLE = '/usr/bin/env R CMD BATCH --vanilla --quiet --slave --no-timing'
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rart']
    
    def process(self):
        self.artifact.auto_write_artifact = False
        self.artifact.generate_workfile()

        work_file = os.path.basename(self.artifact.work_filename())
        artifact_file = os.path.basename(self.artifact.filename())
        command = "%s %s %s" % (self.EXECUTABLE, work_file, artifact_file)
        self.log.info(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)
        self.artifact.data_dict['1'] = open(self.artifact.filename(), "r").read()

### @export "pdf2png"
class Pdf2Png(DexyHandler):
    INPUT_EXTENSIONS = ['.pdf']
    OUTPUT_EXTENSIONS = ['.png']
    ALIASES = ['pdf2png']

    def generate(self):
        self.artifact.write_dj()

    def process(self):
        # Can't use generate_workfile as input is binary, not text-based.
        # TODO should we be doing this in general rather than generating workfiles?
        wf = self.artifact.previous_artifact_filename
        of = self.artifact.filename(False)
        command = "/usr/bin/env gs -dSAFER -dNOPAUSE -dBATCH -sDEVICE=png16m -sOutputFile=%s ../%s" % (of, wf)
        self.log.debug(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

### @export "ps2pdf"
class Ps2Pdf(DexyHandler):
    INPUT_EXTENSIONS = [".ps", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['ps2pdf']

    def generate(self):
        self.artifact.write_dj()
    
    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename(False)
        of = self.artifact.filename(False)
        command = "/usr/bin/env ps2pdf %s %s" % (wf, of)
        self.log.debug(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

### @export "latex"
class LatexHandler(DexyHandler):
    INPUT_EXTENSIONS = [".tex", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf", ".png"]
    ALIASES = ['latex']
    
    def generate(self):
        self.artifact.write_dj()

    def process(self):
        latex_filename = self.artifact.filename().replace(".pdf", ".tex")
        latex_basename = os.path.basename(latex_filename)
        
        f = open(latex_filename, "w")
        f.write(self.artifact.input_text())
        f.close()
        
        # Detect which LaTeX compiler we have...
        latex_bin = None
        for e in ["pdflatex", "latex"]:
            which_cmd = "/usr/bin/env which %s" % e
            latex_bin, s = pexpect.run(which_cmd, withexitstatus = True) 
            if s == 0:
                self.log.info("%s LaTeX command found" % e)
                break
            else:
                self.log.info("%s LaTeX command not found" % e)
                latex_bin = None
        
        if not latex_bin:
            raise Exception("no executable found for latex")

        command = "/usr/bin/env %s %s" % (e, latex_basename)
        self.log.info(command)
        # run LaTeX twice so TOCs, section number references etc. are correct
        ad = self.artifact.artifacts_dir
        self.artifact.stdout = pexpect.run(command, cwd=ad, timeout=20)
        self.artifact.stdout += pexpect.run(command, cwd=ad, timeout=20)

### @export "voice"
class VoiceHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".mp3"]
    ALIASES = ['voice', 'say']
     
    def process(self):
        self.artifact.auto_write_artifact = False
        self.artifact.generate_workfile()
        work_file = os.path.basename(self.artifact.work_filename())
        artifact_file = os.path.basename(self.artifact.filename())

        for e, ext in {"say" : "aiff", "espeak" : "wav"}.items():
            sound_file = artifact_file.replace('mp3', ext)
            tts_bin, s = pexpect.run("/usr/bin/env which %s" % e, withexitstatus = True)
            if s == 0:
                self.log.info("%s text-to-speech found at %s" % (e, tts_bin))
                break
            else:
                self.log.info("%s text-to-speech not found" % e)
                e = None
        
        if e == "say":
            command = "/usr/bin/env say -f %s -o %s" % (work_file, sound_file)
        elif e == "espeak":
            command = "/usr/bin/env espeak -f %s -w %s" % (work_file, sound_file)
        else:
            raise Exception("unknown text-to-speech command %s" % e)

        self.log.info(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

        # Converting to mp3
        command = "/usr/bin/env lame %s %s" % (sound_file, artifact_file)
        self.log.info(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

### @export "ragelruby"
class RagelRubyHandler(DexyHandler):
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".rb"]
    ALIASES = ['rlrb', 'ragelruby']
    
    def process(self):
        self.artifact.auto_write_artifact = False
        self.artifact.generate_workfile()
        artifact_file = self.artifact.filename(False)
        work_file = self.artifact.work_filename(False)
        command = "/usr/bin/env ragel -R -o %s %s" % (artifact_file, work_file)
        self.log.info(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)
        self.artifact.data_dict['1'] = open(self.artifact.filename(), "r").read()

### @export "ragelrubydot"
class RagelRubyDotHandler(DexyHandler):
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".dot"]
    ALIASES = ['rlrbd', 'ragelrubydot']
    
    def process(self):
        self.artifact.generate_workfile()
        work_file = os.path.basename(self.artifact.work_filename())
        command = "/usr/bin/env ragel -R -V %s" % (work_file)
        self.log.info(command)
        ad = self.artifact.artifacts_dir
        self.artifact.data_dict['1'] = pexpect.run(command, cwd=ad)

### @export "dot"
class DotHandler(DexyHandler):
    INPUT_EXTENSIONS = [".dot"]
    OUTPUT_EXTENSIONS = [".png", ".pdf"]
    ALIASES = ['dot', 'graphviz']
    
    def process(self):
        self.artifact.auto_write_artifact = False
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename(False)
        af = self.artifact.filename(False)
        ex = self.artifact.ext.replace(".", "")
        command = "/usr/bin/env dot -T%s -o%s %s" % (ex, af, wf)
        self.log.info(command)
        ad = self.artifact.artifacts_dir
        self.artifact.stdout = pexpect.run(command, cwd=ad)

### @export "rb"
class RubyStdoutHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env ruby'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rb']


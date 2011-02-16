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
    as input. Sends input line-by-line.
    """
    EXECUTABLE = '/usr/bin/env python'
    PROMPT = '>>>|\.\.\.' # Python uses >>> prompt normally and ... when in multi-line structures like loops
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".pycon"]
    ALIASES = ['pycon']

    def process_dict(self, input_dict):
        output_dict = OrderedDict()
        if self.artifact.doc.args.has_key('timeout'):
            timeout = self.artifact.doc.args['timeout']
            self.log.info("using custom timeout %s for %s" % (timeout, self.artifact.key))
        else:
            timeout = None
        if self.artifact.doc.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.doc.args['env'])
            self.log.info("adding to env: %s" % self.artifact.doc.args['env'])
        else:
            env = None

        proc = pexpect.spawn(self.EXECUTABLE, cwd=self.artifact.artifacts_dir, env=env)
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
                proc.expect(self.PROMPT, timeout=timeout)
                section_transcript += proc.before
                start = proc.after
            output_dict[k] = section_transcript
        return output_dict

### @export "sectionwise"
class ProcessSectionwiseInteractiveHandler(DexyHandler):
    """
    Intended for use with interactive processes, such as R interpreter,
    where your goal is to have a session transcript divided into same sections
    as input. Sends input section-by-section.
    """
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

        if self.artifact.doc.args.has_key('timeout'):
            timeout = self.artifact.doc.args['timeout']
            self.log.info("using custom timeout %s for %s" % (timeout, self.artifact.key))
        else:
            timeout = None
        if self.artifact.doc.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.doc.args['env'])
            self.log.info("adding to env: %s" % self.artifact.doc.args['env'])
        else:
            env = None
 
        proc = pexpect.spawn(self.EXECUTABLE, 
                             cwd=self.artifact.artifacts_dir, 
                             env=env)
        proc.expect(self.PROMPT)
        start = (proc.before + proc.after)
        
        for k, s in input_dict.items():
            section_transcript = start
            start = ""
            proc.send(s)
            proc.sendline(self.COMMENT * 5)

            proc.expect(self.COMMENT * 5, timeout = timeout)

            section_transcript += proc.before.rstrip(self.TRAILING_PROMPT)
            output_dict[k] = section_transcript

        return output_dict

### @export "clojure"
class ClojureInteractiveHandler(ProcessLinewiseInteractiveHandler):
    """
    Runs clojure.
    """
    EXECUTABLE = 'java clojure.main'
    INPUT_EXTENSIONS = [".clj"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['clj', 'cljint']
    PROMPT = "user=> "

### @export "lua"
# TODO Add support for lua-style comments to idiopidae fork
class LuaHandler(ProcessSectionwiseInteractiveHandler):
    """
    Runs lua.
    """
    EXECUTABLE = '/usr/bin/env lua'
    VERSION = '/usr/bin/env lua -v'
    INPUT_EXTENSIONS = ['.lua', '.txt']
    OUTPUT_EXTENSIONS = ['.txt']
    ALIASES = ['lua']
    PROMPT = '>'
    TRAILING_PROMPT = '>>'

### @export "timing"
class ProcessTimingHandler(DexyHandler):
    """
    Runs python code N times and reports timings.
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
    """Runs R code in batch mode. Returns a full transcript, including commands and output from each line."""
    EXECUTABLE = '/usr/bin/env R CMD BATCH --vanilla --quiet --no-timing'
    VERSION = "/usr/bin/env R --version"
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".Rout"]
    ALIASES = ['r']

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
    """Runs R code in batch mode. Uses the --slave flag so doesn't echo commands, just returns output."""
    EXECUTABLE = '/usr/bin/env R CMD BATCH --vanilla --quiet --slave --no-timing'
    VERSION = "/usr/bin/env R --version"
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
    """
    Converts a PDF file to PNG format.
    """
    INPUT_EXTENSIONS = ['.pdf']
    OUTPUT_EXTENSIONS = ['.png']
    ALIASES = ['pdf2png']
    EXECUTABLE = "/usr/bin/env gs"
    VERSION = "/usr/bin/env gs --version"

    def generate(self):
        self.artifact.write_dj()

    def process(self):
        # Can't use generate_workfile as input is binary, not text-based.
        # TODO should we be doing this in general rather than generating workfiles?
        wf = self.artifact.previous_artifact_filename
        of = self.artifact.filename(False)
        command = "%s -dSAFER -dNOPAUSE -dBATCH -sDEVICE=png16m -sOutputFile=%s ../%s" % (self.executable(), of, wf)
        self.log.debug(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

### @export "ps2pdf"
class Ps2Pdf(DexyHandler):
    """
    Converts a PS file to PDF format.
    """
    INPUT_EXTENSIONS = [".ps", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['ps2pdf']
    EXECUTABLE = '/usr/bin/env ps2pdf'

    def generate(self):
        self.artifact.write_dj()
    
    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename(False)
        of = self.artifact.filename(False)
        command = "%s %s %s" % (self.executable(), wf, of)
        self.log.debug(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

### @export "latex"
class LatexHandler(DexyHandler):
    """
    Generates a PDF file from LaTeX source.
    """
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
    """
    Use text-to-speech to generate mp3 file from a text file. Uses whichever of
    say, aiff, espeak, wav tools is found, then lame to convert to mp3.
    """
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
    """
    Runs ragel for ruby.
    """
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".rb"]
    ALIASES = ['rlrb', 'ragelruby']
    VERSION = '/usr/bin/env ragel --version'
    EXECUTABLE = '/usr/bin/env ragel -R'
    
    def process(self):
        self.artifact.auto_write_artifact = False
        self.artifact.generate_workfile()
        artifact_file = self.artifact.filename(False)
        work_file = self.artifact.work_filename(False)
        command = "%s -o %s %s" % (self.executable(), artifact_file, work_file)
        self.log.info(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)
        self.artifact.data_dict['1'] = open(self.artifact.filename(), "r").read()

### @export "ragelrubydot"
class RagelRubyDotHandler(DexyHandler):
    """
    Generates state chart in .dot format of ragel state machine for ruby.
    """
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".dot"]
    ALIASES = ['rlrbd', 'ragelrubydot']
    VERSION = '/usr/bin/env ragel --version'
    EXECUTABLE = '/usr/bin/env ragel -R'
    
    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename(False)
        command = "%s -V %s" % (self.executable(), wf)
        self.log.info(command)
        ad = self.artifact.artifacts_dir
        self.artifact.data_dict['1'] = pexpect.run(command, cwd=ad)

### @export "dot"
class DotHandler(DexyHandler):
    """
    Renders .dot files to either PNG or PDF images.
    """
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


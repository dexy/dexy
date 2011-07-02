from dexy.dexy_filter import DexyFilter
from ordereddict import OrderedDict
import os
import pexpect
import re
import time

class ProcessLinewiseInteractiveHandler(DexyFilter):
    """
    Intended for use with interactive processes, such as python interpreter,
    where your goal is to have a session transcript divided into same sections
    as input. Sends input line-by-line.
    """
    EXECUTABLE = 'python'
    PROMPT = '>>>|\.\.\.' # Python uses >>> prompt normally and ... when in multi-line structures like loops
    TRIM_PROMPT = '>>>'
    LINE_ENDING = "\r\n"
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".pycon"]
    ALIASES = ['pycon']
    IGNORE_ERRORS = False # Allow overriding default per-handler.

    def process_dict(self, input_dict):
        output_dict = OrderedDict()
        if self.artifact.args.has_key('timeout'):
            timeout = self.artifact.args['timeout']
            self.log.info("using custom timeout %s for %s" % (timeout, self.artifact.key))
        else:
            timeout = None
        if self.artifact.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.args['env'])
            self.log.info("adding to env: %s" % self.artifact.args['env'])
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
                proc.expect("%s(%s)" % (self.LINE_ENDING, self.PROMPT), timeout=timeout)
                section_transcript += proc.before
                start = proc.after
            lines = section_transcript.split(self.LINE_ENDING)
            # Strip blank lines/trailing prompts at end of section
            while re.match("^\s*(%s)\s*$|^\s*$" % self.TRIM_PROMPT, lines[-1]):
                lines = lines[0:-1]
            output_dict[k] = self.LINE_ENDING.join(lines)
        try:
            proc.close()
        except pexpect.ExceptionPexpect:
            print "process %s may not have closed" % proc.pid

        if proc.exitstatus is not None and proc.exitstatus != 0:
            if not (self.IGNORE_ERRORS or self.artifact.args.ignore_errors):
                raise Exception("""proc returned nonzero status code! if you don't
want dexy to raise errors on failed scripts then pass the --ignore-errors option""")
        return output_dict

class RLinewiseInteractiveHandler(ProcessLinewiseInteractiveHandler):
    """
    Runs R
    """
    EXECUTABLE = "R --quiet --vanilla"
    VERSION = "R --version"
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = ['.Rout']
    PROMPT = ">|\+"
    ALIASES = ['r', 'rint']

class ClojureInteractiveHandler(ProcessLinewiseInteractiveHandler):
    """
    Runs clojure.
    """
    EXECUTABLE = None
    EXECUTABLES = ['clojure', 'clj -r', 'java clojure.main']
    INPUT_EXTENSIONS = [".clj"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['clj', 'cljint']
    PROMPT = "user=> "

class ProcessTimingHandler(DexyFilter):
    """
    Runs python code N times and reports timings.
    """
    EXECUTABLE = 'python'
    VERSION = 'python --version'
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

class Pdf2Jpg(DexyFilter):
    """
    Converts a PDF file to JPEG format.
    """
    INPUT_EXTENSIONS = ['.pdf']
    OUTPUT_EXTENSIONS = ['.jpg']
    ALIASES = ['pdf2jpg', 'pdf2jpeg']
    EXECUTABLE = "gs"
    VERSION = "gs --version"
    BINARY = True

    def process(self):
        # Can't use generate_workfile as input is binary, not text-based.
        # TODO should we be doing this in general rather than generating workfiles?
        wf = self.artifact.previous_artifact_filename
        of = self.artifact.filename()
        command = "%s -dSAFER -dNOPAUSE -dBATCH -sDEVICE=jpeg -sOutputFile=%s ../%s" % (self.executable(), of, wf)
        self.log.debug(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

class Pdf2Png(DexyFilter):
    """
    Converts a PDF file to PNG format.
    """
    INPUT_EXTENSIONS = ['.pdf']
    OUTPUT_EXTENSIONS = ['.png']
    ALIASES = ['pdf2png']
    EXECUTABLE = "gs"
    VERSION = "gs --version"
    BINARY = True

    def process(self):
        # Can't use generate_workfile as input is binary, not text-based.
        # TODO should we be doing this in general rather than generating workfiles?
        wf = self.artifact.previous_artifact_filename
        of = self.artifact.filename()
        command = "%s -dSAFER -dNOPAUSE -dBATCH -sDEVICE=png16m -r300 -sOutputFile=%s %s" % (self.executable(), of, wf)
        self.log.debug(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

class Ps2Pdf(DexyFilter):
    """
    Converts a PS file to PDF format.
    """
    INPUT_EXTENSIONS = [".ps", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['ps2pdf']
    EXECUTABLE = 'ps2pdf'
    BINARY = True

    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename()
        of = self.artifact.filename()
        command = "%s %s %s" % (self.executable(), wf, of)
        self.log.debug(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

class VoiceHandler(DexyFilter):
    """
    Use text-to-speech to generate mp3 file from a text file. Uses whichever of
    say, aiff, espeak, wav tools is found, then lame to convert to mp3.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".mp3"]
    ALIASES = ['voice', 'say']

    def process(self):
        self.artifact.generate_workfile()
        work_file = os.path.basename(self.artifact.work_filename())
        artifact_file = os.path.basename(self.artifact.filename())

        for e, ext in {"say" : "aiff", "espeak" : "wav"}.items():
            sound_file = artifact_file.replace('mp3', ext)
            # TODO replace pexpect with subprocess
            tts_bin, s = pexpect.run("which %s" % e, withexitstatus = True)
            if s == 0:
                self.log.info("%s text-to-speech found at %s" % (e, tts_bin))
                break
            else:
                self.log.info("%s text-to-speech not found" % e)
                e = None

        if e == "say":
            command = "say -f %s -o %s" % (work_file, sound_file)
        elif e == "espeak":
            command = "espeak -f %s -w %s" % (work_file, sound_file)
        else:
            raise Exception("unknown text-to-speech command %s" % e)

        self.log.info(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

        # Converting to mp3
        command = "lame %s %s" % (sound_file, artifact_file)
        self.log.info(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)

class RagelRubyHandler(DexyFilter):
    """
    Runs ragel for ruby.
    """
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".rb"]
    ALIASES = ['rlrb', 'ragelruby']
    VERSION = 'ragel --version'
    EXECUTABLE = 'ragel -R'

    def process(self):
        self.artifact.generate_workfile()
        artifact_file = self.artifact.filename(False)
        work_file = self.artifact.work_filename(False)
        command = "%s -o %s %s" % (self.executable(), artifact_file, work_file)
        self.log.info(command)
        self.artifact.stdout = pexpect.run(command, cwd=self.artifact.artifacts_dir)
        self.artifact.data_dict['1'] = open(self.artifact.filename(), "r").read()

class RagelRubyDotHandler(DexyFilter):
    """
    Generates state chart in .dot format of ragel state machine for ruby.
    """
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".dot"]
    ALIASES = ['rlrbd', 'ragelrubydot']
    VERSION = 'ragel --version'
    EXECUTABLE = 'ragel -R'

    def process(self):
        self.artifact.generate_workfile()
        wf = self.artifact.work_filename(False)
        command = "%s -V %s" % (self.executable(), wf)
        self.log.info(command)
        ad = self.artifact.artifacts_dir
        self.artifact.data_dict['1'] = pexpect.run(command, cwd=ad)


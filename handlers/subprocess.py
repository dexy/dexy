from dexy.handler import DexyHandler
import os
import pexpect
import time
import re

class ProcessInteractiveHandler(DexyHandler):
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

    def process(self):
        proc = pexpect.spawn(self.EXECUTABLE, cwd="artifacts")
        proc.expect(self.PROMPT)
        start = (proc.before + proc.after)

        for k, s in self.artifact.input_data_dict.items():
            section_transcript = start
            start = ""
            for l in s.rstrip().split("\n"):
                section_transcript += start
                start = ""
                proc.sendline(l)
                proc.expect(self.PROMPT, timeout=30)
                section_transcript += proc.before
                start = proc.after
            self.artifact.data_dict[k] = section_transcript

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
        self.artifact.data_dict['1'] = pexpect.run("%s %s" % (self.EXECUTABLE, self.artifact.work_filename()))

class RedclothHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env redcloth'
    INPUT_EXTENSIONS = [".txt", ".textile"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['redcloth', 'textile']

class SloccountHandler(DexyHandler):
    EXECUTABLE = '/usr/bin/env sloccount'
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['sloc', 'sloccount']
    
    def process(self):
        self.artifact.generate_workfile()
        self.artifact.data_dict['1'] = pexpect.run("%s %s" % (self.EXECUTABLE, self.artifact.work_filename()))


class ProcessArtifactHandler(DexyHandler):
    """
    Intended for use with command line processes where the process will write
    data directly to the artifact file which is passed as an argument.
    """
    EXECUTABLE = '/usr/bin/env python'
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['pyart']

    def process(self):
        self.artifact.auto_write_artifact = False
        wf = self.artifact.work_filename()
        af = self.artifact.filename()
        self.artifact.stdout = pexpect.run("%s %s %s" % (self.EXECUTABLE, af, wf))

class ProcessTimingHandler(DexyHandler):
    """
    Runs code N times and reports timings.
    """
    EXECUTABLE = '/usr/bin/env python'
    N = 10
    INPUT_EXTENSIONS = [".txt", ".py"]
    OUTPUT_EXTENSIONS = [".times"]
    ALIASES = ['pytime']
    
    def process(self):
        self.artifact.generate_workfile()
        times = []
        for i in xrange(self.N):
            start = time.time()
            pexpect.run("%s %s" % (self.EXECUTABLE, self.artifact.work_filename()))
            times.append("%s" % (time.time() - start))
        self.artifact.data_dict['1'] = "\n".join(times)

class RInteractiveHandler(ProcessInteractiveHandler):
    """
    Note this produces output files with ASCII formatting codes.
    """
    EXECUTABLE = '/usr/bin/env R --vanilla --quiet'
    PROMPT = '>|\+'
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".Rout"]
    ALIASES = ['rint']

class ROutputHandler(DexyHandler):
    EXECUTABLE = '/usr/bin/env R CMD BATCH --vanilla --quiet --no-timing'
    INPUT_EXTENSIONS = ['.txt', '.r', '.R']
    OUTPUT_EXTENSIONS = [".Rout"]
    ALIASES = ['r', 'R']

    def generate(self):
        self.artifact.write_dj()

    def process(self):
        self.artifact.generate_workfile()
        pexpect.run("%s %s %s" % (self.EXECUTABLE, self.artifact.work_filename(), self.artifact.filename()))
        self.artifact.data_dict['1'] = open(self.artifact.filename(), "r").read()

class RArtifactHandler(DexyHandler):
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
        print command
        self.artifact.stdout = pexpect.run(command, cwd='artifacts')
        self.artifact.data_dict['1'] = open(self.artifact.filename(), "r").read()

class LatexHandler(DexyHandler):
    INPUT_EXTENSIONS = [".tex", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf", ".png"]
    ALIASES = ['latex', 'tex']
    
    def generate(self):
        self.artifact.write_dj()

    def process(self):
        latex_filename = self.artifact.filename().replace(".pdf", ".tex")
        latex_basename = os.path.basename(latex_filename)
        pdf_basename = os.path.basename(self.artifact.filename())
        
        has_header = re.search("documentclass", self.artifact.input_text())

        f = open(latex_filename, "w")
        if not has_header:
            f.write(open("assets/latex-template.txt", "r").read())
        f.write(self.artifact.input_text())
        if not has_header:
            f.write('\n\end{document}')
        f.close()

        command = "/usr/bin/env pdflatex %s" % latex_basename
        print command
        self.artifact.stdout = pexpect.run(command, cwd="artifacts", timeout=20)

class VoiceHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".mp3"]
    ALIASES = ['voice', 'say']
     
    def process(self):
        self.artifact.auto_write_artifact = False
        self.artifact.generate_workfile()
        work_file = os.path.basename(self.artifact.work_filename())
        artifact_file = os.path.basename(self.artifact.filename())
        aiff_file = artifact_file.replace("mp3", "aiff")
        command = "/usr/bin/env say -f %s -o %s" % (work_file, aiff_file)
        print command
        self.artifact.stdout = pexpect.run(command, cwd='artifacts')
        command = "/usr/bin/env lame %s %s" % (aiff_file, artifact_file)
        print command
        self.artifact.stdout = pexpect.run(command, cwd='artifacts')


class RagelRubyHandler(DexyHandler):
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".rb"]
    ALIASES = ['rlrb', 'ragelruby']
    
    def process(self):
        self.artifact.auto_write_artifact = False

        self.artifact.generate_workfile()
        wf = self.artifact.work_filename()
        af = self.artifact.filename()
        command = "/usr/bin/env ragel -R -o %s %s" % (af, wf)
        self.artifact.stdout = pexpect.run(command)


class RagelRubyDotHandler(DexyHandler):
    INPUT_EXTENSIONS = [".rl"]
    OUTPUT_EXTENSIONS = [".dot"]
    ALIASES = ['rlrbd', 'ragelrubydot']
    
    def process(self):
        self.auto_write_artifact = False

        self.artifact.generate_workfile()
        wf = self.artifact.work_filename()
        af = self.artifact.filename()
        command = "/usr/bin/env ragel -R -V -o %s %s" % (af, wf)
        self.artifact.stdout = pexpect.run(command)


class DotHandler(DexyHandler):
    INPUT_EXTENSIONS = [".dot"]
    OUTPUT_EXTENSIONS = [".png", ".pdf"]
    ALIASES = ['dot', 'graphviz']
    
    def process(self):
        self.artifact.auto_write_artifact = False

        self.artifact.generate_workfile()
        wf = self.artifact.work_filename(False)
        af = self.artifact.filename(False)
        command = "/usr/bin/env dot -T%s -o%s %s" % (self.artifact.ext.replace(".", ""), af, wf)
        print command
        self.artifact.data_dict['1'] = pexpect.run(command, cwd="artifacts")


class RubyStdoutHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env ruby'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = []


class RubyInteractiveHandler(DexyHandler):
    EXECUTABLE = '/usr/bin/env ruby'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['rb', 'ruby', 'rbout']

    def process(self):
        self.artifact.generate_workfile()
        input_filename = self.artifact.temp_filename(".txt")

        input_file = open(input_filename, "w")
        input_file.write(self.artifact.input_text())
        input_file.close()

        command = "/usr/bin/env ruby -r %s %s" % (self.artifact.work_filename(), input_filename)
        self.artifact.data_dict['1'] = pexpect.run(command)

class RspecHandler(ProcessStdoutHandler):
    EXECUTABLE = '/usr/bin/env spec -f s'
    INPUT_EXTENSIONS = [".txt", ".rb"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['spec', 'rspec']

    def process(self):
        self.artifact.auto_write_artifact = False
        self.artifact.generate_workfile()
        self.artifact.data_dict['1'] = pexpect.run("%s %s" % (self.EXECUTABLE, self.artifact.work_filename(False)), cwd="artifacts")

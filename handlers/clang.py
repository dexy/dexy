from dexy.handler import DexyHandler
import pexpect
import time

### @export "clang-handler"
class ClangHandler(DexyHandler):
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['c', 'clang']
    
    def process(self):
        self.artifact.generate_workfile()
        o_filename = self.artifact.temp_filename(".o")
        command = "/usr/bin/env clang %s -o %s" % (self.artifact.work_filename(), o_filename)
        self.log.debug("running command:\n%s" % command)
        output = pexpect.run(command)
        self.artifact.stdout = output
        self.log.debug("output:\n%s" % output)
        
        command = "%s > %s" % (o_filename, self.artifact.filename)
        self.artifact.data_dict['1'] = pexpect.run(command)

### @export "clang-interactive-handler"
class ClangInteractiveHandler(DexyHandler):
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['cint']
    
    def process(self):
        self.artifact.generate_workfile()
        o_filename = self.artifact.filename().replace(".txt", ".o")
        command = "/usr/bin/env clang %s -o %s" % (self.artifact.work_filename(), o_filename)
        output = pexpect.run(command)
        self.artifact.stdout = output
        self.log.debug("output:\n%s" % output)
        
        self.artifact.load_input_artifacts()
        for k, v in self.artifact.input_artifacts_dict.items():
            for s, t in v['data_dict'].items():
                proc = pexpect.spawn(o_filename)
                proc.send(t) # TODO alternatively write to a file and use pexpect.run
                proc.sendcontrol('d') # eof
                self.artifact.data_dict[s] = proc.read()

class ClangTimingHandler(DexyHandler):
    """
    Runs code N times and reports graphs timings.
    """
    N = 10
    INPUT_EXTENSIONS = [".txt", ".c"]
    OUTPUT_EXTENSIONS = [".times"]
    ALIASES = ['ctime']
    
    def process(self):
        # Compile code first
        self.artifact.generate_workfile()
        o_filename = self.artifact.temp_filename(".o")
        command = "/usr/bin/env clang %s -o %s" % (self.artifact.work_filename(), o_filename)
        print command
        output = pexpect.run(command)
        print output # output of clang interpreter, save somewhere?

        command = "%s > %s" % (o_filename, self.artifact.filename)
        times = []
        for i in xrange(self.N):
            start = time.time()
            pexpect.run(command)
            times.append("%s" % (time.time() - start))
        self.artifact.data_dict['1'] = "\n".join(times)

class ClangTimingInteractiveHandler(DexyHandler):
    """
    Runs code N times and reports graphs timings.
    """
    N = 10
    INPUT_EXTENSIONS = [".txt", ".c"]
    OUTPUT_EXTENSIONS = [".times"]
    ALIASES = ['ctimeint']
    
    def process(self):
        # Compile code first
        self.artifact.generate_workfile()
        o_filename = self.artifact.temp_filename(".o")
        command = "/usr/bin/env clang %s -o %s" % (self.artifact.work_filename(), o_filename)
        print command
        output = pexpect.run(command)
        print output # output of clang interpreter, save somewhere?

        command = "%s > %s" % (o_filename, self.artifact.filename)
        times = []
        for i in xrange(self.N):
            self.artifact.load_input_artifacts()
            for k, v in self.artifact.input_artifacts_dict.items():
                for s, t in v['data_dict'].items():
                    start = time.time()
                    proc = pexpect.spawn(o_filename)
                    proc.send(t) # TODO alternatively write to a file and use pexpect.run
                    proc.sendcontrol('d') # eof
                    proc.wait()
                    times.append("%s" % (time.time() - start))
        self.artifact.data_dict['1'] = "\n".join(times)

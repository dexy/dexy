from dexy.handler import DexyHandler
import pexpect
import time

class AsciidocHandler(DexyHandler):
    VERSION = "/usr/bin/env asciidoc --version"
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".html", ".xml"]
    ALIASES = ['asciidoc']

    def process(self):
        self.artifact.generate_workfile()
        workfile = self.artifact.work_filename(False)
        outfile = self.artifact.filename(False)
        
        extension = self.artifact.ext

        if extension == ".html":
            backend = "html"
        elif extension == ".xml":
            backend = "docbook"
        else:
            raise Exception("unexpected file extension in asciidoc handler %s" % extension)
        
        command = "/usr/bin/env asciidoc -b %s -o %s %s" % (backend, outfile, workfile)
        self.log.debug(command)
        output = pexpect.run(command, cwd=self.artifact.artifacts_dir)
        self.artifact.stdout = output
        self.log.debug("\n%s" % output)
        
        f = open(self.artifact.filename(), "r")
        self.artifact.data_dict['1'] = f.read()
        f.close()



### @export "cpp-handler"
class CppHandler(DexyHandler):
    VERSION = "/usr/bin/env c++ --version"
    INPUT_EXTENSIONS = [".cpp"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['cpp']
    
    def process(self):
        self.artifact.generate_workfile()
        o_filename = self.artifact.temp_filename(".o")
        command = "/usr/bin/env c++ %s -o %s" % (self.artifact.work_filename(), o_filename)
        self.log.debug(command)
        output = pexpect.run(command)
        self.artifact.stdout = output
        self.log.debug("\n%s" % output)
        
        command = "%s > %s" % (o_filename, self.artifact.filename)
        self.artifact.data_dict['1'] = pexpect.run(command)

### @export "clang-handler"
class ClangHandler(DexyHandler):
    VERSION = "/usr/bin/env clang --version"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['c', 'clang']
    
    def process(self):
        self.artifact.generate_workfile()
        o_filename = self.artifact.temp_filename(".o")
        command = "/usr/bin/env clang %s -o %s" % (self.artifact.work_filename(), o_filename)
        self.log.debug(command)
        output = pexpect.run(command)
        self.artifact.stdout = output
        self.log.debug("\n%s" % output)
        
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
        self.log.debug("\n%s" % output)
        
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
        self.log.debug(command)
        output = pexpect.run(command)
        self.artifact.stdout = output
        self.log.debug("\n%s" % output)

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

from dexy.handler import DexyHandler
import pexpect # TODO replace pexpect with subprocess where possible
import time

### @export "cpp-handler"
class CppHandler(DexyHandler):
    """Compiles and then runs C++ code."""
    VERSION = "/usr/bin/env c++ --version"
    EXECUTABLE ="/usr/bin/env c++"
    INPUT_EXTENSIONS = [".cpp"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['cpp']
    
    def process(self):
        self.artifact.generate_workfile()
        of = self.artifact.temp_filename(".o")
        wf = self.artifact.work_filename()
        command = "%s %s -o %s" % (self.EXECUTABLE, wf, of)
        self.log.debug(command)
        output = pexpect.run(command)
        self.artifact.stdout = output
        self.log.debug("\n%s" % output)
        
        command = "%s > %s" % (of, self.artifact.filename)
        self.artifact.data_dict['1'] = pexpect.run(command)

### @export "clang-handler"
class CHandler(DexyHandler):
    """Compiles C code using gcc compiler, then runs compiled program."""
    VERSION = "/usr/bin/env gcc --version"
    EXECUTABLE = "/usr/bin/env gcc"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['c', 'gcc']
    
    def process(self):
        self.artifact.generate_workfile()
        of = self.artifact.temp_filename(".o")
        wf = self.artifact.work_filename()
        command = "%s %s -o %s" % (self.EXECUTABLE, wf, of)
        self.log.debug(command)
        output = pexpect.run(command)
        self.artifact.stdout = output
        self.log.debug("\n%s" % output)
        
        command = "%s > %s" % (of, self.artifact.filename)
        self.artifact.data_dict['1'] = pexpect.run(command)

### @export "clang-handler"
class ClangHandler(DexyHandler):
    """Compiles C code using clang compiler, then runs compiled program."""
    VERSION = "/usr/bin/env clang --version"
    EXECUTABLE = "/usr/bin/env clang"
    INPUT_EXTENSIONS = [".c"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['clang']
    
    def process(self):
        self.artifact.generate_workfile()
        of = self.artifact.temp_filename(".o")
        wf = self.artifact.work_filename()
        command = "%s %s -o %s" % (self.EXECUTABLE, wf, of)
        self.log.debug(command)
        output = pexpect.run(command)
        self.artifact.stdout = output
        self.log.debug("\n%s" % output)
        
        command = "%s > %s" % (of, self.artifact.filename)
        self.artifact.data_dict['1'] = pexpect.run(command)

### @export "clang-interactive-handler"
class ClangInteractiveHandler(DexyHandler):
    """Compiles C code using clang compiler, then runs compiled program, reading
    input from any input files."""
    VERSION = "/usr/bin/env clang --version"
    EXECUTABLE = "/usr/bin/env clang"
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
                proc.sendcontrol('d')
                output = proc.read()
                # Strip off what the EOT gets mangled to...
                self.artifact.data_dict[s] = output.rstrip("^D\x08\x08")

### @export "clang-timing-handler"
class ClangTimingHandler(DexyHandler):
    """Compiles C code using clang compiler, then runs compiled program N times
    reporting timings."""
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

### @export "clang-timing-interactive-handler"
class ClangTimingInteractiveHandler(DexyHandler):
    """Compiles C code using clang compiler, then runs compiled program, reading
    input from any input files. Program run N times reporting timings."""
    N = 10
    INPUT_EXTENSIONS = [".txt", ".c"]
    OUTPUT_EXTENSIONS = [".times"]
    ALIASES = ['ctimeint']
    
    def process(self):
        # Compile code first
        self.artifact.generate_workfile()
        o_filename = self.artifact.temp_filename(".o")
        command = "/usr/bin/env clang %s -o %s" % (self.artifact.work_filename(), o_filename)
        self.log.debug(command)
        output = pexpect.run(command)
        self.log.debug("\n%s" % output)
        self.artifact.stdout = output

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

from dexy.handler import DexyHandler
import pexpect

class AsciidocHandler(DexyHandler):
    """IN DEVELOPMENT. Converts .txt files with asciidoc markup to HTML or
    XML."""
    VERSION = "/usr/bin/env asciidoc --version"
    EXECUTABLE = "/usr/bin/env asciidoc -b"
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
        
        command = "%s %s -o %s %s" % (self.EXECUTABLE, backend, outfile, workfile)
        self.log.debug(command)
        output = pexpect.run(command, cwd=self.artifact.artifacts_dir)
        self.artifact.stdout = output
        self.log.debug("\n%s" % output)
        
        f = open(self.artifact.filename(), "r")
        self.artifact.data_dict['1'] = f.read()
        f.close()

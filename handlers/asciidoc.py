from dexy.handler import DexyHandler
import pexpect

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

from dexy.handler import DexyHandler
import os
import subprocess

class AsciidocHandler(DexyHandler):
    """IN DEVELOPMENT. Converts .txt files with asciidoc markup to HTML or
    XML."""
    VERSION = "/usr/bin/env asciidoc --version"
    EXECUTABLE = "/usr/bin/env asciidoc -b"
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".html", ".xml"]
    ALIASES = ['asciidoc']
    FINAL = True

    def process(self):
        self.artifact.generate_workfile()
        workfile = self.artifact.work_filename()
        outfile = self.artifact.filename()

        extension = self.artifact.ext

        if extension == ".html":
            backend = "html"
        elif extension == ".xml":
            backend = "docbook"
        else:
            raise Exception("unexpected file extension in asciidoc handler %s" % extension)

        command = "%s %s -o %s %s" % (self.EXECUTABLE, backend, outfile, workfile)
        self.log.debug(command)

        if self.doc.args.has_key('env'):
            env = os.environ
            env.update(self.doc.args['env'])
        else:
            env = None

        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout

        f = open(self.artifact.filepath(), "r")
        self.artifact.data_dict['1'] = f.read()
        f.close()

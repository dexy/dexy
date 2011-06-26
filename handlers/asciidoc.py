from dexy.dexy_filter import DexyFilter
import os
import subprocess

class AsciidocHandler(DexyFilter):
    """IN DEVELOPMENT. Converts .txt files with asciidoc markup to HTML or
    XML."""
    VERSION = "asciidoc --version"
    EXECUTABLE = "asciidoc"
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
            # TODO check here if we are on asciidoc 8.6.5,
            # any lower will throw an error if we try to use html5
            backend = "html5"
        elif extension == ".xml":
            backend = "docbook45"
        else:
            raise Exception("unexpected file extension in asciidoc handler %s" % extension)

        command = "%s -b %s -d book -o %s %s" % (self.EXECUTABLE, backend, outfile, workfile)
        self.log.debug(command)

        if self.artifact.args.has_key('env'):
            env = os.environ
            env.update(self.artifact.args['env'])
        else:
            env = None

        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout

        self.handle_subprocess_proc_return(proc.returncode, stderr)


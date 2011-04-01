from dexy.handler import DexyHandler
import os
import subprocess

class LatexHandler(DexyHandler):
    """
    Generates a PDF file from LaTeX source.
    """
    INPUT_EXTENSIONS = [".tex", ".txt"]
    OUTPUT_EXTENSIONS = [".pdf", ".png"]
    ALIASES = ['latex']
    BINARY = True
    FINAL = True

    def process(self):
        latex_filename = self.artifact.filename().replace(".pdf", ".tex")
        self.artifact.generate_workfile(latex_filename)

        if self.doc.args.has_key('env'):
            env = os.environ
            env.update(self.doc.args['env'])
        else:
            env = None

        # Detect which LaTeX compiler we have...
        latex_bin = None
        for e in ["pdflatex", "latex"]:
            which_cmd = ['which', e]
            if subprocess.call(which_cmd) == 0:
                latex_bin = e
                self.log.info("%s LaTeX command found" % e)
                break
            else:
                self.log.info("%s LaTeX command not found" % e)
                latex_bin = None

        if not latex_bin:
            raise Exception("no executable found for latex")

        command = "%s %s" % (e, latex_filename)
        self.log.info(command)

        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout = stdout

        # Run LaTeX again for TOC numbering etc.
        proc = subprocess.Popen(command, shell=True,
                                cwd=self.artifact.artifacts_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=env)

        stdout, stderr = proc.communicate()
        self.artifact.stdout += stdout

from dexy.handler import DexyHandler
import shutil

class PdfFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['p', 'forcepdf']

    def process(self):
        self.artifact.auto_write_artifact = False
        shutil.copyfile(self.artifact.previous_artifact_filename, self.artifact.filename())

class LatexFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['l', 'forcelatex']

class HtmlFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['h', 'forcehtml']

class JsonFormatHandler(DexyHandler):
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ['j', 'forcejson']



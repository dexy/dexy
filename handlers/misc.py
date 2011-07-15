from dexy.dexy_filter import DexyFilter
import handlers
import shutil

class RFormatHandler(DexyFilter):
    """
    Does nothing, just forces previous filter to output .R extension if able.
    """
    INPUT_EXTENSIONS = [".R"]
    OUTPUT_EXTENSIONS = [".R"]
    ALIASES = ['forcer']

class PdfFormatHandler(DexyFilter):
    """
    Does nothing, just forces previous filter to output .pdf extension if able.
    """
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['p', 'forcepdf']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForceJpgFormatHandler(DexyFilter):
    """
    Does nothing, just forces previous filter to output .png extension if able.
    """
    INPUT_EXTENSIONS = [".jpg"]
    OUTPUT_EXTENSIONS = [".jpg"]
    ALIASES = ['jn', 'forcejpg']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForcePngFormatHandler(DexyFilter):
    """
    Does nothing, just forces previous filter to output .png extension if able.
    """
    INPUT_EXTENSIONS = [".png"]
    OUTPUT_EXTENSIONS = [".png"]
    ALIASES = ['pn', 'forcepng']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ConvertBashFormatHandler(DexyFilter):
    """
    Converts whatever file extension is input to be .bash.
    """
    INPUT_EXTENSIONS = [".*", "*"]
    OUTPUT_EXTENSIONS = [".sh"]
    ALIASES = ['b', 'forcebash']

class ConvertTextFormatHandler(DexyFilter):
    """
    Changes whatever file extension is input to be .txt.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['ct']

class ConvertHTMLFormatHandler(DexyFilter):
    """
    Changes whatever file extension is input to be .html.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['ch']

class TextFormatHandler(DexyFilter):
    """
    Does nothing, just forces previous filter to output .txt extension if able.
    """
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['t', 'forcetext']

class XmlFormatHandler(DexyFilter):
    """
    Does nothing, just forces previous filter to output .xml extension if able.
    """
    INPUT_EXTENSIONS = [".xml"]
    OUTPUT_EXTENSIONS = [".xml"]
    ALIASES = ['x', 'forcexml']

class LatexFormatHandler(DexyFilter):
    """
    Does nothing, just forces previous filter to output .tex extension if able.
    """
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['l', 'forcelatex']

class HtmlFormatHandler(DexyFilter):
    """
    Does nothing, just forces previous filter to output .html extension if able.
    """
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['h', 'forcehtml']

class JsonFormatHandler(DexyFilter):
    """
    Does nothing, just forces previous filter to output .json extension if able.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ['j', 'forcejson']


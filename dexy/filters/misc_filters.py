from dexy.dexy_filter import DexyFilter
import shutil

class RFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .R extension if able.
    """
    INPUT_EXTENSIONS = [".R"]
    OUTPUT_EXTENSIONS = [".R"]
    ALIASES = ['forcer']

class PdfFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .pdf extension if able.
    """
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['p', 'forcepdf']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForceJpgFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .png extension if able.
    """
    INPUT_EXTENSIONS = [".jpg"]
    OUTPUT_EXTENSIONS = [".jpg"]
    ALIASES = ['jn', 'forcejpg']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForcePngFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .png extension if able.
    """
    INPUT_EXTENSIONS = [".png"]
    OUTPUT_EXTENSIONS = [".png"]
    ALIASES = ['pn', 'forcepng']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForceGifFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .gif extension if able.
    """
    INPUT_EXTENSIONS = [".gif"]
    OUTPUT_EXTENSIONS = [".gif"]
    ALIASES = ['gn', 'forcegif']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForceBmpFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .bmp extension if able.
    """
    INPUT_EXTENSIONS = [".bmp"]
    OUTPUT_EXTENSIONS = [".bmp"]
    ALIASES = ['bn', 'forcebmp']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ConvertBashFormatFilter(DexyFilter):
    """
    Converts whatever file extension is input to be .bash.
    """
    INPUT_EXTENSIONS = [".*", "*"]
    OUTPUT_EXTENSIONS = [".sh"]
    ALIASES = ['b', 'forcebash']

class ConvertTextFormatFilter(DexyFilter):
    """
    Changes whatever file extension is input to be .txt.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['ct']

class ConvertHTMLFormatFilter(DexyFilter):
    """
    Changes whatever file extension is input to be .html.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['ch']

class TextFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .txt extension if able.
    """
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['t', 'forcetext']

class XmlFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .xml extension if able.
    """
    INPUT_EXTENSIONS = [".xml"]
    OUTPUT_EXTENSIONS = [".xml"]
    ALIASES = ['x', 'forcexml']

class LatexFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .tex extension if able.
    """
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['l', 'forcelatex']

class HtmlFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .html extension if able.
    """
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['h', 'forcehtml']

class JsonFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .json extension if able.
    """
    INPUT_EXTENSIONS = [".json"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ['j', 'forcejson']

class SvgFormatFilter(DexyFilter):
    """
    Does nothing, just forces previous filter to output .csv extension if able.
    """
    INPUT_EXTENSIONS = [".svg"]
    OUTPUT_EXTENSIONS = [".svg"]
    ALIASES = ['svg', 'forcesvg']

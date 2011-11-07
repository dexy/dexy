from dexy.dexy_filter import DexyFilter
import shutil

class ForceHtmlExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .html extension.
    """
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['h', 'forcehtml']

class ForceJsonExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .json extension.
    """
    INPUT_EXTENSIONS = [".json"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ['j', 'forcejson']

class ForceSvgExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .svg extension.
    """
    INPUT_EXTENSIONS = [".svg"]
    OUTPUT_EXTENSIONS = [".svg"]
    ALIASES = ['svg', 'forcesvg']

class ForceXmlExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .xml extension.
    """
    INPUT_EXTENSIONS = [".xml"]
    OUTPUT_EXTENSIONS = [".xml"]
    ALIASES = ['x', 'forcexml']

class ForceLatexExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .tex extension.
    """
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['l', 'forcelatex']

class ForceTextExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .txt extension.
    """
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['t', 'forcetext']

class ForceRExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .R extension.
    """
    INPUT_EXTENSIONS = [".R"]
    OUTPUT_EXTENSIONS = [".R"]
    ALIASES = ['forcer']

class ForcePdfExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .pdf extension.
    """
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['p', 'forcepdf']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForceJpgExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .jpg extension.
    """
    INPUT_EXTENSIONS = [".jpg"]
    OUTPUT_EXTENSIONS = [".jpg"]
    ALIASES = ['jn', 'forcejpg']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForcePngExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .png extension.
    """
    INPUT_EXTENSIONS = [".png"]
    OUTPUT_EXTENSIONS = [".png"]
    ALIASES = ['pn', 'forcepng']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForceGifExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .gif extension.
    """
    INPUT_EXTENSIONS = [".gif"]
    OUTPUT_EXTENSIONS = [".gif"]
    ALIASES = ['gn', 'forcegif']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ForceBmpExtensionFilter(DexyFilter):
    """
    Forces previous filter to output .bmp extension.
    """
    INPUT_EXTENSIONS = [".bmp"]
    OUTPUT_EXTENSIONS = [".bmp"]
    ALIASES = ['bn', 'forcebmp']
    BINARY = True

    def process(self):
        shutil.copyfile(self.artifact.previous_artifact_filepath, self.artifact.filepath())

class ConvertBashExtensionFilter(DexyFilter):
    """
    Changes file extension to .sh
    """
    INPUT_EXTENSIONS = [".*", "*"]
    OUTPUT_EXTENSIONS = [".sh"]
    ALIASES = ['cb']

class ConvertTextExtensionFilter(DexyFilter):
    """
    Changes file extension to .txt
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['ct']

class ConvertHTMLExtensionFilter(DexyFilter):
    """
    Changes file extension to .html
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['ch']

class ConvertJsonExtensionFilter(DexyFilter):
    """
    Changes file extension to .json
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ['cj']

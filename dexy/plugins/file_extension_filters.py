from dexy.filter import DexyFilter

class PreserveDataClassFilter(DexyFilter):
    """
    Sets PRESERVE_PRIOR_DATA_CLASS to True.
    """
    ALIASES = []
    PRESERVE_PRIOR_DATA_CLASS = True

    def calculate_canonical_name(self):
        return self.artifact.prior.filter_instance.calculate_canonical_name()

class ChangeExtensionManuallyFilter(PreserveDataClassFilter):
    """
    Dummy filter for allowing changing a file extension.
    """
    ALIASES = ['chext']

class ForceCPickleExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .cpickle extension.
    """
    INPUT_EXTENSIONS = [".cpickle"]
    OUTPUT_EXTENSIONS = [".cpickle"]
    ALIASES = ['cpickle']

class ForcePickleExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .pickle extension.
    """
    INPUT_EXTENSIONS = [".pickle"]
    OUTPUT_EXTENSIONS = [".pickle"]
    ALIASES = ['pickle']

class ForceHtmlExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .html extension.
    """
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['h', 'forcehtml']

class ForceJsonExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .json extension.
    """
    INPUT_EXTENSIONS = [".json"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ['j', 'forcejson']

class ForceSvgExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .svg extension.
    """
    INPUT_EXTENSIONS = [".svg"]
    OUTPUT_EXTENSIONS = [".svg"]
    ALIASES = ['svg', 'forcesvg']

class ForceXmlExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .xml extension.
    """
    INPUT_EXTENSIONS = [".xml"]
    OUTPUT_EXTENSIONS = [".xml"]
    ALIASES = ['x', 'forcexml']

class ForceLatexExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .tex extension.
    """
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['l', 'forcelatex']

class ForceTextExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .txt extension.
    """
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['t', 'forcetext']

class ForceRExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .R extension.
    """
    INPUT_EXTENSIONS = [".R"]
    OUTPUT_EXTENSIONS = [".R"]
    ALIASES = ['forcer']

class ForcePdfExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .pdf extension.
    """
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['p', 'forcepdf']

class ForceJpgExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .jpg extension.
    """
    INPUT_EXTENSIONS = [".jpg"]
    OUTPUT_EXTENSIONS = [".jpg"]
    ALIASES = ['jn', 'forcejpg']

class ForcePngExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .png extension.
    """
    INPUT_EXTENSIONS = [".png"]
    OUTPUT_EXTENSIONS = [".png"]
    ALIASES = ['pn', 'forcepng']

class ForceGifExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .gif extension.
    """
    INPUT_EXTENSIONS = [".gif"]
    OUTPUT_EXTENSIONS = [".gif"]
    ALIASES = ['gn', 'forcegif']

class ForceBmpExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .bmp extension.
    """
    INPUT_EXTENSIONS = [".bmp"]
    OUTPUT_EXTENSIONS = [".bmp"]
    ALIASES = ['bn', 'forcebmp']

class ConvertBashExtensionFilter(PreserveDataClassFilter):
    """
    Changes file extension to .sh
    """
    INPUT_EXTENSIONS = [".*", "*"]
    OUTPUT_EXTENSIONS = [".sh"]
    ALIASES = ['cb']

class ConvertTextExtensionFilter(PreserveDataClassFilter):
    """
    Changes file extension to .txt
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['ct']

class ConvertHTMLExtensionFilter(PreserveDataClassFilter):
    """
    Changes file extension to .html
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['ch']

class ConvertJsonExtensionFilter(PreserveDataClassFilter):
    """
    Changes file extension to .json
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ['cj']

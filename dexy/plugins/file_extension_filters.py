from dexy.filter import DexyFilter

class PreserveDataClassFilter(DexyFilter):
    """
    Sets PRESERVE_PRIOR_DATA_CLASS to True.
    """
    ALIASES = []
    _SETTINGS = {
            'preserve-prior-data-class' : True
            }

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
    ALIASES = ['cpickle']
    _SETTINGS = {
            'input-extensions' : ['cpickle'],
            'output-extensions' : ['cpickle']
            }

class ForcePickleExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .pickle extension.
    """
    ALIASES = ['pickle']
    _SETTINGS = {
            'input-extensions' : ['pickle'],
            'output-extensions' : ['pickle']
            }

class ForceHtmlExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .html extension.
    """
    ALIASES = ['h', 'forcehtml']
    _SETTINGS = {
            'input-extensions' : ['.html'],
            'output-extensions' : ['.html'],
            }

class ForceJsonExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .json extension.
    """
    ALIASES = ['j', 'forcejson']
    _SETTINGS = {
            'input-extensions' : ['.json'],
            'output-extensions' : ['.json'],
            }

class ForceSvgExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .svg extension.
    """
    ALIASES = ['svg', 'forcesvg']
    _SETTINGS = {
            'input-extensions' : ['.svg'],
            'output-extensions' : ['.svg'],
            }

class ForceXmlExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .xml extension.
    """
    ALIASES = ['x', 'forcexml']
    _SETTINGS = {
            'input-extensions' : ['.xml'],
            'output-extensions' : ['.xml'],
            }

class ForceLatexExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .tex extension.
    """
    ALIASES = ['l', 'forcelatex']
    _SETTINGS = {
            'input-extensions' : ['.tex'],
            'output-extensions' : ['.tex'],
            }

class ForceTextExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .txt extension.
    """
    ALIASES = ['t', 'forcetext']
    _SETTINGS = {
            'input-extensions' : ['.txt'],
            'output-extensions' : ['.txt'],
            }

class ForceRExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .R extension.
    """
    ALIASES = ['forcer']
    _SETTINGS = {
            'input-extensions' : ['.R'],
            'output-extensions' : ['.R'],
            }

class ForcePdfExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .pdf extension.
    """
    ALIASES = ['p', 'forcepdf']
    _SETTINGS = {
            'input-extensions' : ['.pdf'],
            'output-extensions' : ['.pdf'],
            }

class ForceJpgExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .jpg extension.
    """
    ALIASES = ['jn', 'forcejpg']
    _SETTINGS = {
            'input-extensions' : ['.jpg'],
            'output-extensions' : ['.jpg'],
            }

class ForcePngExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .png extension.
    """
    ALIASES = ['pn', 'forcepng']
    _SETTINGS = {
            'input-extensions' : ['.png'],
            'output-extensions' : ['.png'],
            }

class ForceGifExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .gif extension.
    """
    ALIASES = ['gn', 'forcegif']
    _SETTINGS = {
            'input-extensions' : ['.gif'],
            'output-extensions' : ['.gif'],
            }

class ForceBmpExtensionFilter(PreserveDataClassFilter):
    """
    Forces previous filter to output .bmp extension.
    """
    ALIASES = ['bn', 'forcebmp']
    _SETTINGS = {
            'input-extensions' : ['.bmp'],
            'output-extensions' : ['.bmp'],
            }

class ConvertBashExtensionFilter(PreserveDataClassFilter):
    """
    Changes file extension to .sh
    """
    ALIASES = ['cb']
    _SETTINGS = {
            'input-extensions' : ['.*', '*'],
            'output-extensions' : ['.sh'],
            }

class ConvertTextExtensionFilter(PreserveDataClassFilter):
    """
    Changes file extension to .txt
    """
    ALIASES = ['ct']
    _SETTINGS = {
            'input-extensions' : ['.*'],
            'output-extensions' : ['.txt'],
            }

class ConvertHTMLExtensionFilter(PreserveDataClassFilter):
    """
    Changes file extension to .html
    """
    ALIASES = ['ch']
    _SETTINGS = {
            'input-extensions' : ['.*'],
            'output-extensions' : ['.html'],
            }

class ConvertJsonExtensionFilter(PreserveDataClassFilter):
    """
    Changes file extension to .json
    """
    ALIASES = ['cj']
    _SETTINGS = {
            'input-extensions' : ['.*'],
            'output-extensions' : ['.json'],
            }

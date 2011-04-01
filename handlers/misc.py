from dexy.handler import DexyHandler

class PdfFormatHandler(DexyHandler):
    """
    Does nothing, just forces previous filter to output .pdf extension if able.
    """
    INPUT_EXTENSIONS = [".pdf"]
    OUTPUT_EXTENSIONS = [".pdf"]
    ALIASES = ['p', 'forcepdf']

class ConvertBashFormatHandler(DexyHandler):
    """
    Does nothing, just forces previous filter to output .bash extension if able.
    """
    INPUT_EXTENSIONS = [".*", "*"]
    OUTPUT_EXTENSIONS = [".sh"]
    ALIASES = ['b', 'forcebash']

class ConvertTextFormatHandler(DexyHandler):
    """
    Changes whatever file extension is input to be .txt.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['ct']

class ConvertHTMLFormatHandler(DexyHandler):
    """
    Changes whatever file extension is input to be .html.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['ch']

class TextFormatHandler(DexyHandler):
    """
    Does nothing, just forces previous filter to output .txt extension if able.
    """
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".txt"]
    ALIASES = ['t', 'forcetext']

class XmlFormatHandler(DexyHandler):
    """
    Does nothing, just forces previous filter to output .xml extension if able.
    """
    INPUT_EXTENSIONS = [".xml"]
    OUTPUT_EXTENSIONS = [".xml"]
    ALIASES = ['x', 'forcexml']

class LatexFormatHandler(DexyHandler):
    """
    Does nothing, just forces previous filter to output .tex extension if able.
    """
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    ALIASES = ['l', 'forcelatex']

class HtmlFormatHandler(DexyHandler):
    """
    Does nothing, just forces previous filter to output .html extension if able.
    """
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]
    ALIASES = ['h', 'forcehtml']

class JsonFormatHandler(DexyHandler):
    """
    Does nothing, just forces previous filter to output .json extension if able.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".json"]
    ALIASES = ['j', 'forcejson']


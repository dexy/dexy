import uuid
import os.path
import pexpect
from dexy.handler import DexyHandler

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



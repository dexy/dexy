import dexy.exceptions
import inspect
import json
import os
import posixpath
import re
import shutil
import tempfile
import yaml

def file_exists(filepath):
    #print "calling file_exists on %s" % filepath
    #frame = inspect.currentframe()
    #for f in inspect.getouterframes(frame):
    #    print "   ", f[1], f[2], f[3]
    #del frame
    #del f
    return os.path.exists(filepath)

def iter_paths(path):
    """
    Iterate over all subpaths of path starting with root path.
    """
    path_elements = split_path(path)

    if path.startswith(os.sep):
        start = os.sep
    else:
        start = None

    for i in range(1, len(path_elements)+1):
        if start:
            yield os.path.join(start, *path_elements[0:i])
        else:
            yield os.path.join(*path_elements[0:i])

def reverse_iter_paths(path):
    """
    Iterate over all subpaths of path starting with path, ending with root path.
    """
    path_elements = split_path(path)
    for i in range(len(path_elements), 0, -1):
        yield os.path.join(*path_elements[0:i])
    yield "/"

def split_path(path):
    # TODO test that paths are normed and don't include empty or '.' components.
    tail = True
    path_elements = []
    body = path
    while tail:
        body, tail = os.path.split(body)
        if tail:
            path_elements.append(tail)
        elif path.startswith("/"):
            path_elements.append(tail)
            
    path_elements.reverse()
    return path_elements

class tempdir(object):
    def make_temp_dir(self):
        self.tempdir = tempfile.mkdtemp()
        self.location = os.path.abspath(os.curdir)
        os.chdir(self.tempdir)

    def remove_temp_dir(self):
        os.chdir(self.location)
        try:
            shutil.rmtree(self.tempdir)
        except Exception as e:
            print e
            print "was not able to remove tempdir '%s'" % self.tempdir

    def __enter__(self):
        self.make_temp_dir()

    def __exit__(self, type, value, traceback):
        if not isinstance(value, Exception):
            self.remove_temp_dir()

def value_for_hyphenated_or_underscored_arg(arg_dict, arg_name_hyphen, default=None):
    if not "-" in arg_name_hyphen and "_" in arg_name_hyphen:
        raise dexy.exceptions.InternalDexyProblem("arg_name_hyphen %s has underscores!" % arg_name_hyphen)

    arg_name_underscore = arg_name_hyphen.replace("-", "_")

    arg_value = arg_dict.get(arg_name_hyphen)

    if arg_value is None:
        arg_value = arg_dict.get(arg_name_underscore)

    if arg_value is None:
        return default
    else:
        return arg_value

def s(text):
    return re.sub('\s+', ' ', text)

def getdoc(element, firstline=True):
    docstring = inspect.getdoc(element)
    if docstring and firstline:
        docstring = docstring.splitlines()[0]

    if not docstring:
        docstring = ''

    return docstring

def os_to_posix(path):
    return posixpath.join(*os.path.split(path))

def parse_json(input_text):
    try:
        return json.loads(input_text)
    except ValueError as e:
        msg = inspect.cleandoc("""Was unable to parse the JSON you supplied.
        Here is information from the JSON parser:""")
        msg += "\n"
        msg += str(e)
        raise dexy.exceptions.UserFeedback(msg)

def parse_json_from_file(f):
    try:
        return json.load(f)
    except ValueError as e:
        msg = inspect.cleandoc("""Was unable to parse the JSON you supplied.
        Here is information from the JSON parser:""")
        msg += "\n"
        msg += str(e)
        raise dexy.exceptions.UserFeedback(msg)

def parse_yaml(input_text):
    """
    Parse a single YAML document.
    """
    try:
        return yaml.safe_load(input_text)
    except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
        msg = inspect.cleandoc("""Was unable to parse the YAML you supplied.
        Here is information from the YAML parser:""")
        msg += "\n"
        msg += str(e)
        raise dexy.exceptions.UserFeedback(msg)

def parse_yamls(input_text):
    """
    Parse YAML content that may include more than 1 document.
    """
    try:
        return yaml.safe_load_all(input_text)
    except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
        msg = inspect.cleandoc("""Was unable to parse the YAML you supplied.
        Here is information from the YAML parser:""")
        msg += "\n"
        msg += str(e)
        raise dexy.exceptions.UserFeedback(msg)

def printable_for_char(c):
    if ord(c) >= ord('!'):
        return c
    elif ord(c) == 32:
        return "<space>"
    else:
        return ""

def char_diff(str1, str2):
    """
    Returns a char-by-char diff of two strings, highlighting differences.
    """
    msg = ""
    for i, c1 in enumerate(str1):
        if len(str2) > i:
            c2 = str2[i]

            if c1 == c2:
                flag = ""
            else:
                flag = " <---"

            p_c1 = printable_for_char(c1)
            p_c2 = printable_for_char(c2)

            msg = msg + "\n%5d: %8s\t%8s\t\t%s\t%s %s" % (i, p_c1, p_c2, ord(c1), ord(c2), flag)
        else:
            # str1 is longer than str2
            flag = " <---"
            p_c1 = printable_for_char(c1)
            msg = msg + "\n%5d: %8s\t%8s\t\t%s\t%s %s" % (i, p_c1, '  ', ord(c1), '  ', flag)

    # TODO add code for str2 longer than str1

    return msg

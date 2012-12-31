import dexy.exceptions
import inspect
import json
import os
import yaml
import posixpath
import re

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
        return yaml.load(input_text)
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
        return yaml.load_all(input_text)
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

# Based on http://nedbatchelder.com/code/utilities/wh.py
def command_exists(cmd_name):
    path = os.environ["PATH"]
    if ";" in path:
        path = filter(None, path.split(";"))
    else:
        path = filter(None, path.split(":"))

    if os.environ.has_key("PATHEXT"):
        # Present on windows, returns e.g. '.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC'
        pathext = os.environ["PATHEXT"]
        pathext = filter(None, pathext.split(";"))
    else:
        # Not windows, look for exact command name.
        pathext = [""]

    cmd_found = False
    for d in path:
        for e in pathext:
            filepath = os.path.join(d, cmd_name + e)
            if os.path.exists(filepath):
                cmd_found = True
                break
    return cmd_found

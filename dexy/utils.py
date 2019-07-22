import dexy.exceptions
import hashlib
import inspect
import json
import logging
import os
import platform
import posixpath
import re
import shutil
import tempfile
import time
import yaml

is_windows = platform.system() in ('Windows',)

def copy_or_link(data, destination, use_links=False, read_only_links=True):
    """
    Copies or makes a hard link. Will copy if on windows or if use_links is False.
    """
    if is_windows or not use_links:
        data.output_to_file(destination)
    else:
        os.link(data.storage.data_file(), destination)

defaults = {
    'artifacts_dir' : '.dexy',
    'config_file' : 'dexy.conf',
    'configs' : '',
    'debug' : False,
    'directory' : ".",
    'dont_use_cache' : False,
    'dry_run' : False,
    'encoding' : 'utf-8',
    'exclude' : '.git, .svn, tmp, cache, .trash, .ipynb_checkpoints',
    'exclude_also' : '',
    'full' : False,
    'globals' : '',
    'hashfunction' : 'md5',
    'ignore_nonzero_exit' : False,
    'include' : '',
    'log_dir' : '.dexy',
    'log_file' : 'dexy.log',
    'log_format' : "%(name)s - %(levelname)s - %(message)s",
    'log_level' : "INFO",
    'output_root' : '.',
    'parsers' : "dexy-env.json dexy.txt dexy.yaml",
    'pickle' : 'c',
    'plugins': 'dexyplugins.py dexyplugin.py dexyplugins.yaml dexyplugin.yaml',
    'profile' : False,
    'recurse' : True,
    'reports' : '',
    'safety_filename' : '.dexy-generated',
    'siblings' : False,
    'silent' : False,
    'strace' : False,
    'target' : False,
    'timing' : True,
    'uselocals' : False,
    'writeanywhere' : False
}

log_levels = {
    'DEBUG' : logging.DEBUG,
    'INFO' : logging.INFO,
    'WARN' : logging.WARN
}

def transition(obj, new_state):
    """
    Attempts to transition this object to the new state, if the transition
    from current state to new state is valid as per state_transitions list.
    """
    attempted_transition = (obj.state, new_state) 
    if not attempted_transition in obj.__class__.state_transitions:
        msg = "%s -> %s"
        raise dexy.exceptions.UnexpectedState(msg % attempted_transition)

    if not hasattr(obj, 'time_entered_current_state'):
        obj.time_entered_current_state = None
        obj.state_history = []
  
    if obj.time_entered_current_state:
        transition_time = time.time()

        time_in_prev_state = transition_time - obj.time_entered_current_state
        obj.state_history.append((obj.state, time_in_prev_state))

    obj.time_entered_current_state = time.time()
    obj.state = new_state

def logging_log_level(log_level):
    try:
        return log_levels[log_level.upper()]
    except KeyError:
        msg = "'%s' is not a valid log level, check python logging module docs"
        raise dexy.exceptions.UserFeedback(msg % log_level)

def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def dict_from_string(text):
    """
    Creates a dict from string like "key1=value1,k2=v2"
    """
    d = {}
    if text > 0:
        for pair in text.split(","):
            x, y = pair.split("=")
            d[x] = y
    return d

def file_exists(filepath, debug=False):
    if debug:
        print(("calling file_exists on %s" % filepath))
        frame = inspect.currentframe()
        for f in inspect.getouterframes(frame):
            print(("   ", f[1], f[2], f[3]))
        del frame
        del f
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
            print(e)
            print(("was not able to remove tempdir '%s'" % self.tempdir))

    def __enter__(self):
        self.make_temp_dir()

    def __exit__(self, type, value, traceback):
        if not isinstance(value, Exception):
            self.remove_temp_dir()

class chdir(object):
    def __init__(self, newdir):
        self.newdir = newdir
        self.location = os.path.abspath(os.curdir)

    def __enter__(self):
        os.chdir(self.newdir)

    def __exit__(self, type, value, traceback):
        os.chdir(self.location)

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
        if "found character '\\t'" in str(e):
            msg = "You appear to have hard tabs in your yaml, this is not supported. Please change to using soft tabs instead (your text editor should have this option)."
            raise dexy.exceptions.UserFeedback(msg)
        else:
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

# http://code.activestate.com/recipes/576874-levenshtein-distance/
def levenshtein(s1, s2):
    l1 = len(s1)
    l2 = len(s2)

    matrix = [range(l1 + 1)] * (l2 + 1)
    for zz in range(l2 + 1):
      matrix[zz] = range(zz,zz + l1 + 1)
    for zz in range(0,l2):
      for sz in range(0,l1):
        if s1[sz] == s2[zz]:
          matrix[zz+1][sz+1] = min(matrix[zz+1][sz] + 1, matrix[zz][sz+1] + 1, matrix[zz][sz])
        else:
          matrix[zz+1][sz+1] = min(matrix[zz+1][sz] + 1, matrix[zz][sz+1] + 1, matrix[zz][sz] + 1)
    return matrix[l2][l1]

def indent(s, spaces=4):
    return "\n".join("%s%s" % (' ' * spaces, line)
            for line in s.splitlines())

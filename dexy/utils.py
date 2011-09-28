from BeautifulSoup import BeautifulSoup
from ansi2html import Ansi2HTMLConverter
from pynliner import Pynliner
import StringIO
import datetime
import gc
import logging
import os
import re

# http://code.activestate.com/recipes/361668/#c2
class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    def __getattr__(self, name):
        return self[name]

def ansi_output_to_html(ansi_text):
    try:
        converter = Ansi2HTMLConverter()
        html = converter.convert(ansi_text)
    except IOError as e:
        if re.search("templates/header.mak", str(e)):
            print e
            raise Exception("Your installation of ansi2html is missing some template files, please try 'pip install --upgrade ansi2html' or install from source.")
        raise e

    log = logging.getLogger("pynliner")
    log.setLevel(logging.ERROR) # TODO Allow this to be changed.
    logstream = StringIO.StringIO()
    handler = logging.StreamHandler(logstream)
    log.addHandler(handler)
    try:
        p = Pynliner(log)
    except TypeError:
        print "========== Start of harmless but annoying CSS errors..."
        print "You can install pynliner from source (https://github.com/rennat/pynliner.git) or version > 0.2.1 to get rid of these"
        p = Pynliner()

    p.from_string(html)
    html_with_css_inline = p.run()

    # Ansi2HTMLConverter returns a complete HTML document, we just want body
    doc = BeautifulSoup(html_with_css_inline)
    return doc.body.renderContents()

def print_string_diff(str1, str2):
    msg = ""
    for i, c1 in enumerate(str1):
        if len(str2) > i:
            c2 = str2[i]
            if c1 == c2:
                flag = ""
            else:
                flag = " <---"
            if ord(c1) > ord('a') and ord(c2) > ord('a'):
                msg = msg + "\n%5d: %s\t%s\t\t%s\t%s %s" % (i, c1, c2,
                                              ord(c1), ord(c2), flag)
            else:
                msg = msg + "\n%5d:  \t \t\t%s\t%s %s" % (i, ord(c1),
                                              ord(c2), flag)
        else:
            flag = "<---"
            msg = msg + "\n%5d:  \t \t\t%s %s" % (i, ord(c1), flag)
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

#def profile_memory(description=None):
#    file_name = "memory.log"
#    new_file = not os.path.exists(file_name)
#    f = open("memory.log", "a")
#    if new_file:
#        f.write("vm_size\tgc_count\ttimestamp\tdescription\n")
#    pid = os.getpid()
#    vm_size = MemoryMonitor.getVmSize(pid)
#    gc_count = len(gc.get_objects())
#    timestamp = datetime.datetime.now()
#    f.write("%s\t%s\t%s\t%s\n" % (vm_size, gc_count, timestamp, description))
#    f.close()

from BeautifulSoup import BeautifulSoup
from ansi2html import Ansi2HTMLConverter
from dexy.constants import Constants
from dexy.sizeof import asizeof
from pynliner import Pynliner
import StringIO
import datetime
import dexy.database
import dexy.databases.csv_database
import dexy.introspect
import gc
import json
import logging
import logging.handlers
import os
import re

def load_batch_info(batch_id, logsdir=Constants.DEFAULT_LDIR):
    with open(batch_info_filename(batch_id, logsdir), "r") as f:
        return json.load(f)

def save_batch_info(batch_id, batch_info, logsdir=Constants.DEFAULT_LDIR):
    with open(batch_info_filename(batch_id, logsdir), "w") as f:
        json.dump(batch_info, f, sort_keys = True, indent = 4)

def batch_info_filename(batch_id, logsdir):
    return os.path.join(logsdir, "batch-%05d.json" % batch_id)

def get_db(db_classname=Constants.DEFAULT_DBCLASS, **kwargs):
    # TODO cache the database classes list somewhere
    database_classes = dexy.introspect.database_classes()
    db_class = database_classes[db_classname]
    return db_class(**kwargs)

def get_log(
        name=Constants.DEFAULT_LOGGER_NAME, # Name of the logger
        logsdir=Constants.DEFAULT_LDIR, # Directory to store the logfile
        logfile=Constants.DEFAULT_LFILE, # Filename of logfile
        loglevel=Constants.DEFAULT_LOGLEVEL # Log level to use
    ):
    """Get a log."""

    log = logging.getLogger(Constants.DEFAULT_LOGGER_NAME)
    log.propagate = 0

    if len(log.handlers) == 0:
        # Set up handlers and formatters.
        try:
            log.setLevel(Constants.LOGLEVELS[loglevel])
        except KeyError:
            msg = "You requested log level '%s', valid values are %s" % (loglevel, ",".join(Constants.LOGLEVELS.keys()))
            raise Exception(msg)

        if logsdir and logfile:
            logfile = os.path.join(logsdir, logfile)
            handler = logging.handlers.RotatingFileHandler(logfile)
        else:
            handler = logging.StreamHandler() # log to sys.stderr

        log.addHandler(handler)
        formatter = logging.Formatter(Constants.DEFAULT_LOGFORMAT)
        handler.setFormatter(formatter)

    if name == Constants.DEFAULT_LOGGER_NAME:
        return log
    else:
        log2 = logging.getLogger(name)
        log2.handlers = log.handlers
        return log2

def remove_all_handlers(log):
    for h in log.handlers:
        log.removeHandler(h)

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

try:
    from dexy import MemoryMonitor

    def profile_memory(controller, description=None):
        file_name = "logs/memory.log"
        new_file = not os.path.exists(file_name)
        f = open(file_name, "a")
        if new_file:
            f.write("vm_size\tgc_count\tcontroller_size\ttimestamp\tdescription\n")
        pid = os.getpid()
        vm_size = MemoryMonitor.getVmSize(pid)
        gc_count = len(gc.get_objects())
        controller_size = asizeof(controller)
        timestamp = datetime.datetime.now()
        f.write("%s\t%s\t%s\t%s\t%s\n" % (vm_size, gc_count, controller_size, timestamp, description))
        f.close()

except ImportError:
    def profile_memory(controller, description=None):
        pass

#http://code.activestate.com/recipes/148061-one-liner-word-wrap-function/
def wrap_text(text, width):
    """
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).
    """
    return reduce(lambda line, word, width=width: '%s%s%s' %
             (line,
               ' \n'[(len(line)-line.rfind('\n')-1
                     + len(word.split('\n',1)[0]
                          ) >= width)],
               word),
              text.split(' ')
             )

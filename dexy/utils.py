import os

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

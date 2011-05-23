from BeautifulSoup import BeautifulSoup
from ansi2html import Ansi2HTMLConverter
from pynliner import Pynliner
import re

def ansi_output_to_html(ansi_text, log=None):
    try:
        converter = Ansi2HTMLConverter()
        html = converter.convert(ansi_text)
    except IOError as e:
        if re.search("templates/header.mak", str(e)):
            print e
            raise Exception("Your installation of ansi2html is missing some template files, please try 'pip install --upgrade ansi2html' or install from source.")
        raise e

    try:
        p = Pynliner(log)
        if not log: # put after call to Pynliner() so it doesn't print in case of error
            print """a custom log has not been passed to dexy.utils.ansi_output_to_html,
            harmless but annoying CSS errors will appear on the console."""
    except TypeError:
        print "========== Start of harmless but annoying CSS errors..."
        print "You can install pynliner from source or version > 0.2.1 to get rid of these"
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

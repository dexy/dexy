from dexy.version import DEXY_VERSION
import datetime
import dexy.exceptions

# TODO list available citation types

def cite_command(
        fmt='bibtex' # desired format of citation
        ):
    """
    How to cite dexy in papers.
    """
    if fmt == 'bibtex':
        cite_bibtex()
    else:
        msg = "Don't know how to provide citation in '%s' format"
        raise dexy.exceptions.UserFeedback(msg % fmt)

def bibtex_text():
    args = {
            'version' : DEXY_VERSION,
            'year' : datetime.date.today().year
            }

    return """@misc{Dexy,
    title = {Dexy: Reproducible Data Analysis and Document Automation Software, Version~%(version)s},
    author = {{Nelson, Ana}},
    year = {%(year)s},
    url = {http://www.dexy.it/},
    note = {http://orcid.org/0000-0003-2561-1564}
}""" % args

def cite_bibtex():
    print bibtex_text()

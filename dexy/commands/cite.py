from dexy.version import DEXY_VERSION
import datetime
import dexy.exceptions

def cite_command(
        fmt='bibtex'
        ):
    """
    How to cite dexy in papers.
    """
    if fmt == 'bibtex':
        cite_bibtex()
    else:
        raise dexy.exceptions.UserFeedback("Don't know how to provide citation in '%s' format" % fmt)

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

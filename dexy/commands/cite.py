from dexy.version import DEXY_VERSION
import datetime

citation_formats = ['bibtex']

def build_cite_parser(parser):
    parser.set_defaults(cmd=cite_command)
    parser.add_argument('-f', '--fmt', default=citation_formats[0], help="Desired format of citation.")

# TODO list available citation types

def cite_command(args):
    fmt = args.fmt
    if fmt == 'bibtex':
        cite_bibtex()
    else:
        msg = f"Don't know how to provide citation in '%{fmt}' format"
        print(msg)
        # raise dexy.exceptions.UserFeedback(msg % fmt)

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
    print((bibtex_text()))

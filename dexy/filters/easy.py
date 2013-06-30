# The easyhtml filter is defined in dexy.filters.fluid_html

from dexy.filter import DexyFilter
from pygments.formatters import LatexFormatter

class EasyLatex(DexyFilter):
    """
    Wraps your text in LaTeX article header/footer.
    Easy way to generate a document which can be compiled using LaTeX (includes
    Pygments syntax highlighting).
    """
    aliases = ['easylatex']
    _settings = {
            'input-extensions' : ['.tex'],
            'output-extensions' : ['.tex'],
            'documentclass' : ("The document class to generate.", "article"),
            'style' : ("The pygments style to use.", "default"),
            'title' : ("Title of article.", ""),
            'author' : ("Author of article.", ""),
            'date' : ("Date of article.", ""),
            'font' : ("The font size to use.", "11pt"),
            'papersize' : ("The document class to generate.", "a4paper"),
            "preamble" : ("Additional custom LaTeX content to include in header.", "")
            }

    def pygments_sty(self):
        formatter = LatexFormatter(style=self.setting('style'))
        return formatter.get_style_defs()

    def process_text(self, input_text):
        args = self.setting_values()
        args['input'] = input_text
        args['pygments'] = self.pygments_sty()

        if self.setting('title'):
            args['title'] = r"\title{%(title)s}" % args
            args['maketitle'] = r"\maketitle"
        else:
            args['title'] = ""
            args['maketitle'] = ""

        if self.setting('date'):
            args['date'] = r"\date{%(date)s}" % args

        if self.setting('author'):
            args['author'] = r"\author{%(author)s}" % args

        return self.template % args

    template = r"""\documentclass[%(font)s,%(papersize)s]{%(documentclass)s}
\usepackage{color}
\usepackage{fancyvrb}
%(pygments)s

%(preamble)s

%(title)s
%(author)s
%(date)s

\begin{document}

%(maketitle)s


%(input)s

\end{document}
"""

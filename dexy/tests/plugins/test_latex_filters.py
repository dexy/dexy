from dexy.tests.utils import runfilter
import dexy.exceptions

def test_latex():
    with runfilter('latex', LATEX) as doc:
        assert ".pdf" in doc.output_data().name
        assert doc.output_data().is_cached()

def test_latex_dvi():
    with runfilter('latexdvi', LATEX) as doc:
        assert ".dvi" in doc.output_data().name
        assert doc.output_data().is_cached()

def test_tikz():
    with runfilter('tikz', TIKZ) as doc:
        assert ".pdf" in doc.output_data().name
        assert doc.output_data().is_cached()

def test_xetex():
    with runfilter('xetex', LATEX) as doc:
        assert ".pdf" in doc.output_data().name
        assert doc.output_data().is_cached()

def test_broken_latex():
    with runfilter('latex', BROKEN_LATEX):
        pass

TIKZ = """\
\\tikz \draw (0,0) -- (1,1)
{[rounded corners] -- (2,0) -- (3,1)}
-- (3,0) -- (2,1);
"""
LATEX = """\
\documentclass{article}
\\title{Hello, World!}
\\begin{document}
\maketitle
Hello!
\end{document}
"""

BROKEN_LATEX = """\
\documentclass{article}
"""

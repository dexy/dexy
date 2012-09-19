from dexy.tests.utils import runfilter
import os

def test_tikz_filter():
    with runfilter('tikz', TIKZ) as doc:
        assert ".pdf" in doc.output().name
        assert doc.output().is_cached()

def test_latex_filter():
    with runfilter('latex', LATEX) as doc:
        assert ".pdf" in doc.output().name
        assert doc.output().is_cached()

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

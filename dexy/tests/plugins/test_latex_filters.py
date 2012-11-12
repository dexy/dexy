from dexy.tests.utils import runfilter
import dexy.exceptions

def test_tikz():
    with runfilter('tikz', TIKZ) as doc:
        assert ".pdf" in doc.output().name
        assert doc.output().is_cached()

def test_latex():
    with runfilter('latex', LATEX) as doc:
        assert ".pdf" in doc.output().name
        assert doc.output().is_cached()

def test_xetex():
    with runfilter('xetex', LATEX) as doc:
        assert ".pdf" in doc.output().name
        assert doc.output().is_cached()

def test_broken_latex():
    try:
        with runfilter('latex', BROKEN_LATEX):
            pass
        assert False, 'should raise UserFeedback'
    except dexy.exceptions.UserFeedback as e:
        assert "Latex file not generated" in e.message

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

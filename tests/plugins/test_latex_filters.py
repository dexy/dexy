from tests.utils import runfilter
from tests.utils import wrap
from dexy.doc import Doc
from nose.exc import SkipTest

def test_latex():
    with runfilter('latex', LATEX) as doc:
        assert ".pdf" in doc.output_data().name
        assert doc.output_data().is_cached()

def test_latex_dvi():
    with runfilter('latexdvi', LATEX) as doc:
        assert ".dvi" in doc.output_data().name
        assert doc.output_data().is_cached()

def test_tikz():
    # TODO fix for tikz not installed
    raise SkipTest()
    with runfilter('tikz', TIKZ) as doc:
        assert ".pdf" in doc.output_data().name
        assert doc.output_data().is_cached()

def test_broken_latex():
    with wrap() as wrapper:
        wrapper.debug = False
        node = Doc("example.tex|latex",
                wrapper,
                [],
                contents = BROKEN_LATEX
                )
        wrapper.run_docs(node)
        assert wrapper.state == 'error'

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

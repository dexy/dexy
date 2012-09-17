from dexy.tests.utils import runfilter
import inspect
import os

def test_latex_filter():
    LATEX = inspect.cleandoc("""
        \documentclass{article}
        \\title{Hello, World!}
        \\begin{document}
        \maketitle
        Hello!
        \end{document}
        """)

    with runfilter('latex', LATEX) as doc:
        assert ".pdf" in doc.output().name
        assert doc.output().is_cached()

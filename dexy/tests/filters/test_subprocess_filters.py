from dexy.tests.utils import run_dexy
from dexy.tests.utils import assert_output
from dexy.tests.utils import assert_in_output
from dexy.tests.utils import assert_matches_output

def test_pandoc():
    assert_in_output("example.txt|pandoc", "## Hello", ">Hello</h2")

def test_espeak():
    assert_in_output("example.txt|espeak", "Hello", "")

def test_asciidoc():
    assert_in_output("example.txt|asciidoc", "Introduction\n------------", """<h2 id="_introduction">Introduction</h2>""")

def test_latex():
    latex = """
    \documentclass{article}
    \\begin{document}
    Hello
    \\end{document}
    """
    assert_in_output("example.tex|latex", latex, "")

def test_rout():
    assert_output("example.R|rout", "1+1", "[1] 2\n")

def test_rintbatch():
    assert_output("example.R|rintbatch", "1+1", "> 1+1\n[1] 2\n> \n")

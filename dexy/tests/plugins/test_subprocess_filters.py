from dexy.tests.utils import assert_output
from dexy.tests.utils import assert_in_output
from dexy.tests.utils import assert_output_cached
from dexy.tests.utils import wrap
from dexy.tests.utils import TEST_DATA_DIR
from dexy.node import DocNode
import os
import shutil

PYIN_CONTENTS = """import sys
i = 0
while True:
    i += 1
    line = sys.stdin.readline()
    if not line:
        break
    print "line %s has %s chars" % (i, len(line))
"""

def test_python_input():
    with wrap() as wrapper:
        node = DocNode("hello.py|pyin",
                contents=PYIN_CONTENTS,
                inputs = [
                    DocNode("input.in",
                        contents="here is some input\nmore",
                        wrapper=wrapper)
                    ],
                wrapper=wrapper)
        wrapper.run_docs(node)
        doc = node.children[0]
        assert str(doc.output()) == """\
line 1 has 19 chars
line 2 has 4 chars
"""

def test_pandoc_filter_odt():
    with wrap() as wrapper:
        node = DocNode("hello.md|pandoc",
                contents = "hello",
                pandoc = { "ext" : ".odt"},
                wrapper=wrapper)
        wrapper.run_docs(node)
        wrapper.report()
        assert os.path.exists("output/hello.odt")

def test_pandoc_filter_pdf():
    with wrap() as wrapper:
        node = DocNode("hello.md|pandoc",
                contents = "hello",
                pandoc = { "ext" : ".pdf"},
                wrapper=wrapper)
        wrapper.run_docs(node)
        wrapper.report()
        assert os.path.exists("output/hello.pdf")

def test_pandoc_filter_txt():
    with wrap() as wrapper:
        node = DocNode("hello.md|pandoc",
                contents = "hello",
                pandoc = { "ext" : ".txt"},
                wrapper=wrapper)
        wrapper.run_docs(node)
        wrapper.report()
        doc = node.children[0]
        assert os.path.exists("output/hello.txt")
        assert str(doc.output()) == 'hello\n'

R_SECTIONS = """\
### @export "assign-vars"
x <- 6
y <- 7

### @export "multiply"
x * y
"""

def test_rint_mock():
    with wrap() as wrapper:
        node = DocNode("example.R|idio|rintmock",
                contents=R_SECTIONS,
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().is_cached()
        assert doc.output().as_sectioned()['assign-vars'] == "> x <- 6\n> y <- 7\n> \n"
        assert doc.output().as_sectioned()['multiply'] == "> x * y\n[1] 42\n> \n"

def test_ht_latex():
    assert_output_cached("htlatex", LATEX, ext=".tex")

def test_r_batch():
    assert_output('rout', 'print(1+1)', "[1] 2\n")

def test_r_int_batch():
    assert_output('rintbatch', '1+1', "> 1+1\n[1] 2\n> \n")

def test_ragel_ruby_filter():
    assert_in_output('rlrb', RAGEL, "_keys = _hello_and_welcome_key_offsets[cs]", ext=".rl")

def test_ps2pdf_filter():
    with wrap() as wrapper:
        node = DocNode("hello.ps|ps2pdf",
                contents = PS,
                wrapper=wrapper)
        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().is_cached()
        assert doc.output().filesize() > 1000

def test_html2pdf_filter():
    assert_output_cached("html2pdf", "<p>hello</p>", min_filesize=1000)

def test_dot_filter():
    assert_output_cached("dot", "digraph { a -> b }", min_filesize=1000, ext=".dot")

def test_pdf2img_filter():
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        node = DocNode("example.pdf|pdf2img",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().is_cached()
        assert doc.output().filesize() > 1000

def test_pdf2jpg_filter():
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        node = DocNode("example.pdf|pdf2jpg",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().is_cached()

def test_bw_filter():
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        node = DocNode("example.pdf|bw",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().is_cached()

def test_pdfcrop_filter():
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        node = DocNode("example.pdf|pdfcrop|pdfinfo",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().is_cached()

def test_asciidoc_filter():
    assert_in_output("asciidoc", "hello", """<div class="paragraph"><p>hello</p></div>""")

def test_pandoc_filter():
    assert_output("pandoc", "hello", "<p>hello</p>\n", ext=".md")

def test_espeak_filter():
    assert_output_cached("espeak", "hello", min_filesize = 1000)

PS = """%!PS
1.00000 0.99083 scale
/Courier findfont 12 scalefont setfont
0 0 translate
/row 769 def
85 {/col 18 def 6 {col row moveto (Hello World)show /col col 90 add def}
repeat /row row 9 sub def} repeat
showpage save restore"""

RD = """
 \\name{load}
     \\alias{load}
     \\title{Reload Saved Datasets}
     \description{
       Reload the datasets written to a file with the function
       \code{save}.
     }
"""

RAGEL = """%%{
  machine hello_and_welcome;
  main := ( 'h' @ { puts "hello world!" }
          | 'w' @ { puts "welcome" }
          )*;
}%%
  data = 'whwwwwhw'
  %% write data;
  %% write init;
  %% write exec;
"""

LATEX = """\
\documentclass{article}
\\title{Hello, World!}
\\begin{document}
\maketitle
Hello!
\end{document}
"""

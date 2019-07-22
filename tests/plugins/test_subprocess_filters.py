from dexy.doc import Doc
from dexy.wrapper import Wrapper
from nose.exc import SkipTest
from tests.plugins.test_pexpect_filters import SCALA
from tests.utils import TEST_DATA_DIR
from tests.utils import assert_in_output
from tests.utils import assert_output
from tests.utils import assert_output_cached
from tests.utils import wrap
import os
import shutil

C_HELLO_WORLD = """#include <stdio.h>

int main()
{
    printf("HELLO, world\\n");
}
"""

def test_mkdirs():
    with wrap() as wrapper:
        doc = Doc("hello.c|c",
                wrapper,
                contents = C_HELLO_WORLD,
                c = {'mkdir' : 'foo', 'mkdirs' : ['bar', 'baz']}
                )
        wrapper.run_docs(doc)
        dirs = os.listdir(doc.filters[-1].workspace())
        assert 'foo' in dirs
        assert 'bar' in dirs
        assert 'baz' in dirs

def test_taverna():
    raise SkipTest()
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'simple_python_example_285475.t2flow')
        shutil.copyfile(orig, 'simple-python.t2flow')
        node = Doc("simple-python.t2flow|taverna",
                wrapper)
        wrapper.run_docs(node)

PYIN_CONTENTS = """import sys
i = 0
while True:
    i += 1
    line = sys.stdin.readline()
    if not line:
        break
    print("line %s has %s chars" % (i, len(line)))
"""

def test_scalac():
    assert_output('scala', SCALA, "Hello, world!\n", ext=".scala", basename="HelloWorld")

def test_python_input():
    with wrap() as wrapper:
        node = Doc("hello.py|pyin",
                wrapper,
                [
                    Doc("input.in",
                        wrapper,
                        [],
                        contents="here is some input\nmore")
                    ],
                contents=PYIN_CONTENTS
                )
        wrapper.run_docs(node)
        assert str(node.output_data()) == """\
line 1 has 19 chars
line 2 has 4 chars
"""

def test_pandoc_filter_odt():
    # TODO Why isn't this checking for inactive filters?
    with wrap() as wrapper:
        node = Doc("hello.md|pandoc",
                wrapper,
                [],
                contents = "hello",
                pandoc = { "ext" : ".odt"}
                )
        wrapper.run_docs(node)
        wrapper.report()
        assert os.path.exists("output/hello.odt")

def test_pandoc_filter_pdf():
    with wrap() as wrapper:
        node = Doc("hello.md|pandoc",
                wrapper,
                [],
                contents = "hello",
                pandoc = { "ext" : ".pdf"}
                )
        wrapper.run_docs(node)
        wrapper.report()
        assert os.path.exists("output/hello.pdf")

def test_pandoc_filter_txt():
    with wrap() as wrapper:
        node = Doc("hello.md|pandoc",
            wrapper, [],
            contents = "hello",
            pandoc = { "ext" : ".txt"},
            )
        wrapper.run_docs(node)
        wrapper.report()
        assert os.path.exists("output/hello.txt")
        assert str(node.output_data()) == 'hello\n\n'

R_SECTIONS = """\
### @export "assign-vars"
x <- 6
y <- 7

### @export "multiply"
x * y
"""

def test_rint_mock():
    with wrap() as wrapper:
        node = Doc("example.R|idio|rintmock",
                wrapper,
                [],
                contents=R_SECTIONS
                )

        wrapper.run_docs(node)
        assert node.output_data().is_cached()
        assert str(node.output_data()['assign-vars']) == "> x <- 6\n> y <- 7\n> \n"
        assert str(node.output_data()['multiply']) == "> x * y\n[1] 42\n> \n"

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
        node = Doc("hello.ps|ps2pdf",
                wrapper, [],
                contents = PS)
        wrapper.run_docs(node)
        assert node.output_data().is_cached()
        assert node.output_data().filesize() > 1000

def test_html2pdf_filter():
    assert_output_cached("html2pdf", "<p>hello</p>", min_filesize=1000)

def test_dot_filter():
    assert_output_cached("dot", "digraph { a -> b }", min_filesize=1000, ext=".dot")

def test_pdf2img_filter():
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        wrapper=Wrapper()
        node = Doc("example.pdf|pdf2img", wrapper)
        wrapper.run_docs(node)
        assert node.output_data().is_cached()
        assert node.output_data().filesize() > 1000

def test_pdf2jpg_filter():
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        wrapper=Wrapper()
        node = Doc("example.pdf|pdf2jpg", wrapper)

        wrapper.run_docs(node)
        assert node.output_data().is_cached()

def test_bw_filter():
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        wrapper=Wrapper()
        node = Doc("example.pdf|bw", wrapper)

        wrapper.run_docs(node)
        assert node.output_data().is_cached()

def test_pdfcrop_filter():
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        wrapper=Wrapper()
        node = Doc("example.pdf|pdfcrop|pdfinfo", wrapper)

        wrapper.run_docs(node)
        assert node.output_data().is_cached()

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

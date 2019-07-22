from tests.utils import assert_output
from tests.utils import assert_in_output
from tests.utils import wrap
from dexy.doc import Doc

rst_meta = """
==========
Main Title
==========

---
Foo
---

:Author: J Random Hacker
:Authors: Bert & Ernie
:Contact: jrh@example.com
:Date: 2002-08-18
:Status: Work In Progress
:Version: 1
:Filename: $RCSfile$
:Copyright: This document has been placed in the public domain.

Here's some content.

"""
def test_rst_meta():
    with wrap() as wrapper:
        node = Doc("example.rst|rstmeta",
                wrapper, 
                [],
                contents = rst_meta
                )
        wrapper.run_docs(node)

        assert node.setting('author') == "J Random Hacker"
        assert node.setting('authors') == "Bert & Ernie"
        assert node.setting('subtitle') == "Foo"
        assert node.setting('title') == "Main Title"
        assert node.setting('date') == "2002-08-18"
        assert node.setting('status') == "Work In Progress"
        assert node.setting('version') == "1"
        assert node.setting('copyright') == "This document has been placed in the public domain."

RST = """
* a bullet point using "*"

  - a sub-list using "-"

    + yet another sub-list

  - another item
"""

def test_rst2odt():
    with wrap() as wrapper:
        node = Doc("example.txt|rst2odt",
                wrapper,
                [],
                contents=RST)
        wrapper.run_docs(node)
        assert node.output_data().filesize() > 8000

def test_rst2xml():
    assert_in_output('rst2xml', RST, """<list_item><paragraph>a sub-list using "-"</paragraph><bullet_list bullet="+"><list_item>""")

def test_rst2latex():
    assert_in_output('rst2latex', RST, "\item a bullet point using")
    assert_in_output('rst2latex', RST, "\\begin{document}")

def test_rst2html():
    assert_in_output('rst2html', RST, "<html xmlns")
    assert_in_output('rst2html', RST, "<li>a bullet point using &quot;*&quot;<ul>")

def test_rest_to_tex():
    with wrap() as wrapper:
        node = Doc("example.txt|rstbody",
                wrapper,
                [],
                contents=RST,
                rstbody={"ext" : ".tex"}
                )

        wrapper.run_docs(node)
        assert "\\begin{itemize}" in str(node.output_data())

def test_rest_to_html():
    expected = """\
<ul class="simple">
<li>a bullet point using &quot;*&quot;<ul>
<li>a sub-list using &quot;-&quot;<ul>
<li>yet another sub-list</li>
</ul>
</li>
<li>another item</li>
</ul>
</li>
</ul>
"""

    assert_output('rstbody', RST, expected)

def test_rstbody_latex():
    with wrap() as wrapper:
        node = Doc("example.rst|rstbody",
                wrapper, 
                [],
                rstbody = { 'ext' : '.tex' },
                contents = RST
                )
        wrapper.run_docs(node)
        output = str(node.output_data())
        assert "\\begin{itemize}" in output

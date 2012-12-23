from dexy.tests.utils import assert_output
from dexy.tests.utils import assert_in_output
from dexy.tests.utils import wrap
from dexy.node import DocNode

RST = """
* a bullet point using "*"

  - a sub-list using "-"

    + yet another sub-list

  - another item
"""

def test_rst2odt():
    with wrap() as wrapper:
        node = DocNode("example.txt|rst2odt",
                contents=RST,
                wrapper=wrapper)
        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().filesize() > 8000

def test_rst2xml():
    assert_in_output('rst2xml', RST, """<list_item><paragraph>a sub-list using "-"</paragraph><bullet_list bullet="+"><list_item>""")

def test_rst2latex():
    assert_in_output('rst2latex', RST, "\item a bullet point using ``*''")
    assert_in_output('rst2latex', RST, "\\begin{document}")

def test_rst2html():
    assert_in_output('rst2html', RST, "<html xmlns")
    assert_in_output('rst2html', RST, "<li>a bullet point using &quot;*&quot;<ul>")

def test_rest_to_tex():
    with wrap() as wrapper:
        node = DocNode("example.txt|rst",
                contents=RST,
                rst={"ext" : ".tex"},
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().as_text() == """\
%
\\begin{itemize}

\item a bullet point using ``*''
%
\\begin{itemize}

\item a sub-list using ``-''
%
\\begin{itemize}

\item yet another sub-list

\end{itemize}

\item another item

\end{itemize}

\end{itemize}
"""

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

    assert_output('rst', RST, expected)

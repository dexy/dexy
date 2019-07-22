from tests.utils import runfilter
from tests.utils import wrap
from dexy.doc import Doc

XML = """
<element id="foo">foo</element>
"""

def test_xxml():
    with runfilter("xxml", XML) as doc:
        assert doc.output_data()['foo:source'] == '<element id="foo">foo</element>'
        assert doc.output_data()['foo:text'] == 'foo'
        assert '<div class="highlight">' in doc.output_data()['foo:html-source']

def test_xxml_no_pygments():
    with wrap() as wrapper:
        doc = Doc(
                "example.xml|xxml",
                wrapper,
                [],
                contents = XML,
                xxml = { 'pygments' : False, 'ext' : '.sqlite3' }
                )
        wrapper.run_docs(doc)

        assert "foo:source" in list(doc.output_data().keys())
        assert not "foo:html-source" in list(doc.output_data().keys())
        assert not "foo:latex-source" in list(doc.output_data().keys())

from dexy.tests.utils import runfilter

XML = """
<element id="foo">foo</element>
"""

def test_xxml():
    with runfilter("xxml", XML) as doc:
        assert doc.output_data()['foo:source'] == '<element id="foo">foo</element>'
        assert doc.output_data()['foo:text'] == 'foo'
        assert '<div class="highlight">' in doc.output_data()['foo:html-source']


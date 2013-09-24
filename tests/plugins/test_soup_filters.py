from tests.utils import runfilter

def test_markdown_output():
    md = """
# foo

This is the foo section.

# bar

This is the bar section.

## barbaz

This is the barbaz section.

"""

    with runfilter('markdown|soups', md) as doc:
        data = doc.output_data()

        assert data.keys() == [u'foo', u'bar', u'barbaz']

        assert data['foo']['level'] == 1
        assert data['bar']['level'] == 1
        assert data['barbaz']['level'] == 2

        assert data['foo']['id'] == 'foo'
        assert data['bar']['id'] == 'bar'
        assert data['barbaz']['id'] == 'barbaz'

        assert data['barbaz']['contents'] == """<h2 id="barbaz">barbaz</h2>\n<p>This is the barbaz section.</p>"""

html = """
<p>Text before the first section</p>
<H1>The First Named Section</H1>
<p>Some content in the first section.</p>
<h2>Nested In First Section</h2>
<p>Content in the nested section.</p>
<ul>
<li>list item the first</li>
<li>list item the second</li>
</ul>
<h1>The 2nd Section</h1>
<p>foo.</p>
"""

def test_soup_sections_filter():
    with runfilter('soups', html, ext='.html') as doc:
        data = doc.output_data()

        assert data.keys() == [u'Initial Anonymous Section', u'The First Named Section',
                u'Nested In First Section', u'The 2nd Section']


        initial_section = data['Initial Anonymous Section']
        assert initial_section['contents'] == u"<p>Text before the first section</p>"
        assert initial_section['level'] == 1

        first_section = data["The First Named Section"]
        assert first_section['contents'] == u'<h1 id="the-first-named-section">The First Named Section</h1>\n<p>Some content in the first section.</p>'
        assert first_section['level'] == 1

        nested_section = data["Nested In First Section"]
        assert nested_section['level'] == 2
        assert nested_section['contents'] == """<h2 id="nested-in-first-section">Nested In First Section</h2>
<p>Content in the nested section.</p>
<ul>
<li>list item the first</li>
<li>list item the second</li>
</ul>"""

        final_section = data["The 2nd Section"]
        assert final_section['level'] == 1
        assert final_section['contents'] == u"""<h1 id="the-2nd-section">The 2nd Section</h1>\n<p>foo.</p>"""

def test_no_blank_anonymous_first_section():
    with runfilter('soups', "<h1>first</h1><p>foo</p><h1>second</h1>", ext=".html") as doc:
        assert doc.output_data().keys() == [u'first', u'second']

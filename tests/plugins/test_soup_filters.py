from tests.utils import runfilter

def test_nested_html():
    with runfilter('soups', nested_html) as doc:
        data = doc.output_data()
        assert str(data) == expected
        assert list(data.keys()) == ['First', 'Second', 'Actual Document Contents']

def test_markdown_output():
    with runfilter('markdown|soups', md) as doc:
        data = doc.output_data()

        assert list(data.keys()) == ['foo', 'bar', 'barbaz', 'Actual Document Contents']

        assert data['foo']['level'] == 1
        assert data['bar']['level'] == 1
        assert data['barbaz']['level'] == 2

        assert data['foo']['id'] == 'foo'
        assert data['bar']['id'] == 'bar'
        assert data['barbaz']['id'] == 'barbaz'

def test_soup_sections_filter():
    with runfilter('soups', html, ext='.html') as doc:
        data = doc.output_data()

        assert list(data.keys()) == ['The First Named Section',
                'Nested In First Section', 'The 2nd Section',
                'Actual Document Contents']

        first_section = data["The First Named Section"]
        assert first_section['contents'] == None
        assert first_section['level'] == 1

        nested_section = data["Nested In First Section"]
        assert nested_section['level'] == 2
        assert first_section['contents'] == None

        final_section = data["The 2nd Section"]
        assert final_section['level'] == 1
        assert final_section['contents'] == None

        contents_section = data['Actual Document Contents']
        assert contents_section['level'] == 1

def test_no_blank_anonymous_first_section():
    with runfilter('soups', "<h1>first</h1><p>foo</p><h1>second</h1>", ext=".html") as doc:
        assert list(doc.output_data().keys()) == ['first', 'second', 'Actual Document Contents']

nested_html = """<div>
<h1>First</h1>
<div>
<h2>Second</h2>
</div>
</div>"""

expected = """<div>
<h1 id="first">First</h1>
<div>
<h2 id="second">Second</h2>
</div>
</div>"""

md = """# foo

This is the foo section.

# bar

This is the bar section.

## barbaz

This is the barbaz section.

"""

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

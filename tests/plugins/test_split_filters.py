from tests.utils import wrap
from dexy.doc import Doc

def test_split_html_filter():
    with wrap() as wrapper:
        contents="""
        <p>This is at the top.</p>
        <!-- split "index" -->
        index page content only
        <!-- split "a-page" -->
        some content on a page
        <!-- split "another-page" -->
        This is information about "another-page" which should appear on the index page.
        <!-- content -->
        some content on another page
        <!-- footer -->
        footer on index page only
        <!-- endsplit -->
        bottom
        """

        node = Doc("subdir/example.html|splithtml", wrapper, [], contents=contents)
        wrapper.run_docs(node)

        assert node.children[0].key == "subdir/a-page.html"
        assert node.children[1].key == "subdir/another-page.html"

        od = str(node.output_data())

        assert "<p>This is at the top.</p>" in od
        assert 'index page content only' in od
        assert '<a href="a-page.html">' in od
        assert '<a href="another-page.html">' in od
        assert "This is information about \"another-page\"" in od
        assert "bottom" in od

        od = str(node.children[0].output_data())
        assert "<p>This is at the top.</p>" in od
        assert not 'index page content only' in od
        assert "some content on a page" in od
        assert "bottom" in od

        od = str(node.children[1].output_data())
        assert "<p>This is at the top.</p>" in od
        assert "some content on another page" in od
        assert "bottom" in od

def test_split_html_additional_filters():
    with wrap() as wrapper:
        contents="""
        <p>This is at the top.</p>
        <!-- split "a-page" -->
        some content on a page
        <!-- split "another-page" -->
        some content on another page
        <!-- endsplit -->
        bottom
        """

        node = Doc("example.html|splithtml",
                wrapper,
                [],
                contents=contents,
                splithtml = { "keep-originals" : False, "additional-doc-filters" : "processtext" },
              )
        wrapper.run_docs(node)

        assert node.children[0].key == "a-page.html|processtext"
        assert node.children[1].key == "another-page.html|processtext"

        od = str(node.output_data())
        assert "<p>This is at the top.</p>" in od
        assert '<a href="a-page.html">' in od
        assert '<a href="another-page.html">' in od
        assert "bottom" in od

        a_page = node.children[0]
        a_page_data = str(a_page.output_data())
        assert "<p>This is at the top.</p>" in a_page_data
        assert "some content on a page" in a_page_data
        assert "bottom" in a_page_data
        assert "Dexy processed the text" in a_page_data

        another_page = node.children[1]
        another_page_data = str(another_page.output_data())
        assert "<p>This is at the top.</p>" in another_page_data
        assert "some content on another page" in another_page_data
        assert "bottom" in another_page_data
        assert "Dexy processed the text" in another_page_data

from dexy.tests.utils import assert_output

def test_pandoc_filter():
    assert_output("pandoc", "hello", "<p>hello</p>\n", ext=".md")

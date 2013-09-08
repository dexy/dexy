from tests.utils import assert_in_output

def test_easyhtml_filter():
    some_html = "<p>This is some HTML</p>"
    assert_in_output("easyhtml", some_html, some_html, ".html")
    assert_in_output("easyhtml", some_html, "<html>", ".html")

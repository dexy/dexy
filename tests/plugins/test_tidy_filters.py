from tests.utils import runfilter
from dexy.exceptions import UserFeedback

min_valid_html = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<TITLE></TITLE>
"""

invalid_html = "<html></html>"

def test_tidyerrors():
    with runfilter("tidyerrors", invalid_html, ext=".html") as doc:
        output = str(doc.output_data())
        assert "missing <!DOCTYPE>" in output
        assert "inserting missing 'title'" in output

def test_htmltidy_throws_error_on_invalid_html():
    try:
        with runfilter("htmltidy", invalid_html, ext=".html"):
            assert False, "should not get here"
    except UserFeedback as e:
        assert "missing <!DOCTYPE>" in str(e)
        assert "inserting missing 'title'" in str(e)

def test_htmltidy():
    with runfilter("htmltidy", min_valid_html, ext=".html") as doc:
        output = str(doc.output_data())
        assert "<body>" in output

def test_htmlcheck_on_valid_html():
    with runfilter("tidycheck", min_valid_html, ext=".html") as doc:
        output = str(doc.output_data())
        assert output == min_valid_html

def test_htmlcheck_on_invalid_html():
    try:
        with runfilter("tidycheck", invalid_html, ext=".html"):
            assert False, "should not get here"
    except UserFeedback as e:
        assert "missing <!DOCTYPE>" in str(e)
        assert "inserting missing 'title'" in str(e)

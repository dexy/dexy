from dexy.common import OrderedDict
from dexy.doc import Doc
from dexy.tests.utils import assert_output
from dexy.tests.utils import wrap

def test_join_filter():
    contents = OrderedDict()
    contents['1'] = "section one"
    contents['2'] = "section two"

    assert_output("join", contents, "section one\nsection two")

def test_head_filter():
    assert_output("head", "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n", "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n")

def test_word_wrap_filter():
    with wrap() as wrapper:
        doc = Doc("example.txt|wrap", contents="this is a line of text", wrap={"width" : 5}, wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()
        assert doc.output().data() == "this\nis a\nline\nof\ntext"

def test_lines_filter():
    expected = OrderedDict()
    expected['1'] = "line one"
    expected['2'] = "line two"

    assert_output("lines", "line one\nline two", expected)

def test_ppjson_filter():
    assert_output(
            "ppjson",
            '{"foo" :123, "bar" :456}',
            """{\n    "bar": 456, \n    "foo": 123\n}"""
            )

def test_start_space_filter():
    assert_output("startspace", "abc\ndef", " abc\n def")

def test_tags_filter():
    with wrap() as wrapper:
        doc = Doc("example.txt|tags", contents="<p>the text</p>", tags={"tags" : ["html", "body"]}, wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()
        assert doc.output().data() == "<html><body>\n<p>the text</p>\n</body></html>"


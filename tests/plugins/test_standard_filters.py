from dexy.doc import Doc
from tests.utils import assert_output
from tests.utils import wrap
import json
import os

def test_header_footer_filters():
    with wrap() as wrapper:
        os.makedirs('subdir/subsubdir')
        node = Doc("subdir/file.txt|hd|ft",
                wrapper,
                [
                    Doc("_header.txt", wrapper, [], contents="This is a header in parent dir."),
                    Doc("subdir/_header.txt|jinja", wrapper, [], contents="This is a header."),
                    Doc("subdir/_footer.txt|jinja", wrapper, [], contents="This is a footer."),
                    Doc("subdir/subsubdir/_header.txt", wrapper, [], contents="This is a header in a subdirectory.")
                    ],
                contents="These are main contents."
                )

        wrapper.run_docs(node)
        assert str(node.output_data()) == "This is a header.\nThese are main contents.\nThis is a footer."

def test_join_filter():
    contents = json.loads("""[{},
    {"name" : "1", "contents" : "section one" },
    {"name" : "2", "contents" : "section two" }
    ]""")
    assert_output("join", contents, "section one\nsection two")

def test_head_filter():
    assert_output("head", "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n", "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n")

def test_word_wrap_filter():
    with wrap() as wrapper:
        node = Doc("example.txt|wrap", wrapper, [], contents="this is a line of text", wrap={"width" : 5})
        wrapper.run_docs(node)
        assert str(node.output_data()) == "this\nis a\nline\nof\ntext"

def test_lines_filter():
    expected = {}
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
    o = {}
    o['1'] = " abc\n def"
    assert_output("startspace", "abc\ndef", o)

def test_tags_filter():
    with wrap() as wrapper:
        node = Doc("example.txt|tags", wrapper, [], contents="<p>the text</p>", tags={"tags" : ["html", "body"]})
        wrapper.run_docs(node)
        assert str(node.output_data()) == "<html><body>\n<p>the text</p>\n</body></html>"


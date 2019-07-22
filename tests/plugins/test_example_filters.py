from dexy.doc import Doc
from tests.utils import assert_output
from tests.utils import runfilter
from tests.utils import wrap

def test_process_text_filter():
    assert_output("processtext", "hello", "Dexy processed the text 'hello'")

def test_process_method():
    assert_output("process", "hello", "Dexy processed the text 'hello'")

def test_process_method_manual_write():
    assert_output("processmanual", "hello", "Dexy processed the text 'hello'")

def test_process_method_with_dict():
    assert_output("processwithdict", "hello", {'1' : "Dexy processed the text 'hello'"})

def test_add_new_document():
    with runfilter("newdoc", "hello") as doc:
        assert doc.children[-1].key == "subdir/newfile.txt|processtext"
        assert str(doc.output_data()) == "we added a new file"

        assert "doc:subdir/example.txt|newdoc" in doc.wrapper.nodes
        assert "doc:subdir/newfile.txt|processtext" in doc.wrapper.nodes

def test_key_value_example():
    with wrap() as wrapper:
        doc = Doc(
                "hello.txt|keyvalueexample",
                wrapper,
                [],
                contents="hello"
                )

        wrapper.run_docs(doc)

        print(str(doc.output_data()))

        assert doc.output_data()["foo"] == "bar"
        assert str(doc.output_data()) == "KeyValue('hello.txt|keyvalueexample')"

def test_access_other_documents():
    with wrap() as wrapper:
        node = Doc("hello.txt|newdoc", wrapper, [], contents="hello")
        parent = Doc("test.txt|others",
                wrapper,
                [node],
                contents="hello"
                )
        wrapper.run_docs(parent)

        expected_items = [
            "Here is a list of previous docs in this tree (not including test.txt|others).",
            "newfile.txt|processtext (0 children, 0 inputs, length 33)",
            "hello.txt|newdoc (1 children, 0 inputs, length 19)"
            ]

        output = str(parent.output_data())

        for item in expected_items:
            assert item in output

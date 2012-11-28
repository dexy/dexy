from dexy.artifact import InitialVirtualArtifact, FilterArtifact
from dexy.doc import Doc
from dexy.tests.utils import assert_output
from dexy.tests.utils import runfilter
from dexy.tests.utils import wrap

def test_process_text_filter():
    assert_output("processtext", "hello", "Dexy processed the text 'hello'")

def test_process_text_to_dict_filter():
    assert_output("processtexttodict", "hello", {'1': "Dexy processed the text 'hello'"})

def test_process_dict_filter():
    assert_output("processdict", {'1': 'hello'}, {'1': "Dexy processed the text 'hello'"})

def test_process_method():
    assert_output("process", "hello", "Dexy processed the text 'hello'")

def test_process_method_manual_write():
    assert_output("processmanual", "hello", "Dexy processed the text 'hello'")

def test_process_method_with_dict():
    assert_output("processwithdict", "hello", {'1' : "Dexy processed the text 'hello'"})

def test_add_new_document():
    with runfilter("newdoc", "hello") as doc:
        assert doc.children[-1].key == "subdir/newfile.txt|processtext"
        assert doc.output().data() == "we added a new file"
        assert isinstance(doc.children[-1], Doc)
        assert doc.children[-1].output().data() == "Dexy processed the text 'newfile'"

        assert "Doc:subdir/example.txt|newdoc" in doc.wrapper.batch.lookup_table
        assert "Doc:subdir/newfile.txt|processtext" in doc.wrapper.batch.lookup_table

def test_key_value_example():
    with wrap() as wrapper:
        doc = Doc(
                "hello.txt|keyvalueexample",
                contents="hello",
                wrapper=wrapper
                )

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "foo: bar"

def test_access_other_documents():
    with wrap() as wrapper:
        doc = Doc("hello.txt|newdoc", contents="hello", wrapper=wrapper)
        parent = Doc("test.txt|others", doc, contents="hello", wrapper=wrapper)
        wrapper.run_docs(parent)

        expected_items = [
            "Here is a list of previous docs in this tree (not including test.txt|others).",
            "hello.txt|newdoc (3 children, 2 artifacts, length 19)",
            "newfile.txt|processtext (2 children, 2 artifacts, length 33)"
            ]

        output = parent.output().as_text()

        for item in expected_items:
            assert item in output

def test_doc_children_artifacts():
    with wrap() as wrapper:
        doc = Doc("hello.txt|newdoc", contents="hello", wrapper=wrapper)
        parent = Doc("parent.txt|process", doc, contents="hello", wrapper=wrapper)

        wrapper.root_nodes = [parent]

        doc.populate()
        parent.populate()

        assert len(doc.children) == 2
        assert isinstance(doc.children[0], InitialVirtualArtifact)
        assert isinstance(doc.children[1], FilterArtifact)

        assert len(doc.artifacts) == 2
        assert isinstance(doc.artifacts[0], InitialVirtualArtifact)
        assert isinstance(doc.artifacts[1], FilterArtifact)

        assert len(parent.children) == 3

        assert isinstance(parent.children[0], Doc)
        assert parent.children[0] == doc

        assert isinstance(parent.children[1], InitialVirtualArtifact)
        assert isinstance(parent.children[2], FilterArtifact)

        assert len(parent.artifacts) == 2
        assert isinstance(parent.artifacts[0], InitialVirtualArtifact)
        assert isinstance(parent.artifacts[1], FilterArtifact)

        doc = Doc("hello.txt|newdoc", contents="hello", wrapper=wrapper)
        parent = Doc("parent.txt|process", doc, contents="hello", wrapper=wrapper)

        wrapper.run_docs(parent)

        assert len(doc.children) == 3
        assert isinstance(doc.children[0], InitialVirtualArtifact)
        assert isinstance(doc.children[1], FilterArtifact)
        assert isinstance(doc.children[2], Doc)

        assert len(doc.artifacts) == 2

        assert len(parent.children) == 3
        assert len(parent.artifacts) == 2

        assert "Doc:hello.txt|newdoc" in wrapper.batch.lookup_table
        assert "Doc:parent.txt|process" in wrapper.batch.lookup_table
        assert "Doc:newfile.txt|processtext" in wrapper.batch.lookup_table

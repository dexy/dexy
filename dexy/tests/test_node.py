from dexy.node import Node
from dexy.node import DocNode
from dexy.node import PatternNode
from dexy.task import Task
from dexy.tests.utils import wrap
from dexy.wrapper import Wrapper
import time

def test_node_caching():
    with wrap() as wrapper:
        with open("hello.py", "w") as f:
            f.write("print 1+2\n")

        with open("doc.txt", "w") as f:
            f.write("1 + 1 = {{ d['hello.py|py'] }}")

        hello_py = DocNode("hello.py|py", wrapper=wrapper)

        doc_txt = DocNode("doc.txt|jinja",
                inputs = [hello_py],
                wrapper=wrapper)

        wrapper.run_docs(doc_txt)

        hello_py_doc = hello_py.children[0]
        doc_txt_doc = doc_txt.children[0]

        assert str(doc_txt_doc.output()) == "1 + 1 = 3\n"
        assert str(hello_py_doc.output()) == "3\n"

        assert hello_py_doc.final_artifact.content_source == 'generated'
        assert doc_txt_doc.final_artifact.content_source == 'generated'

        wrapper = Wrapper()

        hello_py = DocNode("hello.py|py", wrapper=wrapper)

        doc_txt = DocNode("doc.txt|jinja",
                inputs = [hello_py],
                wrapper=wrapper)

        wrapper.run_docs(doc_txt)

        hello_py_doc = hello_py.children[0]
        doc_txt_doc = doc_txt.children[0]

        assert hello_py_doc.final_artifact.content_source == 'cached'
        assert doc_txt_doc.final_artifact.content_source == 'cached'

        with open("doc.txt", "w") as f:
            f.write("1 + 1 = {{ d['hello.py|py'] }}\n")

        wrapper = Wrapper()

        hello_py = DocNode("hello.py|py", wrapper=wrapper)

        doc_txt = DocNode("doc.txt|jinja",
                inputs = [hello_py],
                wrapper=wrapper)

        wrapper.run_docs(doc_txt)

        hello_py_doc = hello_py.children[0]
        doc_txt_doc = doc_txt.children[0]

        assert hello_py_doc.final_artifact.content_source == 'cached'
        assert doc_txt_doc.final_artifact.content_source == 'generated'

        time.sleep(2)

        with open("hello.py", "w") as f:
            f.write("print 1+1\n")

        wrapper = Wrapper()

        hello_py = DocNode("hello.py|py", wrapper=wrapper)

        doc_txt = DocNode("doc.txt|jinja",
                inputs = [hello_py],
                wrapper=wrapper)

        wrapper.run_docs(doc_txt)

        hello_py_doc = hello_py.children[0]
        doc_txt_doc = doc_txt.children[0]

        assert hello_py_doc.final_artifact.content_source == 'generated'
        assert doc_txt_doc.final_artifact.content_source == 'generated'

def test_node_init():
    node = Node("foo.txt")
    assert node.key == "foo.txt"

def test_node_init_with_inputs():
    node = Node("foo.txt", inputs=[Node("bar.txt")])
    assert node.key == "foo.txt"
    assert node.inputs[0].key == "bar.txt"

    expected = {
            0 : "bar.txt",
            1 : "foo.txt" 
        }

    for i, n in enumerate(node.walk_inputs()):
        assert expected[i] == n.key

def test_doc_node_populate():
    with wrap() as wrapper:
        node = Task.create('doc', "foo.txt", wrapper=wrapper)
        node.populate()
        assert node.key_with_class() == "DocNode:foo.txt"
        assert node.children[0].key_with_class() == "Doc:foo.txt"

def test_doc_node_with_filters():
    with wrap() as wrapper:
        node = Task.create('doc', "foo.txt|outputabc", wrapper=wrapper)
        node.populate()
        assert node.key_with_class() == "DocNode:foo.txt|outputabc"
        assert node.children[0].key_with_class() == "Doc:foo.txt|outputabc"

def test_pattern_node():
    with wrap() as wrapper:
        with open("foo.txt", "w") as f:
            f.write("foo!")

        with open("bar.txt", "w") as f:
            f.write("bar!")

        wrapper.setup_batch()

        node = PatternNode("*.txt", foo="bar", wrapper=wrapper)
        node.populate()
        assert node.args['foo'] == 'bar'
        assert len(node.children) == 2

        for child in node.children:
            assert child.__class__.__name__ == "Doc"
            assert child.args['foo'] == 'bar'
            assert child.key_with_class() in ["Doc:foo.txt", "Doc:bar.txt"]
            assert child.filters == []

def test_pattern_node_multiple_filters():
    with wrap() as wrapper:
        with open("foo.txt", "w") as f:
            f.write("foo!")

        wrapper.setup_batch()

        node = PatternNode("*.txt|dexy|dexy|dexy", wrapper=wrapper)
        node.populate()
        doc = node.children[0]
        assert doc.key == "foo.txt|dexy|dexy|dexy"
        assert doc.filters == ['dexy', 'dexy', 'dexy']
        assert doc.node == node

def test_pattern_node_one_filter():
    with wrap() as wrapper:
        with open("foo.txt", "w") as f:
            f.write("foo!")

        wrapper.setup_batch()

        node = PatternNode("*.txt|dexy", wrapper=wrapper)
        node.populate()
        doc = node.children[0]
        assert doc.key == "foo.txt|dexy"
        assert doc.filters == ['dexy']
        assert doc.node == node

        assert doc.children[0].key_with_class() == "InitialArtifact:foo.txt(|dexy)"
        assert doc.children[1].key_with_class() == "FilterArtifact:foo.txt|dexy"

        assert doc.children[0].state == "populated"
        assert doc.children[1].state == "populated"

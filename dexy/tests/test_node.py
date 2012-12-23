from dexy.node import Node
from dexy.node import PatternNode
from dexy.task import Task
from dexy.tests.utils import wrap

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

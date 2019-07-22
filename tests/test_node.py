from dexy.doc import Doc
from dexy.node import Node
from dexy.node import PatternNode
from dexy.wrapper import Wrapper
from tests.utils import wrap
import dexy.doc
import dexy.node
import os
import time

def test_create_node():
    with wrap() as wrapper:
        node = dexy.node.Node.create_instance(
                "doc",
                "foo.txt",
                wrapper,
                [],
                # kwargs
                foo='bar',
                contents="these are contents"
                )

        assert node.__class__ == dexy.doc.Doc
        assert node.args['foo'] == 'bar'
        assert node.wrapper == wrapper
        assert node.inputs == []
        assert len(node.hashid) == 32

def test_node_arg_caching():
    with wrap() as wrapper:
        wrapper.nodes = {}
        node = dexy.node.Node("foo", wrapper, [], foo='bar', baz=123)
        wrapper.add_node(node)

        assert node.hashid == 'acbd18db4cc2f85cedef654fccc4a4d8'
        assert node.args['foo'] == 'bar'
        assert node.args['baz'] == 123
        assert node.sorted_arg_string() == '[["baz", 123], ["foo", "bar"]]'

        assert os.path.exists(wrapper.artifacts_dir)
        assert not os.path.exists(wrapper.node_argstrings_filename())
        wrapper.save_node_argstrings()
        assert os.path.exists(wrapper.node_argstrings_filename())
        wrapper.load_node_argstrings()
        assert not node.check_args_changed()

        node.args['baz'] = 456
        assert node.check_args_changed()
        wrapper.save_node_argstrings()
        wrapper.load_node_argstrings()
        assert not node.check_args_changed()

SCRIPT_YAML = """
script:scriptnode:
    - start.sh|shint
    - middle.sh|shint
    - end.sh|shint
"""

def test_script_node_caching__slow():
    with wrap():
        with open("start.sh", "w") as f:
            f.write("pwd")

        with open("middle.sh", "w") as f:
            f.write("echo `time`")

        with open("end.sh", "w") as f:
            f.write("echo 'done'")

        with open("dexy.yaml", "w") as f:
            f.write(SCRIPT_YAML)

        wrapper1 = Wrapper(log_level="DEBUG")
        wrapper1.run_from_new()

        for node in list(wrapper1.nodes.values()):
            assert node.state == 'ran'

        wrapper2 = Wrapper()
        wrapper2.run_from_new()

        for node in list(wrapper2.nodes.values()):
            assert node.state == 'consolidated'

        time.sleep(1.1)
        with open("middle.sh", "w") as f:
            f.write("echo 'new'")

        wrapper3 = Wrapper()
        wrapper3.run_from_new()

        for node in list(wrapper1.nodes.values()):
            assert node.state == 'ran'

# TODO mock out os.stat to get different mtimes without having to sleep?

def test_node_caching__slow():
    with wrap() as wrapper:
        with open("hello.py", "w") as f:
            f.write("print(1+2)\n")

        with open("doc.txt", "w") as f:
            f.write("1 + 1 = {{ d['hello.py|py'] }}")

        wrapper = Wrapper(log_level='DEBUG')
        hello_py = Doc("hello.py|py", wrapper)
        doc_txt = Doc("doc.txt|jinja",
                wrapper,
                [hello_py]
                )

        wrapper.run_docs(doc_txt)

        assert str(doc_txt.output_data()) == "1 + 1 = 3\n"
        assert str(hello_py.output_data()) == "3\n"

        assert hello_py.state == 'ran'
        assert doc_txt.state == 'ran'

        wrapper = Wrapper(log_level='DEBUG')
        hello_py = Doc("hello.py|py", wrapper)
        doc_txt = Doc("doc.txt|jinja",
                wrapper,
                [hello_py]
                )
        wrapper.run_docs(doc_txt)

        assert hello_py.state == 'consolidated'
        assert doc_txt.state == 'consolidated'

        time.sleep(1.1)
        with open("doc.txt", "w") as f:
            f.write("1 + 1 = {{ d['hello.py|py'] }}\n")

        wrapper = Wrapper(log_level='DEBUG')
        hello_py = Doc("hello.py|py", wrapper)
        doc_txt = Doc("doc.txt|jinja",
                wrapper,
                [hello_py]
                )
        wrapper.run_docs(doc_txt)

        assert hello_py.state == 'consolidated'
        assert doc_txt.state == 'ran'

        time.sleep(1.1)
        with open("hello.py", "w") as f:
            f.write("print(1+1)\n")

        wrapper = Wrapper(log_level='DEBUG')
        hello_py = Doc("hello.py|py", wrapper)
        doc_txt = Doc("doc.txt|jinja",
                wrapper,
                [hello_py]
                )
        wrapper.run_docs(doc_txt)

        assert hello_py.state == 'ran'
        assert doc_txt.state == 'ran'

def test_node_init_with_inputs():
    with wrap() as wrapper:
        node = Node("foo.txt",
                wrapper,
                [Node("bar.txt", wrapper)]
                )
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
        node = Node.create_instance(
                'doc', "foo.txt", wrapper,
                [], contents='foo')

        assert node.key_with_class() == "doc:foo.txt"

def test_doc_node_with_filters():
    with wrap() as wrapper:
        node = Node.create_instance('doc',
                "foo.txt|outputabc", wrapper, [], contents='foo')
        assert node.key_with_class() == "doc:foo.txt|outputabc"

def test_pattern_node():
    with wrap() as wrapper:
        with open("foo.txt", "w") as f:
            f.write("foo!")

        with open("bar.txt", "w") as f:
            f.write("bar!")

        wrapper = Wrapper(log_level='DEBUG')
        wrapper.to_valid()

        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        node = PatternNode("*.txt", 
                wrapper,
                [],
                foo="bar")
        assert node.args['foo'] == 'bar'
        wrapper.run_docs(node)
        assert len(node.children) == 2

        for child in node.children:
            assert child.__class__.__name__ == "Doc"
            assert child.args['foo'] == 'bar'
            assert child.key_with_class() in ["doc:foo.txt", "doc:bar.txt"]
            assert child.filters == []

def test_pattern_node_multiple_filters():
    with wrap() as wrapper:
        with open("foo.txt", "w") as f:
            f.write("foo!")

        wrapper = Wrapper(log_level='DEBUG')
        wrapper.to_valid()

        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        node = PatternNode("*.txt|dexy|dexy|dexy", wrapper=wrapper)
        doc = node.children[0]
        assert doc.key == "foo.txt|dexy|dexy|dexy"
        assert doc.filter_aliases == ['dexy', 'dexy', 'dexy']
        assert doc.parent == node

def test_pattern_node_one_filter():
    with wrap() as wrapper:
        with open("foo.txt", "w") as f:
            f.write("foo!")

        wrapper = Wrapper(log_level='DEBUG')
        wrapper.to_valid()

        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        node = PatternNode("*.txt|dexy", wrapper=wrapper)
        doc = node.children[0]
        assert doc.key == "foo.txt|dexy"
        assert doc.filter_aliases == ['dexy']
        assert doc.parent == node

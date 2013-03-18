from dexy.tests.utils import wrap
from dexy.wrapper import Wrapper
import time
import os
import dexy.doc
import dexy.node

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
        assert isinstance(node.doc_changed, bool)
        assert isinstance(node.args_changed, bool)
        assert isinstance(node.changed(), bool)

def test_node_arg_caching():
    with wrap() as wrapper:
        node = dexy.node.Node("foo", wrapper, [], foo='bar', baz=123)
        assert node.hashid == 'acbd18db4cc2f85cedef654fccc4a4d8'
        assert node.args_filename() == ".cache/acbd18db4cc2f85cedef654fccc4a4d8.args"
        assert node.args['foo'] == 'bar'
        assert node.args['baz'] == 123
        assert node.sorted_arg_string() == '[["baz", 123], ["foo", "bar"]]'

        assert os.path.exists(wrapper.artifacts_dir)
        assert not os.path.exists(node.args_filename())
        node.save_args()
        assert os.path.exists(node.args_filename())
        assert not node.check_args_changed()

        node.args['baz'] = 456
        assert node.check_args_changed()
        node.save_args()
        assert not node.check_args_changed()

        os.remove(node.args_filename())
        assert node.check_args_changed()

SCRIPT_YAML = """
script:scriptnode:
    - start.sh|shint
    - middle.sh|shint
    - end.sh|shint
"""

def test_script_node_caching():
    with wrap() as wrapper:
        with open("start.sh", "w") as f:
            f.write("pwd")

        with open("middle.sh", "w") as f:
            f.write("echo `time`")

        with open("end.sh", "w") as f:
            f.write("echo 'done'")

        with open("dexy.yaml", "w") as f:
            f.write(SCRIPT_YAML)

        wrapper1 = Wrapper()
#        wrapper1.log_level = 'DEBUG'
        wrapper1.setup()
        wrapper1.run()

        tasks = [
            "FilterArtifact:start.sh|shint",
            "FilterArtifact:middle.sh|shint",
            "FilterArtifact:end.sh|shint"
            ]

        for t in tasks:
            assert wrapper1.batch.task(t).content_source == 'generated', "%s should be generated" % t

        wrapper2 = Wrapper()
#        wrapper2.log_level = 'DEBUG'
        wrapper2.setup()
        wrapper2.run()

        for t in tasks:
            assert wrapper2.batch.task(t).content_source == 'cached', "%s should be cached" % t

        with open("middle.sh", "w") as f:
            f.write("echo 'new'")

        wrapper3 = Wrapper()
#        wrapper3.log_level = 'DEBUG'
        wrapper3.setup()
        wrapper3.run()

        for t in tasks:
            assert wrapper3.batch.task(t).content_source == 'generated', "%s should be generated" % t

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

        wrapper.walk()
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

        wrapper.walk()
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

        wrapper.walk()
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

from dexy.artifact import FilterArtifact
from dexy.artifact import InitialArtifact
from dexy.artifact import InitialVirtualArtifact
from dexy.common import OrderedDict
from dexy.doc import Doc
from dexy.node import DocNode
from dexy.tests.utils import tempdir
from dexy.tests.utils import wrap
from dexy.wrapper import Wrapper
import dexy.exceptions
import time

def test_create_working_dir():
    with wrap() as wrapper:
        wrapper.setup(True)
        c1 = DocNode("data.txt", contents="12345.67", wrapper=wrapper)
        c2 = DocNode("mymod.py", contents="FOO='bar'", wrapper=wrapper)
        node = DocNode("example.py|py",
                inputs = [c1, c2],
                wrapper=wrapper,
                contents="""\
with open("data.txt", "r") as f:
    print f.read()

import mymod
print mymod.FOO

import os
print sorted(os.listdir(os.getcwd()))
""")

        wrapper.run_docs(node)
        doc = node.children[0]

        output = str(doc.output())
        assert "12345.67" in output
        assert 'bar' in output
        assert "['data.txt', 'example.py', 'mymod.py', 'mymod.pyc']" in output

def test_no_data():
    with wrap() as wrapper:
        node = DocNode("hello.txt", wrapper=wrapper)
        try:
            wrapper.run_docs(node)
            assert False, 'should raise UserFeedback'
        except dexy.exceptions.UserFeedback as e:
            assert "No contents found" in e.message

def test_caching():
    with tempdir():
        wrapper1 = Wrapper()
        wrapper1.setup_dexy_dirs()

        with open("abc.txt", "w") as f:
            f.write("these are the contents")

        node1 = DocNode("abc.txt|dexy", wrapper=wrapper1)
        wrapper1.run_docs(node1)

        doc1 = node1.children[0]

        assert isinstance(doc1.children[0], InitialArtifact)
        hashstring_0_1 = doc1.children[0].hashstring

        assert isinstance(doc1.children[1], FilterArtifact)
        hashstring_1_1 = doc1.children[1].hashstring

        wrapper2 = Wrapper()
        node2 = DocNode("abc.txt|dexy", wrapper=wrapper2)
        wrapper2.run_docs(node2)

        doc2 = node2.children[0]

        assert isinstance(doc2.children[0], InitialArtifact)
        hashstring_0_2 = doc2.children[0].hashstring

        assert isinstance(doc2.children[1], FilterArtifact)
        hashstring_1_2 = doc2.children[1].hashstring

        assert hashstring_0_1 == hashstring_0_2
        assert hashstring_1_1 == hashstring_1_2

def test_caching_virtual_file():
    with tempdir():
        wrapper1 = Wrapper()
        wrapper1.setup_dexy_dirs()

        node1 = DocNode("abc.txt|dexy",
                contents = "these are the contents",
                wrapper=wrapper1)
        wrapper1.run_docs(node1)

        doc1 = node1.children[0]

        assert isinstance(doc1.children[0], InitialVirtualArtifact)
        hashstring_0_1 = doc1.children[0].hashstring

        assert isinstance(doc1.children[1], FilterArtifact)
        hashstring_1_1 = doc1.children[1].hashstring

        wrapper2 = Wrapper()
        node2 = DocNode(
                "abc.txt|dexy",
                contents = "these are the contents",
                wrapper=wrapper2)
        wrapper2.run_docs(node2)

        doc2 = node2.children[0]

        assert isinstance(doc2.children[0], InitialVirtualArtifact)
        hashstring_0_2 = doc2.children[0].hashstring

        assert isinstance(doc2.children[1], FilterArtifact)
        hashstring_1_2 = doc2.children[1].hashstring

        assert hashstring_0_1 == hashstring_0_2
        assert hashstring_1_1 == hashstring_1_2

def test_virtual_artifact():
    with wrap() as wrapper:
        a = InitialVirtualArtifact("abc.txt",
                contents="these are the contents",
                wrapper=wrapper)

        a.name = "abc.txt"
        a.doc = Doc("abc.txt")
        a.setup()
        a.run()

        assert a.output_data.is_cached()
        assert a.output_data.data() == "these are the contents"

def test_initial_artifact_hash():
    with wrap() as wrapper:
        filename = "source.txt"

        with open(filename, "w") as f:
            f.write("hello this is some text")

        artifact = InitialArtifact(filename, wrapper=wrapper)
        artifact.name = filename
        artifact.doc = Doc(filename)
        artifact.setup()
        artifact.run()

        first_hashstring = artifact.hashstring

        time.sleep(1.1) # make sure mtime is at least 1 second different

        with open(filename, "w") as f:
            f.write("hello this is different text")

        artifact = InitialArtifact(filename, wrapper=wrapper)
        artifact.name = filename
        artifact.doc = Doc(filename)
        artifact.setup()
        artifact.run()

        second_hashstring = artifact.hashstring

        assert first_hashstring != second_hashstring

def test_parent_doc_hash():
    with tempdir():
        args = [["hello.txt|newdoc", { "contents" : "hello" }]]
        wrapper = Wrapper(*args)
        wrapper.setup(True)
        wrapper.run()

        node = wrapper.batch.tree[0]
        doc = node.children[0]
        hashstring = doc.final_artifact.hashstring

        wrapper = Wrapper(*args)
        wrapper.setup_db()
        wrapper.setup_log()
        wrapper.setup_batch()
        rows = wrapper.db.get_child_hashes_in_previous_batch(hashstring)
        assert len(rows) == 3

def test_parent_doc_hash_2():
    with tempdir():
        args = [["hello.txt|newdoc", { "contents" : "hello" }]]
        wrapper = Wrapper(*args)
        wrapper.setup_dexy_dirs()
        wrapper.run()

        for task in wrapper.batch.lookup_table.values():
            if task.__class__.__name__ == 'FilterArtifact':
                assert task.content_source == 'generated'

        wrapper = Wrapper(*args)
        wrapper.run()

        for task in wrapper.batch.lookup_table.values():
            if task.__class__.__name__ == 'FilterArtifact':
                assert task.content_source == 'cached'

def test_bad_file_extension_exception():
    with wrap() as wrapper:
        doc = DocNode("hello.abc|py",
                contents="hello",
                wrapper=wrapper)

        try:
            wrapper.run_docs(doc)
            assert False, "should not be here"
        except dexy.exceptions.UserFeedback as e:
            assert "Filter 'py' in 'hello.abc|py' can't handle file extension .abc" in e.message

def test_custom_file_extension():
    with wrap() as wrapper:
        node = DocNode("hello.py|pyg",
                contents="""print "hello, world" """,
                pyg = { "ext" : ".tex" },
                wrapper=wrapper)
        wrapper.run_docs(node)
        doc = node.children[0]
        assert "begin{Verbatim}" in str(doc.output())

def test_choose_extension_from_overlap():
    with wrap() as wrapper:
        doc = Doc("hello.py|pyg|forcelatex",
                contents="""print "hello, world" """,
                wrapper=wrapper)
        wrapper.run_docs(doc)
        assert "begin{Verbatim}" in str(doc.output())

def test_no_file_extension_overlap():
    with wrap() as wrapper:
        doc = Doc("hello.txt|forcetext|forcehtml",
                contents="hello",
                wrapper=wrapper)

        try:
            wrapper.run_docs(doc)
            assert False, "UserFeedback should be raised"
        except dexy.exceptions.UserFeedback as e:
            assert "Filter forcehtml can't go after filter forcetext, no file extensions in common." in e.message

def test_virtual_artifact_data_class_generic():
    with wrap() as wrapper:
        doc = Doc("virtual.txt",
                contents = "virtual",
                wrapper=wrapper)
        doc.populate()
        artifact = doc.children[0]
        assert artifact.__class__.__name__ == "InitialVirtualArtifact"
        assert artifact.data_class_alias() == 'generic'

def test_virtual_artifact_data_class_sectioned():
    with wrap() as wrapper:
        contents = OrderedDict()
        contents['foo'] = 'bar'
        doc = Doc("virtual.txt",
                contents=contents,
                wrapper=wrapper)
        doc.populate()
        artifact = doc.children[0]
        assert artifact.__class__.__name__ == "InitialVirtualArtifact"
        assert artifact.data_class_alias() == 'sectioned'

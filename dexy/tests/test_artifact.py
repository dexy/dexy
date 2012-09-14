from dexy.artifact import FilterArtifact
from dexy.artifact import InitialArtifact
from dexy.artifact import InitialVirtualArtifact
from dexy.doc import Doc
from dexy.tests.utils import tempdir
from dexy.tests.utils import wrap
from dexy.wrapper import Wrapper
import dexy.exceptions
import time

def test_caching():
    with tempdir():
        wrapper1 = Wrapper()

        with open("abc.txt", "w") as f:
            f.write("these are the contents")

        doc1 = Doc("abc.txt|dexy", wrapper=wrapper1)
        wrapper1.docs = [doc1]
        wrapper1.run()

        assert isinstance(doc1.artifacts[0], InitialArtifact)
        hashstring_0_1 = doc1.artifacts[0].hashstring

        assert isinstance(doc1.artifacts[1], FilterArtifact)
        hashstring_1_1 = doc1.artifacts[1].hashstring

        wrapper2 = Wrapper()
        doc2 = Doc("abc.txt|dexy", wrapper=wrapper2)
        wrapper2.docs = [doc2]
        wrapper2.run()

        assert isinstance(doc2.artifacts[0], InitialArtifact)
        hashstring_0_2 = doc2.artifacts[0].hashstring

        assert isinstance(doc2.artifacts[1], FilterArtifact)
        hashstring_1_2 = doc2.artifacts[1].hashstring

        assert hashstring_0_1 == hashstring_0_2
        assert hashstring_1_1 == hashstring_1_2

def test_caching_virtual_file():
    with tempdir():
        wrapper1 = Wrapper()
        doc1 = Doc("abc.txt|dexy",
                contents = "these are the contents",
                wrapper=wrapper1)
        wrapper1.docs = [doc1]
        wrapper1.run()

        assert isinstance(doc1.artifacts[0], InitialVirtualArtifact)
        hashstring_0_1 = doc1.artifacts[0].hashstring

        assert isinstance(doc1.artifacts[1], FilterArtifact)
        hashstring_1_1 = doc1.artifacts[1].hashstring

        wrapper2 = Wrapper()
        doc2 = Doc(
                "abc.txt|dexy",
                contents = "these are the contents",
                wrapper=wrapper2)
        wrapper2.docs = [doc2]
        wrapper2.run()

        assert isinstance(doc2.artifacts[0], InitialVirtualArtifact)
        hashstring_0_2 = doc2.artifacts[0].hashstring

        assert isinstance(doc2.artifacts[1], FilterArtifact)
        hashstring_1_2 = doc2.artifacts[1].hashstring

        assert hashstring_0_1 == hashstring_0_2
        assert hashstring_1_1 == hashstring_1_2

def test_virtual_artifact():
    with wrap() as wrapper:
        a = InitialVirtualArtifact("abc.txt",
                contents="these are the contents",
                wrapper=wrapper)

        a.name = "abc.txt"
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
        artifact.run()

        first_hashstring = artifact.hashstring

        time.sleep(1.1) # make sure mtime is at least 1 second different

        with open(filename, "w") as f:
            f.write("hello this is different text")

        artifact = InitialArtifact(filename, wrapper=wrapper)
        artifact.name = filename
        artifact.run()

        second_hashstring = artifact.hashstring

        assert first_hashstring != second_hashstring

def test_parent_doc_hash():
    with tempdir():
        args = [["hello.txt|newdoc", { "contents" : "hello" }]]
        wrapper = Wrapper(*args)
        wrapper.run()

        doc = wrapper.docs[-1]

        wrapper.setup_db()
        rows = wrapper.get_child_hashes_in_previous_batch(doc.final_artifact.hashstring)
        assert len(rows) == 3

def test_parent_doc_hash_2():
    with tempdir():
        args = [["hello.txt|newdoc", { "contents" : "hello" }]]
        wrapper = Wrapper(*args)
        wrapper.run()

        for doc in wrapper.registered:
            if doc.__class__.__name__ == 'FilterArtifact':
                assert doc.source == 'generated'

        wrapper = Wrapper(*args)
        wrapper.run()

        for doc in wrapper.registered:
            if doc.__class__.__name__ == 'FilterArtifact':
                assert doc.source == 'cached'

def test_bad_file_extension_exception():
    with wrap() as wrapper:
        doc = Doc("hello.abc|py",
                contents="hello",
                wrapper=wrapper)

        wrapper.docs = [doc]

        try:
            wrapper.run()
            assert False, "should not be here"
        except dexy.exceptions.UserFeedback as e:
            assert "Filter 'py' in 'hello.abc|py' can't handle file extension .abc" in e.message

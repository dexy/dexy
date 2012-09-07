from dexy.artifact import FilterArtifact
from dexy.artifact import InitialArtifact
from dexy.artifact import InitialVirtualArtifact
from dexy.doc import Doc
from dexy.params import RunParams
from dexy.runner import Runner
from dexy.tests.utils import tempdir
from dexy.tests.utils import temprun
import time

def test_caching():
    with tempdir():
        runner1 = Runner()

        with open("abc.txt", "w") as f:
            f.write("these are the contents")

        doc1 = Doc("abc.txt|dexy", runner=runner1)
        runner1.docs = [doc1]
        runner1.run()

        assert isinstance(doc1.artifacts[0], InitialArtifact)
        hashstring_0_1 = doc1.artifacts[0].hashstring

        assert isinstance(doc1.artifacts[1], FilterArtifact)
        hashstring_1_1 = doc1.artifacts[1].hashstring

        runner2 = Runner()
        doc2 = Doc("abc.txt|dexy", runner=runner2)
        runner2.docs = [doc2]
        runner2.run()

        assert isinstance(doc2.artifacts[0], InitialArtifact)
        hashstring_0_2 = doc2.artifacts[0].hashstring

        assert isinstance(doc2.artifacts[1], FilterArtifact)
        hashstring_1_2 = doc2.artifacts[1].hashstring

        assert hashstring_0_1 == hashstring_0_2
        assert hashstring_1_1 == hashstring_1_2

def test_caching_virtual_file():
    with tempdir():
        runner1 = Runner()
        doc1 = Doc("abc.txt|dexy",
                contents = "these are the contents",
                runner=runner1)
        runner1.docs = [doc1]
        runner1.run()

        assert isinstance(doc1.artifacts[0], InitialVirtualArtifact)
        hashstring_0_1 = doc1.artifacts[0].hashstring

        assert isinstance(doc1.artifacts[1], FilterArtifact)
        hashstring_1_1 = doc1.artifacts[1].hashstring

        runner2 = Runner()
        doc2 = Doc(
                "abc.txt|dexy",
                contents = "these are the contents",
                runner=runner2)
        runner2.docs = [doc2]
        runner2.run()

        assert isinstance(doc2.artifacts[0], InitialVirtualArtifact)
        hashstring_0_2 = doc2.artifacts[0].hashstring

        assert isinstance(doc2.artifacts[1], FilterArtifact)
        hashstring_1_2 = doc2.artifacts[1].hashstring

        assert hashstring_0_1 == hashstring_0_2
        assert hashstring_1_1 == hashstring_1_2

def test_virtual_artifact():
    with temprun() as runner:
        a = InitialVirtualArtifact("abc.txt",
                contents="these are the contents",
                runner=runner)

        a.name = "abc.txt"
        a.run()

        assert a.output_data.is_cached()
        assert a.output_data.data() == "these are the contents"

def test_initial_artifact_hash():
    with temprun() as runner:
        filename = "source.txt"

        with open(filename, "w") as f:
            f.write("hello this is some text")

        artifact = InitialArtifact(filename, runner=runner)
        artifact.name = filename
        artifact.run()

        first_hashstring = artifact.hashstring

        time.sleep(1.1) # make sure mtime is at least 1 second different

        with open(filename, "w") as f:
            f.write("hello this is different text")

        artifact = InitialArtifact(filename, runner=runner)
        artifact.name = filename
        artifact.run()

        second_hashstring = artifact.hashstring

        assert first_hashstring != second_hashstring

def test_parent_doc_hash():
    with tempdir():
        params = RunParams()
        args = [["hello.txt|newdoc", { "contents" : "hello" }]]
        runner = Runner(params, args)
        runner.run()

        doc = runner.docs[-1]

        runner.setup_db()
        rows = runner.get_child_hashes_in_previous_batch(doc.final_artifact.hashstring)
        assert len(rows) == 3

def test_parent_doc_hash_2():
    with tempdir():
        params = RunParams()
        args = [["hello.txt|newdoc", { "contents" : "hello" }]]

        runner = Runner(params, args)
        runner.run()

        for doc in runner.registered:
            if doc.__class__.__name__ == 'FilterArtifact':
                assert doc.source == 'generated'

        runner = Runner(params, args)
        runner.run()

        for doc in runner.registered:
            if doc.__class__.__name__ == 'FilterArtifact':
                assert doc.source == 'cached'

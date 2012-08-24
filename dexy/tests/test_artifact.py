from dexy.artifact import FilterArtifact
from dexy.artifact import Artifact
from dexy.artifact import InitialArtifact
from dexy.artifact import InitialVirtualArtifact
from dexy.doc import Doc
from dexy.plugin import Metadata
from dexy.runner import Runner
from dexy.tests.utils import tempdir
from dexy.tests.utils import temprun
import time

def test_caching():
    with tempdir():
        runner1 = Runner()
        runner1.setup()

        with open("abc.txt", "w") as f:
            f.write("these are the contents")

        doc1 = Doc("abc.txt|dexy")
        runner1.run(doc1)

        assert isinstance(doc1.artifacts[0], InitialArtifact)
        hashstring_0_1 = doc1.artifacts[0].metadata.hashstring

        assert isinstance(doc1.artifacts[1], FilterArtifact)
        hashstring_1_1 = doc1.artifacts[1].metadata.hashstring

        doc2 = Doc("abc.txt|dexy")
        runner2 = Runner()
        runner2.run(doc2)

        assert isinstance(doc2.artifacts[0], InitialArtifact)
        hashstring_0_2 = doc2.artifacts[0].metadata.hashstring

        assert isinstance(doc2.artifacts[1], FilterArtifact)
        hashstring_1_2 = doc2.artifacts[1].metadata.hashstring

        assert hashstring_0_1 == hashstring_0_2
        assert hashstring_1_1 == hashstring_1_2

def test_caching_virtual_file():
    with tempdir():
        runner1 = Runner()
        runner1.setup()

        doc1 = Doc("abc.txt|dexy", contents = "these are the contents")
        runner1.run(doc1)

        assert isinstance(doc1.artifacts[0], InitialVirtualArtifact)
        hashstring_0_1 = doc1.artifacts[0].metadata.hashstring

        assert isinstance(doc1.artifacts[1], FilterArtifact)
        hashstring_1_1 = doc1.artifacts[1].metadata.hashstring

        doc2 = Doc("abc.txt|dexy", contents = "these are the contents")
        runner2 = Runner()
        runner2.run(doc2)

        assert isinstance(doc2.artifacts[0], InitialVirtualArtifact)
        hashstring_0_2 = doc2.artifacts[0].metadata.hashstring

        assert isinstance(doc2.artifacts[1], FilterArtifact)
        hashstring_1_2 = doc2.artifacts[1].metadata.hashstring

        assert hashstring_0_1 == hashstring_0_2
        assert hashstring_1_1 == hashstring_1_2

def test_setup():
    a1 = InitialArtifact("abc.txt")
    a2 = InitialVirtualArtifact("abc.txt")
    a3 = FilterArtifact("abc.txt")

    # We should have a working log
    a1.log.debug("hello")
    a2.log.debug("hello")
    a3.log.debug("hello")

    # And a metadata instance
    assert isinstance(a1.metadata, Metadata)
    assert isinstance(a2.metadata, Metadata)
    assert isinstance(a3.metadata, Metadata)

def test_virtual_artifact():
    with temprun() as runner:
        a = InitialVirtualArtifact("abc.txt", contents="these are the contents")
        a.name = "abc.txt"
        runner.run(a)
        assert a.output_data.is_cached()
        assert a.output_data.data() == "these are the contents"
        assert a.state == 'complete'

def test_initial_artifact_hash():
    with temprun() as runner:
        filename = "source.txt"

        with open(filename, "w") as f:
            f.write("hello this is some text")

        artifact = InitialArtifact(filename)
        artifact.name = filename
        artifact.run(runner)

        first_hashstring = artifact.metadata.hashstring

        time.sleep(1.1) # make sure mtime is at least 1 second different

        with open(filename, "w") as f:
            f.write("hello this is different text")

        artifact = InitialArtifact(filename)
        artifact.name = filename
        artifact.run(runner)

        second_hashstring = artifact.metadata.hashstring

        assert first_hashstring != second_hashstring

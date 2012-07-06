from dexy.opuscule import *

def test_opuscule():
    opus = Doc("abc.txt|f1|f2")
    assert opus.key == "abc.txt|f1|f2"
    assert opus.name == "abc.txt"
    assert opus.filters == ["f1", "f2"]

    assert opus.children[0].key == "abc.txt"
    assert opus.children[1].key == "abc.txt|f1"
    assert opus.children[2].key == "abc.txt|f1|f2"

    assert opus.children[0].__class__.__name__ == "InitialArtifact"
    assert opus.children[1].__class__.__name__ == "Artifact"
    assert opus.children[2].__class__.__name__ == "Artifact"

    assert opus.children[1].prior.__class__.__name__ == "InitialArtifact"
    assert opus.children[2].prior.__class__.__name__ == "Artifact"

    assert opus.children[1].prior.key == "abc.txt"
    assert opus.children[2].prior.key == "abc.txt|f1"

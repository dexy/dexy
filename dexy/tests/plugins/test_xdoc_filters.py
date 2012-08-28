from dexy.tests.utils import temprun
from dexy.doc import Doc

def test_pydoc_filter():
    with temprun() as runner:
        doc = Doc("modules.txt|pydoc", contents="dexy")
        runner.run(doc)
        assert "dexy.artifact.Artifact.__class__:source" in doc.output().keys()

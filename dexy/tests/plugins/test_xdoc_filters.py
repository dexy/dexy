from dexy.tests.utils import wrap
from dexy.doc import Doc

def test_pydoc_filter():
    with wrap() as wrapper:
        doc = Doc("modules.txt|pydoc", contents="dexy", wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()
        assert "dexy.artifact.Artifact.__class__:source" in doc.output().keys()

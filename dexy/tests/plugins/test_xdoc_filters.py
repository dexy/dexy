from dexy.tests.utils import wrap
from dexy.doc import Doc

def test_pydoc_filter():
    with wrap() as wrapper:
        doc = Doc("modules.txt|pydoc", contents="os", wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()
        assert "os.ttyname:html-source" in doc.output().keys()

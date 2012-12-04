from dexy.tests.utils import wrap
from dexy.doc import Doc

def test_pydoc_filter():
    with wrap() as wrapper:
        doc = Doc("modules.txt|pydoc", contents="os math", wrapper=wrapper)
        wrapper.run_docs(doc)

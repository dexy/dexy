from dexy.tests.utils import wrap
from dexy.doc import Doc

def test_pydoc_filter():
    with wrap() as wrapper:
        doc = Doc("modules.txt|pydoc", contents="os math", wrapper=wrapper)
        wrapper.run_docs(doc)
        assert "os.unsetenv:html-source" in doc.output().keys()

#        print doc.output().query("math.log")
#        for k in doc.output().keys():
#            print k

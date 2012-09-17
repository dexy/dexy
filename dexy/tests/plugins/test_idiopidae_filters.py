from dexy.tests.utils import wrap
from dexy.doc import Doc

def test_force_text():
    with wrap() as wrapper:
        doc = Doc("example.py|idio|t",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

        assert doc.output().as_text() == "print 'hello'\n"

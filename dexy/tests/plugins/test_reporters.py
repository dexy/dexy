import os
from dexy.doc import Doc
from dexy.tests.utils import wrap

def test_output_reporter():
    with wrap() as wrapper:
        wrapper.reports = "output"
        doc = Doc("hello.txt", contents="hello", wrapper=wrapper)
        wrapper.run_docs(doc)
        wrapper.report()
        assert os.path.exists("output")
        assert os.path.exists("output/hello.txt")

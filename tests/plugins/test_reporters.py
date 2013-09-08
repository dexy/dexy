import os
from dexy.doc import Doc
from tests.utils import wrap

def test_output_reporter():
    with wrap() as wrapper:
        wrapper.reports = "output"
        doc = Doc("hello.txt", wrapper, [], contents="hello")
        wrapper.run_docs(doc)
        wrapper.report()
        assert os.path.exists("output")
        assert os.path.exists("output/hello.txt")

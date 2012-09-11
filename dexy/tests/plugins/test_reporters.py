from dexy.plugins.output_reporters import OutputReporter
import os
from dexy.doc import Doc
from dexy.tests.utils import wrap

def test_output_reporter():
    with wrap() as wrapper:
        doc = Doc("hello.txt", contents="hello", wrapper=wrapper)
        reporter = OutputReporter()
        wrapper.docs = [doc]
        wrapper.run()
        wrapper.report(reporter)
        assert os.path.exists("output")
        assert os.path.exists("output/hello.txt")

from dexy.plugins.output_reporters import OutputReporter
import os
from dexy.doc import Doc
from dexy.tests.utils import temprun

def test_output_reporter():
    with temprun() as runner:
        doc = Doc("hello.txt", contents="hello")
        reporter = OutputReporter()
        runner.run(doc)
        runner.report(reporter)
        assert os.path.exists("output")
        assert os.path.exists("output/hello.txt")

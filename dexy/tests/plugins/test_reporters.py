from dexy.plugins.output_reporters import OutputReporter
import os
from dexy.doc import Doc
from dexy.tests.utils import temprun

def test_output_reporter():
    with temprun() as runner:
        doc = Doc("hello.txt", contents="hello", runner=runner)
        reporter = OutputReporter()
        runner.docs = [doc]
        runner.run()
        runner.report(reporter)
        assert os.path.exists("output")
        assert os.path.exists("output/hello.txt")

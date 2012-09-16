from dexy.tests.utils import assert_output
from dexy.doc import Doc
from dexy.tests.utils import wrap

def test_python_stdout_filter():
    assert_output('py', 'print 1+1', "2\n")

def test_bash_stdout_filter():
    assert_output('bash', 'echo "hello"', "hello\n")

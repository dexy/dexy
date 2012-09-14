from dexy.tests.utils import assert_output

def test_python_stdout_filter():
    assert_output('py', 'print 1+1', "2\n")

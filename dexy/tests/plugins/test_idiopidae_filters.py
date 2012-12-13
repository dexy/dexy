from dexy.doc import Doc
from dexy.tests.utils import wrap
from nose.tools import raises
import dexy.exceptions

@raises(dexy.exceptions.UserFeedback)
def test_idio_invalid_input():
    with wrap() as wrapper:
        doc = Doc("hello.py|idio", wrapper=wrapper, contents=" ")
        wrapper.run_docs(doc)

@raises(dexy.exceptions.UserFeedback)
def test_idio_bad_file_extension():
    with wrap() as wrapper:
        doc = Doc("hello.xyz|idio", wrapper=wrapper, contents=" ")
        wrapper.run_docs(doc)

def test_multiple_sections():
    with wrap() as wrapper:
        src = """
### @export "vars"
x = 6
y = 7

### @export "multiply"
x*y

"""
        doc = Doc("example.py|idio",
                contents=src,
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().keys() == ['1', 'vars', 'multiply']

def test_force_text():
    with wrap() as wrapper:
        doc = Doc("example.py|idio|t",
                contents="print 'hello'\n",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert str(doc.output()) == "print 'hello'\n"

def test_force_latex():
    with wrap() as wrapper:
        doc = Doc("example.py|idio|l",
                contents="print 'hello'\n",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert "begin{Verbatim}" in str(doc.output())

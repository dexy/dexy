from dexy.doc import Doc
from dexy.tests.utils import wrap
from nose.tools import raises
import dexy.exceptions

@raises(dexy.exceptions.UserFeedback)
def test_idio_invalid_input():
    with wrap() as wrapper:
        doc = Doc("hello.py|idio",
                wrapper, [],
                contents=" ")
        wrapper.run(doc)

@raises(dexy.exceptions.UserFeedback)
def test_idio_bad_file_extension():
    with wrap() as wrapper:
        doc = Doc("hello.xyz|idio", wrapper, [], contents=" ")
        wrapper.run(doc)

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
                wrapper,
                [],
                contents=src)

        wrapper.run(doc)

        assert doc.output_data().keys() == ['1', 'vars', 'multiply']

def test_force_text():
    with wrap() as wrapper:
        node = Doc("example.py|idio|t",
                wrapper,
                [],
                contents="print 'hello'\n")

        wrapper.run(node)
        print node.output_data().__class__
        assert str(node.output_data()) == "print 'hello'\n"

def test_force_latex():
    with wrap() as wrapper:
        doc = Doc("example.py|idio|l",
                wrapper,
                [],
                contents="print 'hello'\n")

        wrapper.run(doc)

        assert "begin{Verbatim}" in str(doc.output_data())

from dexy.common import OrderedDict
from dexy.doc import Doc
from dexy.tests.utils import assert_in_output
from dexy.tests.utils import assert_output
from dexy.tests.utils import assert_output_cached
from dexy.tests.utils import wrap
from nose.tools import raises
import dexy.exceptions

def test_pyg4rst():
    o = OrderedDict()
    o['1'] = ".. code:: python\n\n  print 'hello'"
    assert_output("pyg4rst", "print 'hello'", o, ext=".py")

def test_html():
    assert_in_output("pyg|h", "print 'hello'", """<div class="highlight">""")

def test_png():
    assert_output_cached("pyg|pn", "print 'hello'")

def test_jpg():
    assert_output_cached("pyg|jn", "print 'hello'")

def test_gif():
    assert_output_cached("pyg|gn", "print 'hello'")

@raises(dexy.exceptions.UserFeedback)
def test_pyg4rst_bad_file_extension():
    with wrap() as wrapper:
        doc = Doc("hello.xyz|pyg4rst", wrapper=wrapper, contents=" ")
        wrapper.run_docs(doc)

@raises(dexy.exceptions.UserFeedback)
def test_pygments_bad_file_extension():
    with wrap() as wrapper:
        doc = Doc("hello.xyz|pyg", wrapper=wrapper, contents=" ")
        wrapper.run_docs(doc)

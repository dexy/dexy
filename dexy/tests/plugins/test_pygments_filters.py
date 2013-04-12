from dexy.common import OrderedDict
from dexy.doc import Doc
from dexy.tests.utils import assert_in_output
from dexy.tests.utils import assert_output
from dexy.tests.utils import assert_output_cached
from dexy.tests.utils import wrap

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

def test_pyg4rst_bad_file_extension():
    with wrap() as wrapper:
        wrapper.debug = False
        doc = Doc(
                "hello.xyz|pyg4rst",
                wrapper,
                [],
                contents=" ",
                pyg4rst = { 'allow_unknown_ext' : False }
                )
        wrapper.run_docs(doc)
        assert wrapper.state == 'error'

def test_pygments_bad_file_extension():
    with wrap() as wrapper:
        wrapper.debug = False
        doc = Doc(
                "hello.xyz|pyg",
                wrapper,
                [],
                contents=" ",
                pyg = { 'allow_unknown_ext' : False }
                )
        wrapper.run_docs(doc)
        assert wrapper.state == 'error'

from dexy.common import OrderedDict
from dexy.doc import Doc
from dexy.tests.utils import assert_output
from dexy.tests.utils import wrap

def test_pyg4rst():
    o = OrderedDict()
    o['1'] = ".. code:: python\n  print 'hello'"
    assert_output("pyg4rst", "print 'hello'", o, ext=".py")

def test_html():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|h",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

        assert """<div class="highlight">""" in doc.output().as_text()

def test_png():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|pn",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

def test_jpg():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|jn",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

def test_gif():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|gn",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

def test_gif():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|gn",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

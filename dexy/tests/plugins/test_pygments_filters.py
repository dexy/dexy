from dexy.tests.utils import wrap
from dexy.doc import Doc

def test_force_html():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|h",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

        assert """<div class="highlight">""" in doc.output().as_text()

def test_force_png():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|pn",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

def test_force_jpg():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|jn",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

def test_force_gif():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|gn",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

def test_force_gif():
    with wrap() as wrapper:
        doc = Doc("example.py|pyg|gn",
                contents="print 'hello'\n",
                wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()

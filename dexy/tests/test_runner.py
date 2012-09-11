from dexy.doc import Doc
from dexy.wrapper import Wrapper
from dexy.tests.utils import tempdir
import os

def test_wrapper_init():
    wrapper = Wrapper()
    assert wrapper.artifacts_dir == 'artifacts'

def test_wrapper_setup():
    with tempdir():
        assert not os.path.exists('artifacts')
        wrapper = Wrapper()
        wrapper.setup_dexy_dirs()
        assert os.path.exists('artifacts')

def test_wrapper_run():
    with tempdir():
        wrapper = Wrapper()
        wrapper.setup_dexy_dirs()
        d1 = Doc("abc.txt|outputabc", contents="these are the contents", wrapper=wrapper)
        d2 = Doc("hello.txt|outputabc", contents="these are more contents", wrapper=wrapper)
        assert d1.state == 'setup'
        assert d2.state == 'setup'
        wrapper.docs = [d1, d2]
        wrapper.run()
        assert d1.state == 'complete'
        assert d2.state == 'complete'

def test_wrapper_register():
    with tempdir():
        doc = Doc("abc.txt")
        wrapper = Wrapper()
        wrapper.setup_run()
        wrapper.register(doc)
        assert doc in wrapper.registered

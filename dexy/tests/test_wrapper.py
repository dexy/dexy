from dexy.doc import Doc
from dexy.wrapper import Wrapper
from dexy.tests.utils import tempdir
import os

def test_config_file():
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("""{ "logfile" : "a.log" }""")

        wrapper = Wrapper()
        assert wrapper.log_file == "a.log"

def test_kwargs_override_config_file():
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("""{ "logfile" : "a.log" }""")

        wrapper = Wrapper(logfile="b.log")
        assert wrapper.log_file == "b.log"

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
        wrapper.run_docs(d1, d2)
        assert d1.state == 'complete'
        assert d2.state == 'complete'

def test_wrapper_register():
    with tempdir():
        doc = Doc("abc.txt")
        wrapper = Wrapper()
        wrapper.setup_dexy_dirs()
        wrapper.setup_run()
        wrapper.register(doc)
        assert doc in wrapper.registered_docs()

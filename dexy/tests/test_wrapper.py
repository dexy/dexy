from dexy.commands import init_wrapper
from dexy.doc import Doc
from dexy.exceptions import UserFeedback
from dexy.tests.utils import tempdir
from dexy.tests.utils import wrap
from dexy.wrapper import Wrapper
from nose.tools import raises
import os

def test_config_for_directory():
    with wrap() as wrapper:
        with open("docs.yaml", "w") as f:
            f.write(""".abc""")

        with open("root.abc", "w") as f:
            f.write("hello")

        with open("root.def", "w") as f:
            f.write("hello")

        os.makedirs("s1")
        os.makedirs("s2")

        with open("s1/s1.abc", "w") as f:
            f.write("hello")

        with open("s1/s1.def", "w") as f:
            f.write("hello")

        with open("s2/s2.abc", "w") as f:
            f.write("hello")

        with open("s2/s2.def", "w") as f:
            f.write("hello")

        with open(os.path.join('s1', 'docs.yaml'), 'w') as f:
            f.write(""".def|dexy""")

        wrapper.setup_config()
        wrapper.run()

        assert len(wrapper.batch.tasks()) == 8

        p = wrapper.batch.task("PatternNode:*.abc")
        c = wrapper.batch.task("Doc:s2/s2.abc")
        assert c in p.children

def test_config_file():
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("""{ "logfile" : "a.log" }""")

        wrapper = init_wrapper({'conf' : 'dexy.conf'})
        assert wrapper.log_file == "a.log"

def test_kwargs_override_config_file():
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("""{ "logfile" : "a.log" }""")

        wrapper = init_wrapper({
            '__cli_options' : { 'logfile' : 'b.log' },
            'logfile' : "b.log",
            'conf' : 'dexy.conf'
            })
        assert wrapper.log_file == "b.log"

def test_wrapper_init():
    wrapper = Wrapper()
    assert wrapper.artifacts_dir == 'artifacts'

def test_wrapper_setup():
    with tempdir():
        assert not os.path.exists('artifacts')
        wrapper = init_wrapper({'conf' : 'dexy.conf'})
        wrapper.setup_dexy_dirs()
        assert os.path.exists('artifacts')

def test_wrapper_run():
    with tempdir():
        wrapper = init_wrapper({'conf' : 'dexy.conf'})
        wrapper.setup_dexy_dirs()
        d1 = Doc("abc.txt|outputabc", contents="these are the contents", wrapper=wrapper)
        d2 = Doc("hello.txt|outputabc", contents="these are more contents", wrapper=wrapper)
        assert d1.state == 'new'
        assert d2.state == 'new'
        wrapper.run_docs(d1, d2)
        assert d1.state == 'complete'
        assert d2.state == 'complete'

def test_wrapper_register():
    with tempdir():
        doc = Doc("abc.txt")
        wrapper = init_wrapper({'conf' : 'dexy.conf'})
        wrapper.setup_dexy_dirs()
        wrapper.setup_log()
        wrapper.setup_db()
        wrapper.setup_batch()
        wrapper.batch.add_doc(doc)
        assert doc in wrapper.batch.tasks()

@raises(UserFeedback)
def test_double_config_raises_error():
    with wrap() as wrapper:
        with open("dexy.txt", "w") as f:
            f.write("hello.txt")
        with open("dexy.yaml", "w") as f:
            f.write("hello.txt")

        wrapper.load_doc_config()

def test_no_config_raises_error():
    with wrap() as wrapper:
        wrapper.load_doc_config()

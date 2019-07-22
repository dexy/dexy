from dexy.doc import Doc
from dexy.filters.process import SubprocessFilter
from tests.utils import wrap
import dexy.exceptions
import os

def test_add_new_files():
    with wrap() as wrapper:
        node = Doc("example.sh|sh",
                wrapper,
                [],
                contents = "echo 'hello' > newfile.txt",
                sh = {
                    "add-new-files" : True,
                    "keep-originals" : True,
                    "additional-doc-filters" : { '.txt' : 'markdown' }
                    }
                )
        wrapper.run_docs(node)

        assert str(wrapper.nodes['doc:newfile.txt'].output_data()) == "hello" + os.linesep
        assert str(wrapper.nodes['doc:newfile.txt|markdown'].output_data()) == "<p>hello</p>"

def test_not_present_executable():
    # TODO modify test so we try to run this
    dexy.filter.Filter.create_instance('notreal')

class NotPresentExecutable(SubprocessFilter):
    """
    notreal
    """
    EXECUTABLE = 'notreal'
    aliases = ['notreal']

def test_command_line_args():
    with wrap() as wrapper:
        node = Doc("example.py|py",
                wrapper,
                [],
                py={"args" : "-B"},
                contents="print('hello')"
                )
        wrapper.run_docs(node)

        assert str(node.output_data()) == "hello" + os.linesep

        command_used = node.filters[-1].command_string()
        assert command_used == "python -B  \"example.py\" "

def test_scriptargs():
    with wrap() as wrapper:
        node = Doc("example.py|py",
                wrapper,
                [],
                py={"scriptargs" : "--foo"},
                contents="""import sys\nprint("args are: '%s'" % sys.argv[1])"""
                )
        wrapper.run_docs(node)

        assert "args are: '--foo'" in str(node.output_data())

        command_used = node.filters[-1].command_string()
        assert command_used == "python   \"example.py\" --foo"

def test_custom_env_in_args():
    with wrap() as wrapper:
        node = Doc("example.py|py",
                wrapper,
                [],
                py={"env" : {"FOO" : "bar" }},
                contents="import os\nprint(os.environ['FOO'])"
                )
        wrapper.run_docs(node)

        assert str(node.output_data()) == "bar" + os.linesep

def test_nonzero_exit():
    with wrap() as wrapper:
        wrapper.debug = False
        node = Doc("example.py|py",
                wrapper,
                [],
                contents="import sys\nsys.exit(1)"
                )
        wrapper.run_docs(node)
        assert wrapper.state == 'error'

def test_ignore_nonzero_exit():
    with wrap() as wrapper:
        wrapper.ignore_nonzero_exit = True
        node = Doc("example.py|py",
                wrapper,
                [],
                contents="import sys\nsys.exit(1)"
                )
        wrapper.run_docs(node)
        assert True # no NonzeroExit was raised...

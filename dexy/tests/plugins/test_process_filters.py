from dexy.node import DocNode
from dexy.plugins.process_filters import SubprocessFilter
from dexy.tests.utils import wrap
import dexy.exceptions
import os

def test_add_new_files():
    with wrap() as wrapper:
        node = DocNode("example.sh|sh",
                contents = "echo 'hello' > newfile.txt",
                sh = {
                    "add-new-files" : True,
                    "additional-doc-filters" : { '.txt' : 'markdown' }
                    },
                wrapper=wrapper)

        wrapper.run_docs(node)

        assert wrapper.batch.lookup_table['Doc:newfile.txt'].output().data() == "hello" + os.linesep
        assert wrapper.batch.lookup_table['Doc:newfile.txt|markdown'].output().data() == "<p>hello</p>"

def test_walk_working_dir():
    with wrap() as wrapper:
        node = DocNode("example.sh|sh",
                contents = "echo 'hello' > newfile.txt",
                sh = {
                    "walk-working-dir" : True,
                    },
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]

        for doc in wrapper.batch.tasks():
            if doc.key_with_class() == "Doc:example.sh-sh.txt-files":
                assert doc.output().as_sectioned()['newfile.txt'] == "hello" + os.linesep


def test_not_present_executable():
    assert 'notreal' in NotPresentExecutable.executables()
    assert not NotPresentExecutable.executable()

class NotPresentExecutable(SubprocessFilter):
    """
    notreal
    """
    EXECUTABLE = 'notreal'

def test_command_line_args():
    with wrap() as wrapper:
        node = DocNode("example.py|py",
                py={"args" : "-B"},
                wrapper=wrapper,
                contents="print 'hello'"
                )
        wrapper.run_docs(node)
        doc = node.children[0]

        assert doc.output().data() == "hello" + os.linesep

        command_used = doc.children[-1].filter_instance.command_string()
        assert command_used == """python -B "example.py"  "example.txt" """

def test_scriptargs():
    with wrap() as wrapper:
        node = DocNode("example.py|py",
                py={"scriptargs" : "--foo"},
                wrapper=wrapper,
                contents="import sys\nprint sys.argv[1]"
                )
        wrapper.run_docs(node)
        doc = node.children[0]

        assert doc.output().data() == "--foo" + os.linesep

        command_used = doc.children[-1].filter_instance.command_string()
        assert command_used == """python  "example.py" --foo "example.txt" """

def test_custom_env_in_args():
    with wrap() as wrapper:
        node = DocNode("example.py|py",
                py={"env" : {"FOO" : "bar" }},
                wrapper=wrapper,
                contents="import os\nprint os.environ['FOO']"
                )
        wrapper.run_docs(node)

        doc = node.children[0]

        assert doc.output().data() == "bar" + os.linesep

def test_nonzero_exit():
    with wrap() as wrapper:
        node = DocNode("example.py|py",
                wrapper=wrapper,
                contents="import sys\nsys.exit(1)"
                )
        try:
            wrapper.run_docs(node)
            assert False, "should raise error"
        except dexy.exceptions.UserFeedback:
            assert True

def test_ignore_nonzero_exit():
    with wrap() as wrapper:
        wrapper.ignore_nonzero_exit = True
        node = DocNode("example.py|py",
                wrapper=wrapper,
                contents="import sys\nsys.exit(1)"
                )
        wrapper.run_docs(node)
        assert True # no NonzeroExit was raised...

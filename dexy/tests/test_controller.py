from dexy.artifacts.file_system_json_artifact import FileSystemJsonArtifact
from dexy.topsort import CycleError
from dexy.constants import NullHandler
from dexy.controller import Controller
from dexy.document import Document
from dexy.tests.utils import tempdir
from dexy.tests.utils import divert_stdout
from modargs import args as modargs
import dexy.commands
import dexy.database
import dexy.filters.python_filters
import os

SIMPLE_PY_CONFIG = {
   "." : {
       "@simple.py|py" : {
           "contents" : "x=6\\ny=7\\nprint x*y"
        }
    }
}

CIRCULAR_CONFIG = {
   "." : {
       "@abc" : { "inputs" : ["@ghi"] },
       "@def" : { "inputs" : ["@abc"] },
       "@ghi" : { "inputs" : ["@def"] }
    }
}

NO_FILTERS_CONFIG = {
   "." : {
       "@hello.txt" : {
           "contents" : "well, hello there!"
        }
    }
}

def test_init():
    c = Controller()
    assert isinstance(c.args, dict)
    assert isinstance(c.config, dict)
    assert len(c.args) == 0
    assert len(c.config) == 0

    assert len(c.log.handlers) == 1
    # Because we didn't pass a logfile or logsdir...
    assert isinstance(c.log.handlers[0], NullHandler)

    assert len(c.reports_dirs) > 1
    assert len(c.artifact_classes) > 0

def test_init_with_artifact_class():
    args = { "artifactclass" : "FileSystemJsonArtifact" }
    c = Controller(args)
    assert c.artifact_class == FileSystemJsonArtifact

def test_init_with_db():
    args = { "dbclass" : "SqliteDatabase", "dbfile" : None, "logsdir" : None }
    c = Controller(args)
    assert isinstance(c.db, dexy.database.Database)

def test_run():
    with tempdir():
        fn = modargs.function_for(dexy.commands, "dexy")
        args = modargs.determine_kwargs(fn)
        args['globals'] = []
        os.mkdir(args['logsdir'])
        c = Controller(args)
        c.config = SIMPLE_PY_CONFIG
        c.process_config()
        assert c.members.has_key("simple.py|py")
        assert isinstance(c.members["simple.py|py"], Document)

def test_docs_with_no_filters():
    with tempdir():
        fn = modargs.function_for(dexy.commands, "dexy")
        args = modargs.determine_kwargs(fn)
        args['globals'] = []
        os.mkdir(args['logsdir'])
        c = Controller(args)
        c.config = NO_FILTERS_CONFIG
        c.process_config()
        assert c.members.has_key("hello.txt")
        assert isinstance(c.members["hello.txt"], Document)
        assert sorted(c.batch_info().keys()) == [
                "args",
                "config",
                "docs",
                "elapsed",
                "finish_time",
                "id",
                "start_time",
                "timing"
                ]

def test_circular_dependencies():
    with tempdir():
        fn = modargs.function_for(dexy.commands, "dexy")
        args = modargs.determine_kwargs(fn)
        args['globals'] = []
        os.mkdir(args['logsdir'])
        args['danger'] = True
        c = Controller(args)
        c.config = CIRCULAR_CONFIG
        with divert_stdout() as stdout:
            try:
                c.process_config()
                assert False
            except CycleError:
                assert True
            stdout_text = stdout.getvalue()
        assert "abc depends on ghi" in stdout_text
        assert "def depends on abc" in stdout_text
        assert "ghi depends on def" in stdout_text


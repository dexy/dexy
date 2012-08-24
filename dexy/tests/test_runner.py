from dexy.doc import Doc
from dexy.params import RunParams
from dexy.runner import Runner
from dexy.tests.utils import tempdir
from ordereddict import OrderedDict
import os

def test_runner_init():
    runner = Runner()
    assert isinstance(runner.params, RunParams)
    assert isinstance(runner.completed, OrderedDict)
    assert runner.artifacts_dir == 'artifacts'

def test_runner_setup():
    with tempdir():
        assert not os.path.exists('artifacts')
        runner = Runner()
        runner.setup()
        assert os.path.exists('artifacts')

def test_runner_run():
    with tempdir():
        runner = Runner()
        runner.setup()
        d1 = Doc("abc.txt|outputabc", contents="these are the contents")
        d2 = Doc("hello.txt|outputabc", contents="these are more contents")
        assert d1.state == 'new'
        assert d2.state == 'new'
        runner.run(d1, d2)
        assert d1.state == 'complete'
        assert d2.state == 'complete'

def test_runner_append():
    doc = Doc("abc.txt")
    runner = Runner()
    runner.append(doc)
    assert doc.key in runner.completed
    assert runner.completed[doc.key] == doc

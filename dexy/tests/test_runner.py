from dexy.doc import Doc
from dexy.params import RunParams
from dexy.runner import Runner
from dexy.tests.utils import tempdir
from ordereddict import OrderedDict
import os

def test_runner_init():
    runner = Runner()
    assert isinstance(runner.params, RunParams)
    assert isinstance(runner.registered, list)
    assert runner.params.artifacts_dir == 'artifacts'

def test_runner_setup():
    with tempdir():
        assert not os.path.exists('artifacts')
        runner = Runner()
        runner.setup_dexy_dirs()
        assert os.path.exists('artifacts')

def test_runner_run():
    with tempdir():
        runner = Runner()
        runner.setup_dexy_dirs()
        d1 = Doc("abc.txt|outputabc", contents="these are the contents", runner=runner)
        d2 = Doc("hello.txt|outputabc", contents="these are more contents", runner=runner)
        assert d1.state == 'setup'
        assert d2.state == 'setup'
        runner.docs = [d1, d2]
        runner.run()
        assert d1.state == 'complete'
        assert d2.state == 'complete'

def test_runner_register():
    with tempdir():
        doc = Doc("abc.txt")
        runner = Runner()
        runner.setup_dexy_dirs()
        runner.register(doc)
        assert doc in runner.registered

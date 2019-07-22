from dexy.version import DEXY_VERSION
from dexy.wrapper import Wrapper
from io import StringIO
from mock import patch
from nose.exc import SkipTest
from nose.tools import raises
from tests.utils import tempdir
from tests.utils import wrap
import dexy.commands
import os
import sys

def test_init_wrapper():
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("artifactsdir: custom")

        modargs = {}
        wrapper = dexy.commands.utils.init_wrapper(modargs)
        assert wrapper.artifacts_dir == 'custom'

@patch.object(sys, 'argv', ['dexy', 'setup'])
def test_setup_with_dexy_conf_file():
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("artifactsdir: custom")

        dexy.commands.run()
        assert os.path.exists("custom")
        assert os.path.isdir("custom")
        assert not os.path.exists("artifacts")

@raises(SystemExit)
@patch.object(sys, 'argv', ['dexy', 'grep', '-expr', 'hello'])
def test_grep():
    with wrap():
        dexy.commands.run()

@patch.object(sys, 'argv', ['dexy', 'grep'])
@patch('sys.stderr', new_callable=StringIO)
def test_grep_without_expr(stderr):
    raise SkipTest()
    try:
        dexy.commands.run()
    except SystemExit as e:
        assert e.code == 1
        assert 'Must specify either expr or key' in stderr.getvalue()

@patch.object(sys, 'argv', ['dexy'])
@patch('sys.stderr', new_callable=StringIO)
def test_run_with_userfeedback_exception(stderr):
    with wrap():
        with open("docs.txt", "w") as f:
            f.write("*.py|py")

        with open("hello.py", "w") as f:
            f.write("raise")

        dexy.commands.run()

@patch.object(sys, 'argv', ['dexy', 'invalid'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_invalid_command(stdout):
    try:
        dexy.commands.run()
        assert False, 'should raise SystemExit'
    except SystemExit as e:
        assert e.code == 1

@patch.object(sys, 'argv', ['dexy', '--help'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_help_old_syntax(stdout):
    dexy.commands.run()
    assert "Commands for running dexy:" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', '--version'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_version_old_syntax(stdout):
    dexy.commands.run()
    assert DEXY_VERSION in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'help'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_help(stdout):
    dexy.commands.run()
    assert "Commands for running dexy:" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'version'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_version(stdout):
    dexy.commands.run()
    assert DEXY_VERSION in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_dexy(stdout):
    with tempdir():
        wrapper = Wrapper()
        wrapper.create_dexy_dirs()
        dexy.commands.run()

### "viewer-ping"
@patch.object(sys, 'argv', ['dexy', 'viewer:ping'])
@patch('sys.stdout', new_callable=StringIO)
def test_viewer_command(stdout):
    raise SkipTest()
    dexy.commands.run()
    assert "pong" in stdout.getvalue()

### "conf"
@patch.object(sys, 'argv', ['dexy', 'conf'])
@patch('sys.stdout', new_callable=StringIO)
def test_conf_command(stdout):
    with tempdir():
        dexy.commands.run()
        assert os.path.exists("dexy.conf")
        assert "has been written" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'conf'])
@patch('sys.stdout', new_callable=StringIO)
def test_conf_command_if_path_exists(stdout):
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("foo")
        assert os.path.exists("dexy.conf")
        dexy.commands.run()
        assert "dexy.conf already exists" in stdout.getvalue()
        assert "artifactsdir" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'conf', '-p'])
@patch('sys.stdout', new_callable=StringIO)
def test_conf_command_with_print_option(stdout):
    with tempdir():
        dexy.commands.run()
        assert not os.path.exists("dexy.conf")
        assert "artifactsdir" in stdout.getvalue()

### "filters"
@patch.object(sys, 'argv', ['dexy', 'filters'])
@patch('sys.stdout', new_callable=StringIO)
def test_filters_cmd(stdout):
    dexy.commands.run()
    assert "pyg : Apply Pygments" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'filters', '-alias', 'pyg'])
@patch('sys.stdout', new_callable=StringIO)
def test_filters_cmd_alias(stdout):
    dexy.commands.run()
    assert "pyg, pygments" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'filters', '-versions'])
@patch('sys.stdout', new_callable=StringIO)
def test_filters_text_versions__slow(stdout):
    dexy.commands.run()
    assert "Installed version: Python" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'filters', '-alias', 'pyg', '-source'])
@patch('sys.stdout', new_callable=StringIO)
def test_filters_text_single_alias_source(stdout):
    raise SkipTest() # TODO fixme
    dexy.commands.run()
    text = stdout.getvalue()
    sys.stderr.write("TEXT IS:\n%s" % text)
    assert "pyg, pygments" in text
    assert "class" in text
    assert "PygmentsFilter" in text
    assert not "class PygmentsFilter" in text

@patch.object(sys, 'argv', ['dexy', 'filters', '-alias', 'pyg', '-source', '-nocolor'])
@patch('sys.stdout', new_callable=StringIO)
def test_filters_text_single_alias_source_nocolor(stdout):
    raise SkipTest() # TODO fixme
    dexy.commands.run()
    text = stdout.getvalue()
    assert "pyg, pygments" in text
    assert "class PygmentsFilter" in text

@patch.object(sys, 'argv', ['dexy', 'parsers'])
@patch('sys.stdout', new_callable=StringIO)
def test_parsers_text(stdout):
    dexy.commands.run()
    text = stdout.getvalue()
    assert "Yaml Parser" in text

@patch.object(sys, 'argv', ['dexy', 'nodes'])
@patch('sys.stdout', new_callable=StringIO)
def test_nodes_text(stdout):
    dexy.commands.run()
    text = stdout.getvalue()
    assert "bundle" in text

@patch.object(sys, 'argv', ['dexy', 'env'])
@patch('sys.stdout', new_callable=StringIO)
def test_env_text(stdout):
    dexy.commands.run()
    text = stdout.getvalue()
    assert "uuid" in text

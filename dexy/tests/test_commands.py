from StringIO import StringIO
from dexy.tests.utils import tempdir
from dexy.tests.utils import wrap
from dexy.version import DEXY_VERSION
from mock import patch
from nose.exc import SkipTest
import dexy.commands
import os
import sys

def test_init_wrapper():
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("artifactsdir: custom")

        modargs = {}
        wrapper = dexy.commands.init_wrapper(modargs)
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

@patch.object(sys, 'argv', ['dexy', 'grep', '-expr', 'hello'])
def test_grep():
    with wrap() as wrapper:
        wrapper.setup_dexy_dirs()
        dexy.commands.run()

@patch.object(sys, 'argv', ['dexy', 'grep'])
@patch('sys.stdout', new_callable=StringIO)
def test_grep_without_expr(stdout):
    try:
        dexy.commands.run()
    except SystemExit as e:
        assert e.message == 1
        assert 'Option -expr' in stdout.getvalue()

def test_help_text():
    assert "Available commands" in dexy.commands.help_text()

@patch.object(sys, 'argv', ['dexy'])
@patch('sys.stderr', new_callable=StringIO)
def test_run_with_userfeedback_exception(stderr):
    with tempdir():
        with open("docs.txt", "w") as f:
            f.write("*.py|py")

        with open("hello.py", "w") as f:
            f.write("raise")

        try:
            dexy.commands.run()
            assert False, 'should raise SystemExit'
        except SystemExit as e:
            assert e.message == 1
            assert "Dexy is stopping" in stderr.getvalue()

@patch.object(sys, 'argv', ['dexy', 'invalid'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_invalid_command(stdout):
    try:
        dexy.commands.run()
        assert False, 'should raise SystemExit'
    except SystemExit as e:
        assert e.message == 1

@patch.object(sys, 'argv', ['dexy', '--help'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_help_old_syntax(stdout):
    dexy.commands.run()
    assert "Available commands for dexy are:" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', '--version'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_version_old_syntax(stdout):
    dexy.commands.run()
    assert DEXY_VERSION in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'help'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_help(stdout):
    dexy.commands.run()
    assert "Available commands for dexy are:" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'version'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_version(stdout):
    dexy.commands.run()
    assert DEXY_VERSION in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy'])
@patch('sys.stdout', new_callable=StringIO)
def test_run_dexy(stdout):
    with tempdir():
        os.makedirs('logs')
        os.makedirs('artifacts')
        dexy.commands.run()

    assert "finished in" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'viewer:ping'])
@patch('sys.stdout', new_callable=StringIO)
def test_viewer_command(stdout):
    try:
        dexy.commands.run()
        assert "pong" in stdout.getvalue()
    except SystemExit:
        raise SkipTest

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

def test_filters_text():
    text = dexy.commands.filters_text()
    assert "pyg, pygments : Apply Pygments syntax highlighting." in text

def test_filters_text_single_alias():
    text = dexy.commands.filters_text(alias="pyg")
    assert "pyg, pygments" in text

def test_filters_text_versions():
    text = dexy.commands.filters_text(versions=True)
    assert "Installed version: Python" in text

def test_filters_text_single_alias_source():
    text = dexy.commands.filters_text(alias="pyg", source=True)
    assert "pyg, pygments" in text
    assert "class" in text
    assert "PygmentsFilter" in text
    assert not "class PygmentsFilter" in text

def test_filters_text_single_alias_source_nocolor():
    text = dexy.commands.filters_text(alias="pyg", source=True, nocolor=True)
    assert "pyg, pygments" in text
    assert "class PygmentsFilter" in text

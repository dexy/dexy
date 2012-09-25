from StringIO import StringIO
from dexy.version import DEXY_VERSION
from dexy.tests.utils import tempdir
from mock import patch
import dexy.commands
import os
import sys

@patch.object(sys, 'argv', ['dexy', 'grep', '-expr', 'hello'])
def test_grep():
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
def test_run_help(stdout):
    with tempdir():
        dexy.commands.run()
        assert os.path.exists('artifacts')

@patch.object(sys, 'argv', ['dexy', 'viewer:ping'])
@patch('sys.stdout', new_callable=StringIO)
def test_viewer_command(stdout):
    dexy.commands.run()
    assert "pong" in stdout.getvalue()

@patch.object(sys, 'argv', ['dexy', 'conf'])
@patch('sys.stdout', new_callable=StringIO)
def test_conf_command(stdout):
    with tempdir():
        dexy.commands.run()
        assert os.path.exists("dexy.conf")
        assert "has been written" in stdout.getvalue()

def test_filters_text():
    text = dexy.commands.filters_text()
    assert "PygmentsFilter (pyg, pygments) Apply Pygments syntax highlighting." in text

def test_filters_text_single_alias():
    text = dexy.commands.filters_text(alias="pyg")
    assert "Aliases: pyg, pygments" in text

def test_filters_text_versions():
    text = dexy.commands.filters_text(versions=True)
    assert "Installed version: Python" in text

def test_filters_text_single_alias_source():
    text = dexy.commands.filters_text(alias="pyg", source=True)
    assert "Aliases: pyg, pygments" in text
    assert "class" in text
    assert "PygmentsFilter" in text
    assert not "class PygmentsFilter" in text

def test_filters_text_single_alias_source_nocolor():
    text = dexy.commands.filters_text(alias="pyg", source=True, nocolor=True)
    assert "Aliases: pyg, pygments" in text
    assert "class PygmentsFilter" in text

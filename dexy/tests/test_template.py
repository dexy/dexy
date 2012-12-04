from dexy.plugins.templates import DefaultTemplate
from dexy.tests.utils import tempdir
import os

def test_run():
    with tempdir():
        DefaultTemplate.run("test")
        assert not os.path.exists("dexy.rst")

def test_dexy():
    for batch in DefaultTemplate.dexy():
        assert 'jinja' in batch.filters_used()
        assert "Doc:hello.txt|jinja" in batch.lookup_table
        assert "Doc:dexy.rst|jinja|rst2html" in batch.lookup_table

def test_validate_default():
    DefaultTemplate.validate()

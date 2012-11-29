from dexy.plugins.templates import DefaultTemplate
from dexy.tests.utils import tempdir

def test_run():
    with tempdir():
        DefaultTemplate.run("test")

def test_dexy():
    batch = DefaultTemplate.dexy()
    assert 'jinja' in batch.filters_used()
    assert "Doc:hello.txt|jinja" in batch.lookup_table

def test_validate_default():
    DefaultTemplate.validate()

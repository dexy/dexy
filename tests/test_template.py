from dexy.templates.standard import DefaultTemplate
from tests.utils import tempdir
import os

def test_run():
    with tempdir():
        DefaultTemplate().generate("test")
        assert not os.path.exists("dexy.rst")

def test_dexy():
    for wrapper in DefaultTemplate().dexy():
        batch = wrapper.batch
        assert 'jinja' in batch.filters_used
        assert "doc:hello.txt|jinja" in batch.docs
        assert "doc:dexy.rst|jinja|rst2html" in batch.docs

def test_validate_default():
    DefaultTemplate().validate()

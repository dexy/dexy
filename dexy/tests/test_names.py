from dexy.exceptions import UserFeedback
from dexy.doc import Doc
from dexy.tests.utils import wrap
from nose.tools import raises
import os

def test_custom_name():
    with wrap() as wrapper:
        doc = Doc(
                "data.txt",
                canonical_name="data.abc",
                contents="12345.67",
                wrapper=wrapper
                )
        wrapper.run_docs(doc)

        assert doc.output().name == "data.abc"

def test_custom_name_in_subdir():
    with wrap() as wrapper:
        doc = Doc(
                "data.txt",
                canonical_name="subdir/data.abc",
                contents="12345.67",
                wrapper=wrapper
                )
        wrapper.run_docs(doc)
        wrapper.report()

        assert doc.output().name == "subdir/data.abc"
        assert doc.output().parent_dir() == "subdir"

def test_custom_name_with_args():
    with wrap() as wrapper:
        doc = Doc(
                "data.txt",
                canonical_name="%(bar)s/data-%(foo)s.abc",
                foo='bar',
                bar='baz',
                contents="12345.67",
                wrapper=wrapper
                )
        wrapper.run_docs(doc)
        wrapper.report()

        assert doc.output().name == "baz/data-bar.abc"
        assert doc.output().parent_dir() == "baz"
        assert os.path.exists("output/baz/data-bar.abc")

@raises(UserFeedback)
def test_custom_name_with_evil_args():
    with wrap() as wrapper:
        doc = Doc(
                "data.txt",
                canonical_name="/%(bar)s/data-%(foo)s.abc",
                foo='bar',
                bar='baz',
                contents="12345.67",
                wrapper=wrapper
                )
        wrapper.run_docs(doc)

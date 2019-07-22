from dexy.data import Data
from dexy.doc import Doc
from dexy.exceptions import UserFeedback
from nose.tools import raises
from tests.utils import wrap

def test_create_doc_with_one_filter():
    with wrap() as wrapper:
        doc = Doc("foo.txt|dexy", wrapper, [], contents="foo")

        assert len(doc.filters) == 1
        f = doc.filters[0]

        assert f.doc == doc
        assert not f.prev_filter
        assert not f.next_filter

        wrapper.run_docs(doc)

def test_create_doc_with_two_filters():
    with wrap() as wrapper:
        doc = Doc("foo.txt|dexy|dexy", wrapper, [], contents="foo")
        assert len(doc.filters) == 2

        f1, f2 = doc.filters

        assert f1.doc == doc
        assert f2.doc == doc

        assert f1.next_filter == f2
        assert f2.prev_filter == f1

        assert not f1.prev_filter
        assert not f2.next_filter

@raises(UserFeedback)
def test_blank_alias():
    with wrap() as wrapper:
        Doc("abc.txt|", wrapper, [], contents='foo')

def test_output_is_data():
    with wrap() as wrapper:
        doc = Doc("abc.txt", wrapper, [], contents="these are the contents")
        wrapper.run_docs(doc)
        assert isinstance(doc.output_data(), Data)

def test_create_virtual_initial_artifact():
    with wrap() as wrapper:
        doc = Doc("abc.txt", wrapper, [], contents="these are the contents")
        wrapper.run_docs(doc)
        assert doc.output_data().__class__.__name__ == "Generic"

from dexy.common import OrderedDict
from dexy.data import Data
from dexy.doc import Doc
from dexy.exceptions import UserFeedback
from dexy.tests.utils import wrap
from nose.tools import raises
import os

def test_create_doc_with_one_filter():
    with wrap() as wrapper:
        doc = Doc("foo.txt|dexy", wrapper, [], contents="foo")

        assert len(doc.filters) == 1
        f = doc.filters[0]

        assert f.doc == doc
        assert not f.prev_filter
        assert not f.next_filter

        print repr(doc.initial_data)
        print os.listdir(".cache/0a")

        doc.run()
        print os.listdir(".cache/0a")

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
        doc = Doc("abc.txt|", wrapper=wrapper)
        doc.populate()

def test_output_is_data():
    with wrap() as wrapper:
        doc = Doc("abc.txt", contents="these are the contents", wrapper=wrapper)
        wrapper.run_docs(doc)
        assert isinstance(doc.output(), Data)

def test_create_virtual_initial_artifact():
    with wrap() as wrapper:
        doc = Doc("abc.txt", contents="these are the contents", wrapper=wrapper)
        wrapper.run_docs(doc)
        assert doc.children[0].__class__.__name__ == "InitialVirtualArtifact"
        assert doc.children[0].output_data.__class__.__name__ == "Generic"

def test_create_virtual_initial_artifact_with_dict():
    with wrap() as wrapper:
        od_contents = OrderedDict()
        od_contents['1'] = "these are the contents"
        doc = Doc("abc.txt", contents = od_contents, wrapper=wrapper)
        wrapper.run_docs(doc)
        assert doc.children[0].output_data.__class__.__name__ == "Sectioned"

def test_doc_setup():
    with wrap() as wrapper:
        with open("abc.txt", "w") as f:
            f.write("def")

        wrapper.walk()

        doc = Doc("abc.txt|dexy|dexy", wrapper=wrapper)

        doc.populate()

        for child in doc.children:
            child.setup()

        doc.setup()

        assert doc.key == "abc.txt|dexy|dexy"
        assert doc.name == "abc.txt"
        assert doc.filters == ["dexy", "dexy"]

        assert doc.children[0].key == "abc.txt"
        assert doc.children[1].key == "abc.txt|dexy"
        assert doc.children[2].key == "abc.txt|dexy|dexy"

        assert doc.children[0].__class__.__name__ == "InitialArtifact"
        assert doc.children[1].__class__.__name__ == "FilterArtifact"
        assert doc.children[2].__class__.__name__ == "FilterArtifact"

        assert not hasattr(doc.children[0], 'next_filter_alias')
        assert doc.children[1].next_filter_alias == "dexy"
        assert doc.children[2].next_filter_alias == None

        assert not doc.children[0].prior
        assert doc.children[1].prior.__class__.__name__ == "InitialArtifact"
        assert doc.children[2].prior.__class__.__name__ == "FilterArtifact"

        assert not doc.children[0].prior
        assert doc.children[1].prior.key == "abc.txt"
        assert doc.children[2].prior.key == "abc.txt|dexy"


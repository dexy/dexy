from dexy.common import OrderedDict
from dexy.data import Data
from dexy.doc import Doc
from dexy.doc import PatternDoc
from dexy.exceptions import UserFeedback
from dexy.filter import DexyFilter
from dexy.tests.utils import wrap
from nose.tools import raises

@raises(UserFeedback)
def test_blank_alias():
    with wrap() as wrapper:
        doc = Doc("abc.txt|", wrapper=wrapper)
        doc.populate()

@raises(UserFeedback)
def test_blank_alias_exception():
    doc = Doc("foo")
    doc.filter_class_for_alias("")

def test_filter_class_for_alias():
    doc = Doc("foo")
    filter_class = doc.filter_class_for_alias("dexy")
    assert filter_class == DexyFilter

def test_output_is_data():
    with wrap() as wrapper:
        doc = Doc("abc.txt", contents="these are the contents", wrapper=wrapper)
        wrapper.run_docs(doc)
        assert isinstance(doc.output(), Data)

def test_create_doc_with_child():
    with wrap() as wrapper:
        doc = Doc("parent.txt", Doc("child.txt", wrapper=wrapper), wrapper=wrapper)
        doc.populate()
        assert doc.key == "parent.txt"
        assert doc.children[0].key == "child.txt"
        assert doc.children[1].key == "parent.txt"

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

def test_create_doc_with_filters():
    with wrap() as wrapper:
        doc = Doc("abc.txt|outputabc", contents="these are the contents", wrapper=wrapper)
        wrapper.run_docs(doc)

def test_doc_setup():
    with wrap() as wrapper:
        with open("abc.txt", "w") as f:
            f.write("def")

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

def test_setup_pattern_doc_no_filters():
    with wrap() as wrapper:
        doc = PatternDoc("*.txt", wrapper=wrapper)
        doc.populate()
        doc.setup()
        assert doc.file_pattern == "*.txt"
        assert doc.filter_aliases == []

def test_setup_pattern_doc_one_filter():
    with wrap() as wrapper:
        doc = PatternDoc("*.txt|dexy", wrapper=wrapper)
        doc.populate()
        doc.setup()
        assert doc.file_pattern == "*.txt"
        assert doc.filter_aliases == ['dexy']

def test_setup_pattern_doc_many_filters():
    with wrap() as wrapper:
        doc = PatternDoc("*.txt|dexy|dexy|dexy", wrapper=wrapper)
        doc.populate()
        doc.setup()
        assert doc.file_pattern == "*.txt"
        assert doc.filter_aliases == ['dexy', 'dexy', 'dexy']

def test_pattern_doc_args():
    with wrap() as wrapper:
        with open("hello.txt", "w") as f:
            f.write("hello!")

        wrapper.setup_batch()

        doc = PatternDoc("*.txt", foo="bar", wrapper=wrapper)
        doc.populate()
        assert doc.args['foo'] == 'bar'
        assert isinstance(doc.children[0], Doc)
        assert doc.children[0].key == "hello.txt"
        assert doc.children[0].args['foo'] == 'bar'

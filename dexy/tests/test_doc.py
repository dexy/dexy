from dexy.doc import Doc
from dexy.doc import PatternDoc
from ordereddict import OrderedDict
from dexy.exceptions import *
from dexy.filter import DexyFilter
from dexy.data import Data
from dexy.plugins.example_filters import AbcExtension
from dexy.tests.utils import tempdir, temprun
from nose.tools import raises

@raises(UserFeedback)
def test_blank_alias():
    with temprun():
        Doc("abc.txt|")

@raises(BlankAlias)
def test_blank_alias_exception():
    Doc.filter_class_for_alias("")

def test_filter_class_for_alias():
    filter_class = Doc.filter_class_for_alias("dexy")
    assert filter_class == DexyFilter

def test_output_is_data():
    with temprun() as runner:
        doc = Doc("abc.txt", contents="these are the contents")
        runner.run(doc)
        assert isinstance(doc.output(), Data)

### @export "test-create-doc-with-child"
def test_create_doc_with_child():
    with tempdir():
        doc = Doc("parent.txt", Doc("child.txt"))
        assert doc.key == "parent.txt"
        assert doc.children[0].key == "child.txt"
        assert doc.children[1].key == "parent.txt"
### @end

def test_create_virtual_initial_artifact():
    with temprun() as runner:
        doc = Doc("abc.txt", contents="these are the contents")
        runner.run(doc)
        assert doc.children[0].__class__.__name__ == "InitialVirtualArtifact"
        assert doc.children[0].output_data.__class__.__name__ == "GenericData"

def test_create_virtual_initial_artifact_with_dict():
    with temprun() as runner:
        od_contents = OrderedDict()
        od_contents['1'] = "these are the contents"
        doc = Doc("abc.txt", contents = od_contents)
        runner.run(doc)
        assert doc.children[0].output_data.__class__.__name__ == "SectionedData"

def test_create_doc_with_filters():
    with temprun() as runner:
        doc = Doc("abc.txt|outputabc", contents="these are the contents")
        runner.run(doc)

def test_doc_setup():
    doc = Doc("abc.txt|dexy|dexy")
    assert doc.key == "abc.txt|dexy|dexy"
    assert doc.name == "abc.txt"
    assert doc.filters == ["dexy", "dexy"]

    assert doc.children[0].key == "abc.txt"
    assert doc.children[1].key == "abc.txt|dexy"
    assert doc.children[2].key == "abc.txt|dexy|dexy"

    assert doc.children[0].__class__.__name__ == "InitialVirtualArtifact"
    assert doc.children[1].__class__.__name__ == "FilterArtifact"
    assert doc.children[2].__class__.__name__ == "FilterArtifact"

    assert not hasattr(doc.children[0], 'next_filter_alias')
    assert doc.children[1].next_filter_alias == "dexy"
    assert doc.children[2].next_filter_alias == None

    assert not doc.children[0].prior
    assert doc.children[1].prior.__class__.__name__ == "InitialVirtualArtifact"
    assert doc.children[2].prior.__class__.__name__ == "FilterArtifact"

    assert not doc.children[0].prior
    assert doc.children[1].prior.key == "abc.txt"
    assert doc.children[2].prior.key == "abc.txt|dexy"

def test_doc_run():
    with temprun() as runner:
        doc = Doc("abc.txt|dexy|dexy")
        assert not hasattr(doc, 'runner')
        doc.run(runner)
        assert hasattr(doc, 'runner')
        assert doc.key in runner.completed.keys()

def test_setup_pattern_doc_no_filters():
    doc = PatternDoc("*.txt")
    assert doc.file_pattern == "*.txt"
    assert doc.filter_aliases == []

def test_setup_pattern_doc_one_filter():
    doc = PatternDoc("*.txt|dexy")
    assert doc.file_pattern == "*.txt"
    assert doc.filter_aliases == ['dexy']

def test_setup_pattern_doc_many_filters():
    doc = PatternDoc("*.txt|dexy|dexy|dexy")
    assert doc.file_pattern == "*.txt"
    assert doc.filter_aliases == ['dexy', 'dexy', 'dexy']

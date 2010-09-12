from dexy.controller import Controller
from dexy.document import Document

def setup_controller():
    controller = Controller()
    controller.setup_and_run("tests/data")
    return controller

def setup_doc():
    controller = setup_controller()
    doc = controller.members['tests/data/simple.R|pyg']
    assert isinstance(doc, Document)
    return doc

def test_init():
    """document: filters should be processed correctly"""
    doc = Document("data/test.R|abc")
    assert doc.name == "data/test.R"
    assert doc.filters == ['abc']

    doc.filters += ['def', 'xyz']
    assert doc.filters == ['abc', 'def', 'xyz']

    assert doc.key() == "data/test.R|abc|def|xyz"

def test_complete():
    """document: after controller has run"""
    doc = setup_doc()
    assert doc.key() == "tests/data/simple.R|pyg"

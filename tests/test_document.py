from dexy.controller import Controller
from dexy.document import Document
from dexy.artifacts.file_system_artifact import FileSystemJsonArtifact

def setup_controller():
    controller = Controller()
    controller.artifact_class = FileSystemJsonArtifact
    controller.config_file = '.dexy'
    controller.load_config('tests/data')
    controller.setup_and_run()
    return controller

def setup_doc():
    controller = setup_controller()
    doc = controller.members['tests/data/simple.R|pyg']
    assert isinstance(doc, Document)
    return doc

def test_init():
    """document: filters should be processed correctly"""
    doc = Document(FileSystemJsonArtifact, "data/test.R|abc")
    assert doc.name == "data/test.R"
    assert doc.filters == ['abc']

    doc.filters += ['def', 'xyz']
    assert doc.filters == ['abc', 'def', 'xyz']

    assert doc.key() == "data/test.R|abc|def|xyz"

def test_complete():
    """document: after controller has run"""
    doc = setup_doc()
    assert doc.key() == "tests/data/simple.R|pyg"

from dexy.controller import Controller
from dexy.document import Document
from dexy.artifacts.file_system_json_artifact import FileSystemJsonArtifact
import os

def setup_controller():
    controller = Controller()
    controller.artifacts_dir = 'artifacts'
    if not os.path.isdir(controller.artifacts_dir):
        os.mkdir(controller.artifacts_dir)
    controller.artifact_class = FileSystemJsonArtifact
    controller.allow_remote = True
    controller.config = {
        'tests/data' : {
            "@simple.py|pyg" : {
                "contents" : "x = 5\nx^2"
            }
        }
    }
    controller.setup_and_run()
    return controller

def setup_doc():
    controller = setup_controller()
    doc = controller.members['tests/data/simple.py|pyg']
    assert isinstance(doc, Document)
    return doc

def setup_artifact():
    doc = setup_doc()
    return doc.final_artifact()

def test_artifact_hash_dict():
    artifact = setup_artifact()
    hash_dict = artifact.hash_dict()
    for k in hash_dict.keys():
        assert k in artifact.HASH_WHITELIST

    # hashstring shouldn't change
    hashstring = artifact.hashstring
    artifact.set_hashstring
    assert artifact.hashstring == hashstring

def test_init():
    """document: filters should be processed correctly"""
    doc = Document(FileSystemJsonArtifact, "data/test.py|abc")
    assert doc.name == "data/test.py"
    assert doc.filters == ['abc']

    doc.filters += ['def', 'xyz']
    assert doc.filters == ['abc', 'def', 'xyz']

    assert doc.key() == "data/test.py|abc|def|xyz"

def test_complete():
    """document: after controller has run"""
    doc = setup_doc()
    assert doc.key() == "tests/data/simple.py|pyg"

from dexy.artifact import Artifact
from dexy.controller import Controller
from dexy.document import Document
from dexy.handler import DexyHandler
import os.path
import imghdr

def setup_controller():
    controller = Controller()
    controller.setup_and_run("tests/data")
    return controller

def test_handlers():
    """controller: find_handlers() should not raise errors"""
    controller = Controller()
    handlers = controller.find_handlers()
    assert handlers[''] == DexyHandler

def test_members():
    """controller: files and filters to be run should be identified correctly"""
    controller = setup_controller()
    assert controller.members.keys() == [
        'tests/data/simple.R|pyg',
        'tests/data/graph.R|pyg',
        'tests/data/simple.R|jinja|r|pyg',
        'tests/data/graph.R|jinja|r|pyg'
    ]

def test_r():
    """controller: jpeg should have been generated and added to additional_inputs"""
    controller = setup_controller()
    doc = controller.members['tests/data/graph.R|jinja|r|pyg']
    assert isinstance(doc, Document)

    artifact = doc.artifacts[-1]
    assert isinstance(artifact, Artifact)
    
    assert artifact.additional_inputs.has_key('graph')
    assert os.path.exists(artifact.additional_inputs['graph'])
    image_type = imghdr.what(artifact.additional_inputs['graph'])
    assert image_type == 'jpeg'
    

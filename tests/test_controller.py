from dexy.artifact import Artifact
from dexy.controller import Controller
from dexy.document import Document
from dexy.handler import DexyHandler
import os.path
import imghdr

def setup_controller(config_file = None):
    controller = Controller()
    if config_file:
        controller.config_file = config_file
    controller.setup_and_run("tests/data")
    return controller

def test_handlers():
    """controller: find_handlers() should not raise errors"""
    controller = Controller()
    handlers = controller.find_handlers()
    assert handlers['dexy'] == DexyHandler

def test_members():
    """controller: files and filters to be run should be identified correctly"""
    controller = setup_controller()
    print controller.members.keys()
    assert controller.members.keys() == [
        'tests/data/simple.R|fn|r|pyg',
        'tests/data/graph.R|fn|r|pyg',
        'tests/data/simple.R|pyg',
        'tests/data/graph.R|pyg'
    ]


def test_r():
    """controller: jpeg should have been generated and added to additional_inputs"""
    controller = setup_controller()
    doc = controller.members['tests/data/graph.R|fn|r|pyg']
    assert isinstance(doc, Document)

    artifact = doc.artifacts[-1]
    assert isinstance(artifact, Artifact)
    
    assert artifact.additional_inputs.has_key('graph')

    full_path = os.path.join(controller.artifacts_dir, artifact.additional_inputs['graph'])
    assert os.path.exists(full_path)
    image_type = imghdr.what(full_path)
    assert image_type == 'jpeg'


def test_config_list_filters_separately():
    controller = setup_controller("list-filters-separately.dexy")
    assert controller.members.keys() == [
        'tests/data/simple.R|pyg|l',
        'tests/data/graph.R|pyg|l'
    ]

def test_config_nested_doc():
    controller = setup_controller("nested-doc.dexy")
    assert controller.members.keys() == [
        'tests/data/graph.R|r',
        'tests/data/simple.R|r'
    ]

def test_config_both_filter_styles():
    controller = setup_controller("both-filter-styles.dexy")
    assert controller.members.keys() == [
        'tests/data/simple.R|pyg|l',
        'tests/data/graph.R|pyg|l'
    ]

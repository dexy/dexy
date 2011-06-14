from dexy.artifacts.file_system_json_artifact import FileSystemJsonArtifact
from dexy.controller import Controller
from dexy.dexy_filter import DexyFilter
import os.path

def setup_controller(config_file = None):
    controller = Controller()
    controller.artifacts_dir = 'artifacts'
    if not os.path.isdir(controller.artifacts_dir):
        os.mkdir(controller.artifacts_dir)
    controller.artifact_class = FileSystemJsonArtifact
    if config_file:
        controller.config_file = config_file
    else:
        controller.config_file = '.dexy'
    controller.load_config("tests/data")
    controller.setup_and_run()
    return controller

def test_handlers():
    """controller: find_handlers() should not raise errors"""
    controller = Controller()
    handlers = controller.find_handlers()
    assert handlers['dexy'] == DexyFilter

def test_members():
    """controller: files and filters to be run should be identified correctly"""
    controller = setup_controller()
    assert sorted(controller.members.keys()) == [
        'tests/data/graph.R|fn|r|pyg',
        'tests/data/graph.R|pyg',
        'tests/data/simple.R|fn|r|pyg',
        'tests/data/simple.R|pyg'
    ]

#def test_r():
#    """controller: jpeg should have been generated and added to additional_inputs"""
#    controller = setup_controller()
#    doc = controller.members['tests/data/graph.R|fn|r|pyg']
#    assert isinstance(doc, Document)
#
#    artifact = doc.final_artifact()
#    assert isinstance(artifact, Artifact)
#
#    graph_artifact = artifact.additional_inputs['graph']
#    assert os.path.exists(graph_artifact.filepath())
#    image_type = imghdr.what(graph_artifact.filepath())
#    assert image_type == 'jpeg'
#
#    print dir(graph_artifact)


def test_config_list_filters_separately():
    controller = setup_controller("list-filters-separately.dexy")
    assert sorted(controller.members.keys()) == [
        'tests/data/graph.R|pyg|l',
        'tests/data/simple.R|pyg|l'
    ]

#def test_config_nested_doc():
#    controller = setup_controller("nested-doc.dexy")
#    assert sorted(controller.members.keys()) == [
#        'tests/data/graph.R|r',
#        'tests/data/simple.R|r'
#    ]

def test_config_both_filter_styles():
    controller = setup_controller("both-filter-styles.dexy")
    assert sorted(controller.members.keys()) == [
        'tests/data/graph.R|pyg|l',
        'tests/data/simple.R|pyg|l'
    ]

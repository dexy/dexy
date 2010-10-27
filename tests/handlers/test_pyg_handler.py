from dexy.artifact import Artifact
from handlers.pyg_handler import PygHandler
import helper

def setup_handler():
    h = PygHandler()
    h.ext = '.rb'
    h.artifact = Artifact()
    h.artifact.ext = '.tex'
    h.artifact.hashstring = "abc"
    h.artifact.artifacts_dir = 'artifacts'
    return h

def test_process_dict():
    helper.test_process_dict(setup_handler(), 'pyg.txt')

def test_process(): 
    helper.test_process(setup_handler(), 'pyg.txt', 'process_dict')


from dexy.artifact import Artifact
from handlers.subprocess import ProcessInteractiveHandler
import helper

def setup_handler():
    h = ProcessInteractiveHandler()
    h.ext = '.py'
    h.artifact = Artifact()
    h.artifact.data_dict = {}
    return h

def test_process():
   helper.test_process(setup_handler(), 'pycon.txt')

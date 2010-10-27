from dexy.artifact import Artifact
from handlers.subprocess import ProcessLinewiseInteractiveHandler
import helper

def setup_handler():
    h = ProcessLinewiseInteractiveHandler()
    h.ext = '.py'
    h.artifact = Artifact()
    h.artifact.data_dict = {}
    return h

def test_process():
   helper.test_process(setup_handler(), 'pycon.txt')

from dexy.artifact import Artifact
from dexy.handler import DexyHandler
from handlers.python import IdioHandler
import helper

def setup_handler():
    h = IdioHandler()
    h.ext = '.py'
    h.artifact = Artifact()
    h.artifact.ext = '.html'
    h.artifact.hashstring = 'filename'
    return h

def test_process_text_to_dict():
    h = setup_handler()
#    input_text = read_file("idio.txt")
    output_dict = h.process_text_to_dict(input_text)
    assert output_dict['hello-world'] == output_text_1
    assert output_dict['this-is-the-end'] == output_text_2

def test_process(): 
    helper.test_process(setup_handler(), 'idio.txt')

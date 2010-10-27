from dexy.artifact import Artifact
from dexy.handler import DexyHandler
from handlers.jinja_handler import JinjaHandler

input_text = """
One plus one equals {{ 1+1 }}

"""

output_text = """
One plus one equals 2
"""

def setup_handler():
    h = JinjaHandler()
    h.ext = '.txt'
    h.artifact = Artifact()
    h.artifact.ext = '.txt'
    h.artifact.input_artifacts = {}
    h.artifact.data_dict = {}
    return h

def test_process_text():
    h = setup_handler()
    output = h.process_text(input_text)
    assert output == output_text

def test_process(): 
    h = setup_handler()
    h.artifact.input_data_dict = {'1' : input_text}
    assert h.process() == "process_text"
    assert h.artifact.data_dict == {'1' : output_text}

from dexy.artifact import Artifact
from dexy.handler import DexyHandler
from handlers.pyg_handler import IdioHandler
import helper

def setup_handler():
    h = IdioHandler()
    h.ext = '.py'
    h.artifact = Artifact()
    h.artifact.ext = '.html'
    h.artifact.hashstring = 'filename'
    h.artifact.artifacts_dir = 'artifacts'
    return h

def test_process_text_to_dict():
    output_text_1 =  """<div class=\"highlight\"><pre><span class=\"k\">print</span> <span class=\"s\">&quot;hello, world&quot;</span>
</pre></div>
"""
    output_text_2 = """<div class=\"highlight\"><pre><span class=\"k\">print</span> <span class=\"s\">&quot;this is the end&quot;</span>
</pre></div>
"""
    h = setup_handler()
    input_text = helper.read_file("idio.txt")
    output_dict = h.process_text_to_dict(input_text)
    assert output_dict['hello-world'] == output_text_1
    assert output_dict['this-is-the-end'] == output_text_2


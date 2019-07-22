from tests.utils import TEST_DATA_DIR
from dexy.doc import Doc
from tests.utils import wrap
import os

markdown_file = os.path.join(TEST_DATA_DIR, "markdown-test.md")

def run_kramdown(ext):
    with open(markdown_file, 'r') as f:
        example_markdown = f.read()

    with wrap() as wrapper:
        node = Doc("markdown.md|kramdown",
                wrapper,
                [],
                kramdown = { 'ext' : ext },
                contents = example_markdown
                )
        wrapper.run_docs(node)
        assert node.output_data().is_cached()
        return node.output_data()

def test_kramdown_html():
    html = str(run_kramdown(".html"))
    assert """<h2 id="download">""" in html

def test_kramdown_tex():
    tex = str(run_kramdown(".tex"))
    assert "\subsection" in tex

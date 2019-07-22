from tests.utils import wrap
from tests.utils import TEST_DATA_DIR
from dexy.doc import Doc
import os

markdown_file = os.path.join(TEST_DATA_DIR, "markdown-with-python.md")

def run_filter(alias):
    with open(markdown_file, 'r') as f:
        example_markdown = f.read()

    with wrap() as wrapper:
        node = Doc("example.md|%s" % alias,
                wrapper,
                [],
                contents = example_markdown
                )
        wrapper.run_docs(node)
        assert node.output_data().is_cached()
        return node.output_data()


def test_markdown_to_ipynb():
    print(run_filter("mdjup"))

def test_markdown_to_generic():
    print(run_filter("mdsections"))

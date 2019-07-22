from tests.utils import TEST_DATA_DIR
from dexy.doc import Doc
from tests.utils import wrap
import os

sweave_file = os.path.join(TEST_DATA_DIR, "example-2.Snw")

def test_sweave_filter():
    with open(sweave_file, 'r') as f:
        sweave_content = f.read()

    with wrap() as wrapper:
        node = Doc("example.Snw|sweave",
                wrapper,
                [],
                contents = sweave_content
              )
        wrapper.run_docs(node)
        assert node.output_data().is_cached()
        assert "Coefficients:" in str(node.output_data())

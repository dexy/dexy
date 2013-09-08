from dexy.doc import Doc
from tests.utils import TEST_DATA_DIR
from tests.utils import assert_output
from tests.utils import runfilter
from tests.utils import wrap
from nose.exc import SkipTest
import os
import shutil

def test_phantomjs_render_filter():
    with runfilter("phrender", "<p>hello</p>") as doc:
        assert doc.output_data().is_cached()

def test_phantomjs_stdout_filter():
    assert_output('phantomjs', PHANTOM_JS, "Hello, world!\n")

def test_casperjs_svg2pdf_filter():
    # TODO find smaller file - make test go faster?
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'butterfly.svg')
        shutil.copyfile(orig, 'butterfly.svg')

        from dexy.wrapper import Wrapper
        wrapper = Wrapper()

        node = Doc("butterfly.svg|svg2pdf", wrapper)

        wrapper.run_docs(node)

        assert node.output_data().is_cached()
        assert node.output_data().filesize() > 1000

def test_casperjs_stdout_filter():
    with wrap() as wrapper:
        node = Doc("example.js|casperjs",
                wrapper,
                [],
                contents=CASPER_JS,
                casperjs={"add-new-files" : True }
                )

        wrapper.run_docs(node)

        assert 'doc:google.pdf' in wrapper.nodes

        try:
            assert 'doc:cookies.txt' in wrapper.nodes
        except AssertionError:
            import urllib
            try:
                urllib.urlopen("http://google.com")
                raise
            except IOError:
                raise SkipTest("internet not available, skipping test")
            else:
                raise

PHANTOM_JS = """
console.log('Hello, world!');
phantom.exit();
"""

CASPER_JS = """
var links = [];
var casper = require('casper').create();

casper.start('http://google.com/', function() {
    this.capture('google.pdf');
});

casper.run();
"""

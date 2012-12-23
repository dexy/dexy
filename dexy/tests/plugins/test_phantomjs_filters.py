from dexy.node import DocNode
from dexy.tests.utils import TEST_DATA_DIR
from dexy.tests.utils import assert_output
from dexy.tests.utils import runfilter
from dexy.tests.utils import wrap
from nose.exc import SkipTest
import os
import shutil

def test_phantomjs_render_filter():
    with runfilter("phrender", "<p>hello</p>") as doc:
        assert doc.output().is_cached()

def test_phantomjs_stdout_filter():
    assert_output('phantomjs', PHANTOM_JS, "Hello, world!\n")

def test_casperjs_svg2pdf_filter():
    # TODO find smaller file - make test go faster?
    with wrap() as wrapper:
        orig = os.path.join(TEST_DATA_DIR, 'butterfly.svg')
        shutil.copyfile(orig, 'butterfly.svg')
        node = DocNode("butterfly.svg|svg2pdf",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().is_cached()
        assert doc.output().filesize() > 1000

def test_casperjs_stdout_filter():
    with wrap() as wrapper:
        node = DocNode("example.js|casperjs",
                contents=CASPER_JS,
                wrapper=wrapper)

        wrapper.run_docs(node)

        assert 'google.pdf' in wrapper.batch.doc_names()

        try:
            assert 'cookies.txt' in wrapper.batch.doc_names()
        except AssertionError as e:
            import urllib
            try:
                urllib.urlopen("http://google.com")
                raise e
            except IOError:
                raise SkipTest


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

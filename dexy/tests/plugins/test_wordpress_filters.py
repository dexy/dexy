from dexy.doc import Doc
from dexy.plugins.wordpress_filters import WordPressFilter
from dexy.tests.utils import TEST_DATA_DIR
from dexy.tests.utils import wrap
from dexy.tests.utils import divert_stdout
from mock import patch
import dexy.exceptions
import json
import os
import shutil

def test_docmd_create_keyfile():
    with wrap():
        assert not os.path.exists(".dexyapis")
        WordPressFilter.docmd_create_keyfile()
        assert os.path.exists(".dexyapis")

def test_docmd_create_keyfile_if_exists():
    with wrap():
        with open(".dexyapis", "w") as f:
            f.write("{}")
        assert os.path.exists(".dexyapis")
        try:
            WordPressFilter.docmd_create_keyfile()
            assert False, ' should raise exception'
        except dexy.exceptions.UserFeedback as e:
            assert ".dexyapis already exists" in e.message

def test_api_url_with_php_ending():
    with wrap():
        with open(".dexyapis", "wb") as f:
            json.dump({
                    "wordpress" : {"url" : "http://example.com/api/xmlrpc.php"}
                    }, f)

        url = WordPressFilter.api_url()
        assert url == "http://example.com/api/xmlrpc.php"

def test_api_url_without_php_ending():
    with wrap():
        with open(".dexyapis", "wb") as f:
            json.dump({ "wordpress" : {"url" : "http://example.com/api"} }, f)

        url = WordPressFilter.api_url()
        assert url == "http://example.com/api/xmlrpc.php"

def test_api_url_without_php_ending_with_trailing_slash():
    with wrap():
        with open(".dexyapis", "wb") as f:
            json.dump({ "wordpress" : {"url" : "http://example.com/api/"} }, f)

        url = WordPressFilter.api_url()
        assert url == "http://example.com/api/xmlrpc.php"

def test_wordpress_without_doc_config_file():
    with wrap() as wrapper:
        doc = Doc("hello.txt|wp",
                contents = "hello, this is a blog post",
                wrapper=wrapper
                )

        try:
            wrapper.run_docs(doc)
            assert False, 'should raise exception'
        except dexy.exceptions.UserFeedback as e:
            assert "wordpress.json" in e.message
            assert "Filter wp" in e.message

def mk_wp_doc(wrapper):
    return Doc("hello.txt|wp",
            contents = "hello, this is a blog post",
            dirty = True,
            wrapper=wrapper
            )

ATTRS = {
        'return_value.metaWeblog.newPost.return_value' : 42,
        'return_value.metaWeblog.getPost.return_value' : {
            'permaLink' : 'http://example.com/blog/42'
            },
        'return_value.wp.getCategories.return_value' : [
            { 'categoryName' : 'foo' },
            { 'categoryName' : 'bar' }
            ],
        'return_value.wp.uploadFile.return_value' : {
            'url' : 'http://example.com/example.pdf'
            }
        }

@patch('xmlrpclib.ServerProxy', **ATTRS)
def test_wordpress(MockXmlrpclib):
    with wrap() as wrapper:
        with open("wordpress.json", "wb") as f:
            json.dump({}, f)

        with open(".dexyapis", "wb") as f:
            json.dump({
                'wordpress' : {
                    'url' : 'http://example.com',
                    'username' : 'foo',
                    'password' : 'bar'
                    }}, f)

        # Create new (unpublished) draft
        doc = mk_wp_doc(wrapper)
        wrapper.run_docs(doc)

        with open("wordpress.json", "rb") as f:
            result = json.load(f)

        assert result['postid'] == 42
        assert result['publish'] == False

        # Update existing draft
        doc = mk_wp_doc(wrapper)
        wrapper.run_docs(doc)
        assert doc.output().json_as_dict().keys() == ['permaLink']

        result['publish'] = True
        with open("wordpress.json", "wb") as f:
            json.dump(result, f)

        # Publish existing draft
        doc = mk_wp_doc(wrapper)
        wrapper.run_docs(doc)
        assert doc.output().as_text() == "http://example.com/blog/42"

        # Now, separately, test an image upload.
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        doc = Doc("example.pdf|wp",
                wrapper=wrapper)

        with open(".dexyapis", "wb") as f:
            json.dump({
                'wordpress' : {
                    'url' : 'http://example.com',
                    'username' : 'foo',
                    'password' : 'bar'
                    }}, f)

        wrapper.run_docs(doc)
        assert doc.output().as_text() == "http://example.com/example.pdf"

        # test list categories
        with divert_stdout() as stdout:
            WordPressFilter.docmd_list_categories()
            assert stdout.getvalue() == "categoryName\nfoo\nbar\n"

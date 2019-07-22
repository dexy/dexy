from dexy.doc import Doc
from tests.utils import TEST_DATA_DIR
from tests.utils import wrap
from tests.utils import capture_stdout
from mock import patch
import dexy.exceptions
import json
import os
import shutil
import dexy.filter
import dexy.wrapper

def test_docmd_create_keyfile():
    with wrap():
        assert not os.path.exists(".dexyapis")
        dexy.filter.Filter.create_instance("wp").docmd_create_keyfile()
        assert os.path.exists(".dexyapis")

def test_docmd_create_keyfile_if_exists():
    with wrap():
        with open(".dexyapis", "w") as f:
            f.write("{}")
        assert os.path.exists(".dexyapis")
        try:
            dexy.filter.Filter.create_instance("wp").docmd_create_keyfile()
            assert False, ' should raise exception'
        except dexy.exceptions.UserFeedback as e:
            assert ".dexyapis already exists" in e.message

def test_api_url_with_php_ending():
    with wrap():
        with open(".dexyapis", "w") as f:
            json.dump({
                    "wordpress" : {"url" : "http://example.com/api/xmlrpc.php"}
                    }, f)

        url = dexy.filter.Filter.create_instance("wp").api_url()
        assert url == "http://example.com/api/xmlrpc.php"

def test_api_url_without_php_ending():
    with wrap():
        with open(".dexyapis", "w") as f:
            json.dump({ "wordpress" : {"url" : "http://example.com/api"} }, f)

        url = dexy.filter.Filter.create_instance("wp").api_url()
        assert url == "http://example.com/api/xmlrpc.php"

def test_api_url_without_php_ending_with_trailing_slash():
    with wrap():
        with open(".dexyapis", "w") as f:
            json.dump({ "wordpress" : {"url" : "http://example.com/api/"} }, f)

        url = dexy.filter.Filter.create_instance("wp").api_url()
        assert url == "http://example.com/api/xmlrpc.php"

def test_wordpress_without_doc_config_file():
    with wrap() as wrapper:
        wrapper.debug = False
        doc = Doc("hello.txt|wp",
                contents = "hello, this is a blog post",
                wrapper=wrapper
                )

        wrapper.run_docs(doc)
        assert wrapper.state == 'error'

def mk_wp_doc(wrapper):
    doc = Doc("hello.txt|wp",
            contents = "hello, this is a blog post",
            dirty = True,
            wrapper=wrapper
            )
    for d in doc.datas():
        d.setup()
    return doc

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

@patch('xmlrpc.client.ServerProxy', **ATTRS)
def test_wordpress(MockXmlrpclib):
    with wrap():
        with open("wordpress.json", "w") as f:
            json.dump({}, f)

        with open(".dexyapis", "w") as f:
            json.dump({
                'wordpress' : {
                    'url' : 'http://example.com',
                    'username' : 'foo',
                    'password' : 'bar'
                    }}, f)

        # Create new (unpublished) draft
        wrapper = dexy.wrapper.Wrapper()
        doc = mk_wp_doc(wrapper)
        wrapper.run_docs(doc)

        with open("wordpress.json", "r") as f:
            result = json.load(f)

        assert result['postid'] == 42
        assert result['publish'] == False

        # Update existing draft
        wrapper = dexy.wrapper.Wrapper()
        doc = mk_wp_doc(wrapper)
        wrapper.run_docs(doc)
        assert list(doc.output_data().json_as_dict().keys()) == ['permaLink']

        result['publish'] = True
        with open("wordpress.json", "w") as f:
            json.dump(result, f)

        # Publish existing draft
        wrapper = dexy.wrapper.Wrapper()
        doc = mk_wp_doc(wrapper)
        wrapper.run_docs(doc)
        assert "http://example.com/blog/42" in str(doc.output_data())

        # Now, separately, test an image upload.
        orig = os.path.join(TEST_DATA_DIR, 'color-graph.pdf')
        shutil.copyfile(orig, 'example.pdf')
        from dexy.wrapper import Wrapper
        wrapper = Wrapper()
        doc = Doc("example.pdf|wp",
                wrapper=wrapper)

        with open(".dexyapis", "w") as f:
            json.dump({
                'wordpress' : {
                    'url' : 'http://example.com',
                    'username' : 'foo',
                    'password' : 'bar'
                    }}, f)

        wrapper.run_docs(doc)
        assert doc.output_data().as_text() == "http://example.com/example.pdf"

        # test list categories
        with capture_stdout() as stdout:
            dexy.filter.Filter.create_instance("wp").docmd_list_categories()
            assert stdout.getvalue() == "categoryName\nfoo\nbar\n"

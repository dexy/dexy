from dexy.tests.utils import run_dexy

def test_xml():
    contents = """<div id="abc">def</div>"""
    config = {"." : { "@example.html|xxml" : {"contents" : contents }}}

    for doc in run_dexy(config):
        doc.run()
        artifact = doc.last_artifact
        artifact.setup_kv_storage()
        assert artifact['abc:text'] == "def"
        assert artifact['abc:source'] == contents
        assert artifact['abc:lineno'] == 1

def test_html():
    contents = """<div id="abc">def</div>"""
    config = {"." : { "@example.html|htmlsec" : {"contents" : contents }}}

    for doc in run_dexy(config):
        doc.run()
        artifact = doc.last_artifact
        artifact.setup_kv_storage()
        assert artifact['abc:text'] == "def"
        assert artifact['abc:source'] == contents

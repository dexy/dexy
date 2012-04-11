from dexy.tests.utils import run_dexy

CONFIG = {
    "." : {
        "@packages.txt|pydoc" : { "contents" : "os" }
    }
}

def test_basic_filter():
    for doc in run_dexy(CONFIG):
        doc.run()
        artifact = doc.last_artifact
        assert artifact.ext == ".json"
        artifact.setup_kv_storage()
        assert "Directory tree generator." in artifact["os.walk:doc"]
        assert "Directory tree generator." in artifact._storage.retrieve("os.walk:doc")

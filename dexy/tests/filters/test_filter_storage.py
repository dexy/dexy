from dexy.dexy_filter import DexyFilter
from dexy.tests.utils import run_dexy
from dexy.tests.utils import set_filter_list

CONTENTS = "This is the first line.\nThis is the 2nd line."

CONFIG = {
    "." : {
        "@lines.txt|kvlines|-json" : { "contents" : CONTENTS, "kvlines" : {"ext" : ".json"}},
        "@lines.txt|kvlines|-kch" : { "contents" : CONTENTS, "kvlines" : {"ext" : ".kch"}},
        "@lines.txt|kvlines|-sqlite3" : { "contents" : CONTENTS, "kvlines" : {"ext" : ".sqlite3"}}
    }
}

class ConvertLinesToKeyValueStorageFilter(DexyFilter):
    ALIASES = ['kvlines']
    BINARY = True

    def process(self):
        self.artifact.setup_kv_storage()
        for i, line in enumerate(self.artifact.input_text().splitlines()):
            self.artifact._storage.append(str(i+1), line)
        self.artifact._storage.save()

def test_filter_storage():
    set_filter_list([ConvertLinesToKeyValueStorageFilter])
    for doc in run_dexy(CONFIG):
        doc.run()
        artifact = doc.last_artifact
        artifact.setup_kv_storage()
        assert artifact["1"] == "This is the first line."
        assert artifact["2"] == "This is the 2nd line."
        assert artifact._storage.mode == "read"
        assert artifact._storage.keys() == ["1", "2"]

CONTENT_CONFIG = {
    "." : {
        "@example.json" : { "binary" : True, "contents" : """{"abc" : 123 }""" }
        }
    }

def test_existing_content():
    for doc in run_dexy(CONTENT_CONFIG):
        artifact = doc.last_artifact
        assert artifact["abc"] == 123

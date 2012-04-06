from dexy.dexy_filter import DexyFilter
from dexy.tests.utils import run_dexy
from dexy.tests.utils import set_filter_list

CONTENTS = "This is the first line.\nThis is the 2nd line."

JSON_CONFIG = {
    "." : {
        "@lines.txt|kvstorage|-json" : { "contents" : CONTENTS, "kv-ext" : ".json"},
        "@lines.txt|kvstorage|-sqlite" : { "contents" : CONTENTS, "kv-ext" : ".sqlite3"},
        "@lines.txt|kvstorage|-kyoto" : { "contents" : CONTENTS, "kv-ext" : ".kch" }
    }
}

class KeyValueStorageFilter(DexyFilter):
    ALIASES = ['kvstorage']

    def process(self):
        self.artifact.setup_kv_storage()
        for i, line in enumerate(self.artifact.input_text().splitlines()):
            self.artifact.append_to_kv_storage(str(i+1), line)
        self.artifact.persist_kv_storage()
        self.artifact.data_dict = self.artifact.input_data_dict

def test_json_storage():
    set_filter_list([KeyValueStorageFilter])
    for doc in run_dexy(JSON_CONFIG):
        doc.run()
        artifact = doc.last_artifact
        print artifact.key
        print artifact.kv_keys()
        assert artifact.kv_keys() == ["1", "2"]
        assert artifact.retrieve_from_kv_storage("1") == "This is the first line."
        assert artifact.retrieve_from_kv_storage("2") == "This is the 2nd line."

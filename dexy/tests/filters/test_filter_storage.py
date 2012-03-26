from dexy.dexy_filter import DexyFilter
from dexy.tests.utils import run_dexy
from dexy.tests.utils import set_filter_list

CONTENTS = "This is the first line.\nThis is the 2nd line."

JSON_CONFIG = {
    "." : {
        "@lines.txt|jsonstorage" : { "contents" : CONTENTS },
        "@lines.txt|kyotostorage" : { "contents" : CONTENTS },
        "@lines.txt|sqlitestorage" : { "contents" : CONTENTS }
    }
}

class JsonStorageFilter(DexyFilter):
    ALIASES = ['jsonstorage']
    OUTPUT_EXTENSIONS = ['.json']

    def process(self):
        self.artifact.setup_kv_storage()
        for i, line in enumerate(self.artifact.input_text().splitlines()):
            self.artifact.append_to_kv_storage(str(i+1), line)
        self.artifact.persist_kv_storage()

class KyotoStorageFilter(JsonStorageFilter):
    ALIASES = ['kyotostorage']
    OUTPUT_EXTENSIONS = ['.kch']

class SqliteStorageFilter(JsonStorageFilter):
    ALIASES = ['sqlitestorage']
    OUTPUT_EXTENSIONS = ['.sqlite3']

def test_json_storage():
    set_filter_list([JsonStorageFilter, KyotoStorageFilter, SqliteStorageFilter])
    for doc in run_dexy(JSON_CONFIG):
        doc.run()
        artifact = doc.last_artifact
        print artifact.kv_keys()
        assert artifact.kv_keys() == ["1", "2"]
        assert artifact.retrieve_from_kv_storage("1") == "This is the first line."
        assert artifact.retrieve_from_kv_storage("2") == "This is the 2nd line."

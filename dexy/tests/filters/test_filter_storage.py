from dexy.dexy_filter import DexyFilter
from dexy.tests.utils import run_dexy
from dexy.tests.utils import set_filter_list

JSON_CONFIG = {
    "." : {
        "@lines.txt|jsonstorage" : { "contents" : "This is the first line.\nThis is hte 2nd line." },
        "@lines.txt|kyotostorage" : { "contents" : "This is the first line.\nThis is hte 2nd line." }
    }
}

class JsonStorageFilter(DexyFilter):
    ALIASES = ['jsonstorage']
    OUTPUT_EXTENSIONS = ['.json']

    def process(self):
        self.artifact.setup_storage()
        for i, line in enumerate(self.artifact.input_text().splitlines()):
            self.artifact.append_to_kv_storage(str(i+1), line)
        self.artifact.persist_storage()

class KyotoStorageFilter(JsonStorageFilter):
    ALIASES = ['kyotostorage']
    OUTPUT_EXTENSIONS = ['.kch']

def test_json_storage():
    set_filter_list([JsonStorageFilter, KyotoStorageFilter])
    for doc in run_dexy(JSON_CONFIG):
        doc.run()
        assert doc.last_artifact.retrieve_from_kv_storage("1") == "This is the first line."
        assert doc.last_artifact.retrieve_from_kv_storage("2") == "This is hte 2nd line."

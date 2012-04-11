from dexy.helpers import DataStorage
from dexy.helpers import KeyValueData
from dexy.helpers import RowData
from dexy.tests.utils import tempdir
import json

def test_init_csv():
    with tempdir():
        storage = RowData("example.csv")
        assert storage.ext == ".csv"
        assert storage.mode == "write"

def test_init_csv_read():
    with tempdir():
        with open("example.csv", "w") as f:
            f.write("some data")
        storage = RowData("example.csv")
        assert storage.ext == ".csv"
        assert storage.mode == "read"

def test_init_json():
    with tempdir():
        storage = KeyValueData("example.json")
        assert storage.ext == ".json"
        assert storage.mode == "write"

def test_init_json_read():
    with tempdir():
        with open("example.json", "w") as f:
            f.write("""{}""")
        storage = RowData("example.json")
        assert storage.ext == ".json"
        assert storage.mode == "read"

def test_init_kyotocabinet():
    with tempdir():
        storage = KeyValueData("example.kch")
        assert storage.ext == ".kch"
        assert storage.mode == "write"

def test_init_kyotocabinet_read():
    with tempdir():
        with open("example.kch", "w") as f:
            f.write("fake data")
        storage = KeyValueData("example.kch")
        assert storage.ext == ".kch"
        assert storage.mode == "read"

def test_init_sqlite_kv():
    with tempdir():
        storage = KeyValueData("example.sqlite3")
        assert storage.ext == ".sqlite3"
        assert storage.mode == "write"

def test_init_sqlite_kv_read():
    with tempdir():
        with open("example.sqlite3", "w") as f:
            f.write("fake data")
        storage = KeyValueData("example.sqlite3")
        assert storage.ext == ".sqlite3"
        assert storage.mode == "read"

def test_init_sqlite_row():
    with tempdir():
        storage = RowData("example.sqlite3")
        assert storage.ext == ".sqlite3"
        assert storage.mode == "write"

def test_init_sqlite_row_read():
    with tempdir():
        with open("example.sqlite3", "w") as f:
            f.write("fake data")
        storage = RowData("example.sqlite3")
        assert storage.ext == ".sqlite3"
        assert storage.mode == "read"

def test_write_read_csv():
    with tempdir():
        storage = RowData("example.csv", ["x", "y"])
        storage.append(1, 1)
        storage.append(2, 4)
        storage.save()

        storage = RowData("example.csv")
        assert storage.read() == "x,y\r\n1,1\r\n2,4\r\n"

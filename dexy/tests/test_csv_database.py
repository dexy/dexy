from dexy.constants import Constants
from dexy.databases.csv_database import CsvDatabase
from dexy.tests.utils import tempdir
import os

def test_persist():
    with tempdir():
        os.mkdir(Constants.DEFAULT_LDIR)
        db = CsvDatabase()
        db.persist()
        assert(os.path.exists(db.filename))

def test_next_batch_id():
    db = CsvDatabase()
    batch_id = db.next_batch_id()
    assert batch_id == 1

    batch_id = db.next_batch_id()
    assert batch_id == 2

def test_next_batch_order():
    db = CsvDatabase()
    batch_id = db.next_batch_id()

    batch_order = db.next_batch_order(batch_id)
    assert batch_order == 1

    batch_order = db.next_batch_order(batch_id)
    assert batch_order == 2


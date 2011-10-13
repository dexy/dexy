from dexy.database import Database
import os

def new_random_filename():
    return "logs/%s.sql" % "abcde"

def new_random_database():
    fn = new_random_filename()
    return (fn, Database(fn))

def test_persist():
    fn, db = new_random_database()
    db.persist()
    assert(os.path.exists(fn))

def test_next_batch_id():
    fn, db = new_random_database()
    batch_id = db.next_batch_id()
    assert batch_id == 1

    batch_id = db.next_batch_id()
    assert batch_id == 2

def test_next_batch_order():
    fn, db = new_random_database()
    batch_id = db.next_batch_id()

    batch_order = db.next_batch_order(batch_id)
    assert batch_order == 1

    batch_order = db.next_batch_order(batch_id)
    assert batch_order == 2


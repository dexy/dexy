from dexy.artifact import Artifact
from dexy.databases.sqlite_database import SqliteDatabase

def test_create_table():
    db = SqliteDatabase(dbfile=None)
    assert len(db.conn.execute("select * from sqlite_master where type='table' and name='artifacts'").fetchall()) == 1
    print db.create_table_sql()

def test_max_batch_id():
    db = SqliteDatabase(dbfile=None)
    assert db.max_batch_id() == 0
    assert db.next_batch_id() == 1
    assert db.max_batch_order(0) == 0
    assert db.next_batch_order(0) == 1

def test_artifact_row():
    a1 = Artifact()
    a1.key = "abc.txt"
    a1.batch_id = 1
    a1.batch_order = 1
    a1.source = 'run'
    a1.elapsed = 5
    a1.hashstring = "abcde123"

    db = SqliteDatabase(dbfile=None)
    db.append_artifact(a1)

    row = db.artifact_row(a1)
    assert row['key'] == a1.key
    assert row['batch_id'] == a1.batch_id

def test_append_and_update_artifacts():
    a1 = Artifact()
    a1.key = "abc.txt"
    a1.batch_id = 1
    a1.batch_order = 1
    a1.source = 'run'
    a1.elapsed = 5
    a1.hashstring = "abcde123"

    a2 = Artifact()
    a2.key = "def.txt"
    a2.hashstring = "abcde456"
    a2.batch_id = 1
    a2.batch_order = 2

    db = SqliteDatabase(dbfile=None)
    db.append_artifacts([a1, a2])

    assert len(db.conn.execute("select * from artifacts").fetchall()) == 2
    assert len(db.conn.execute("select * from artifacts where id = ?", (a1.unique_key(),)).fetchall()) == 1
    assert len(db.conn.execute("select * from artifacts where id = ?", (a2.unique_key(),)).fetchall()) == 1
    assert db.conn.execute("select elapsed from artifacts where id = ?", (a1.unique_key(),)).fetchall()[0][0] == 5

    a1.elapsed = 10

    db.update_artifact(a1)
    assert db.conn.execute("select elapsed from artifacts where id = ?", (a1.unique_key(),)).fetchall()[0][0] == 10

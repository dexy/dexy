from mock import MagicMock
from datetime import datetime
from dexy.tests.utils import temprun

def test_add_task():
    with temprun() as runner:
        attrs = {
                "args" : {},
                "doc.key" : "abc23456",
                "key_with_batch_id.return_value" : "def1234556",
                "runner.batch_id" : 1001,
                "state" : "running",
                "created_by_doc" : None,
                "key" : "file.txt"
                }
        task = MagicMock(**attrs)
        runner.db.add_task_before_running(task)
        runner.db.conn.commit()

        sql = """select * from tasks"""
        runner.db.cursor.execute(sql)
        row = runner.db.cursor.fetchone()

        assert row['batch_id'] == 1001
        assert row['key'] == "file.txt"
        assert row['class_name'] == "MagicMock"
        assert row['started_at'] < datetime.now()
        assert not row['created_by_doc']

        assert runner.db.get_next_batch_id() == 1002

def test_update_task():
    with temprun() as runner:
        attrs = {
                "args" : {},
                "doc.key" : "abc23456",
                "key_with_batch_id.return_value" : "def1234556",
                "runner.batch_id" : 1001,
                "hashstring" : "abc123001",
                "state" : "running",
                "created_by_doc" : None,
                "key" : "file.txt"
                }
        task = MagicMock(**attrs)
        runner.db.add_task_before_running(task)
        runner.db.conn.commit()

        attrs = {
                "state" : "complete"
                }

        runner.db.update_task_after_running(task)

        sql = """select * from tasks"""
        runner.db.cursor.execute(sql)
        row = runner.db.cursor.fetchone()

        assert row['hashstring'] == 'abc123001'

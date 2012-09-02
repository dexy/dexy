from mock import MagicMock
from datetime import datetime
from dexy.tests.utils import temprun

def test_add_task():
    with temprun() as runner:
        attrs = {
                "runner.batch_id" : 1001,
                "metadata.hashstring" : "abc123001",
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
        assert row['hashstring'] == "abc123001"
        assert row['state'] == 'running'
        assert row['started_at'] < datetime.now()
        assert not row['created_by_doc']

        assert runner.db.get_next_batch_id() == 1002

def test_update_task():
    with temprun() as runner:
        attrs = {
                "runner.batch_id" : 1001,
                "metadata.hashstring" : "abc123001",
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
        task.k

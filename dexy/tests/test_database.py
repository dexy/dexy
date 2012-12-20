from mock import MagicMock
from datetime import datetime
from dexy.tests.utils import wrap

def test_add_task():
    with wrap() as wrapper:
        wrapper.setup_db()
        attrs = {
                "args" : {},
                "doc.key" : "abc23456",
                'hashstring' : '12345',
                "key_with_batch_id.return_value" : "def1234556",
                "wrapper.batch.batch_id" : 1001,
                "state" : "running",
                "created_by_doc" : None,
                "key" : "file.txt"
                }
        task = MagicMock(**attrs)
        wrapper.db.add_task_before_running(task)
        wrapper.db.conn.commit()

        sql = """select * from tasks"""
        wrapper.db.cursor.execute(sql)
        row = wrapper.db.cursor.fetchone()

        assert row['batch_id'] == 1001
        assert row['key'] == "file.txt"
        assert row['class_name'] == "MagicMock"
        assert row['started_at'] < datetime.now()
        assert not row['created_by_doc']

        assert wrapper.db.next_batch_id() == 1002

def test_update_task():
    with wrap() as wrapper:
        wrapper.setup_db()
        attrs = {
                "args" : {},
                "doc.key" : "abc23456",
                "key_with_batch_id.return_value" : "def1234556",
                "wrapper.batch.batch_id" : 1001,
                "hashstring" : "abc123001",
                "output_data.name" : "abc23456",
                "created_by_doc" : None,
                "output_data_type" : "generic",
                "ext" : ".txt",
                "output_data.storage_type" : "generic",
                "key" : "file.txt"
                }
        task = MagicMock(**attrs)
        wrapper.db.add_task_before_running(task)
        wrapper.db.conn.commit()

        wrapper.db.update_task_after_running(task)

        sql = """select * from tasks"""
        wrapper.db.cursor.execute(sql)
        row = wrapper.db.cursor.fetchone()

        assert row['hashstring'] == 'abc123001'

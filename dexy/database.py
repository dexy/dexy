from datetime import datetime
from dexy.plugin import PluginMeta
import json

class Database:
    """
    Class that persists run data to a database.
    """
    ALIASES = []
    __metaclass__ = PluginMeta

    @classmethod
    def is_active(klass):
        return True

import sqlite3
class Sqlite3(Database):
    START_BATCH_ID = 1001
    ALIASES = ['sqlite3', 'sqlite']
    FIELDS = [
            ("unique_key", "text"),
            ("batch_id" , "integer"),
            ("key" , "text"),
            ("args" , "text"),
            ("doc_key" , "text"),
            ("class_name" , "text"),
            ("hashstring" , "text"),
            ("created_by_doc" , "text"),
            ("started_at", "timestamp"),
            ("completed_at", "timestamp"),
            ]

    def get_child_hashes_in_previous_batch(self, current_batch_id, parent_hashstring):
        sql = "select max(batch_id) as previous_batch_id from tasks where batch_id < ?"
        self.cursor.execute(sql, (current_batch_id,))
        row = self.cursor.fetchone()
        previous_batch_id = row['previous_batch_id']

        sql = "select * from tasks where batch_id = ? and created_by_doc = ? order by doc_key, started_at"
        self.cursor.execute(sql, (previous_batch_id, parent_hashstring))
        return self.cursor.fetchall()

    def get_next_batch_id(self):
        sql = "select max(batch_id) as max_batch_id from tasks"
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        if row['max_batch_id']:
            return row['max_batch_id'] + 1
        else:
            return self.START_BATCH_ID

    def add_task_before_running(self, task):
        if hasattr(task, 'doc'):
            doc_key = task.doc.key
        else:
            doc_key = task.key

        args_to_serialize = task.args.copy()
        if args_to_serialize.has_key('runner'):
            del args_to_serialize['runner']

        attrs = {
                'args' : json.dumps(args_to_serialize),
                'doc_key' : doc_key,
                'batch_id' : task.runner.batch_id,
                'class_name' : task.__class__.__name__,
                'created_by_doc' : task.created_by_doc,
                'key' : task.key,
                'started_at' : datetime.now(),
                'unique_key' : task.key_with_batch_id()
                }
        self.create_record(attrs)

    def update_task_after_running(self, task):
        if hasattr(task, 'hashstring'):
            hashstring = task.hashstring
        else:
            hashstring = None

        attrs = {
                'completed_at' : datetime.now(),
                'hashstring' : hashstring
                }
        unique_key = task.key_with_batch_id()
        self.update_record(unique_key, attrs)

    def __init__(self, runner):
        self.runner = runner
        self.conn = sqlite3.connect(
                self.runner.params.db_file,
                detect_types=sqlite3.PARSE_DECLTYPES
                )
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_table()

    def save(self):
        self.conn.commit()
        self.conn.close()

    def create_table_sql(self):
        sql = "create table tasks (%s)"
        fields = ["%s %s" % k for k in self.FIELDS]
        return sql % (", ".join(fields))

    def create_table(self):
        try:
            self.conn.execute(self.create_table_sql())
            self.conn.commit()
        except sqlite3.OperationalError as e:
            if e.message != "table tasks already exists":
                raise e

    def create_record(self, attrs):
        keys = sorted(attrs)
        values = [attrs[k] for k in keys]

        qs = ("?," * len(keys))[:-1]
        sql = "insert into tasks (%s) VALUES (%s)" % (",".join(keys), qs)
        self.conn.execute(sql, values)

    def update_record(self, unique_key, attrs):
        keys = sorted(attrs)
        values = [attrs[k] for k in keys]
        updates = ["%s=?" % k for k in keys]

        sql = "update tasks set %s WHERE unique_key=?" % ", ".join(updates)
        values.append(unique_key)

        self.conn.execute(sql, values)

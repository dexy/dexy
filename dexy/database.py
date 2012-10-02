from datetime import datetime
from dexy.plugin import PluginMeta
import dexy.data
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
            ("ext" , "text"),
            ("data_type", "text"),
            ("storage_type", "text"),
            ("created_by_doc" , "text"),
            ("started_at", "timestamp"),
            ("completed_at", "timestamp"),
            ]

    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.conn = sqlite3.connect(
                self.wrapper.db_path(),
                detect_types=sqlite3.PARSE_DECLTYPES
                )
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_table()

    def all_in_batch(self, n=10):
        sql = "select unique_key from tasks where batch_id = ? LIMIT ?"
        values = (self.wrapper.batch_id, n,)
        self.cursor.execute(sql, values)
        rows = self.cursor.fetchall()
        return rows

    def query_like(self, query):
        sql = "select * from tasks where batch_id = ? and key like ?"
        self.cursor.execute(sql, (self.max_batch_id(), "%%%s%%" % query))
        return self.cursor.fetchall()

    def find_data_by_doc_key(self, doc_key):
        sql = "select key, ext, data_type, hashstring, storage_type from tasks where key = ? AND class_name = 'FilterArtifact'"
        self.cursor.execute(sql, (doc_key,))
        row = self.cursor.fetchone()

        print "row for", doc_key, "is", row

        return dexy.data.Data.retrieve(
                row['key'],
                row['ext'],
                row['data_type'],
                row['hashstring'],
                row['storage_type'])

    def find_data_by_websafe_key(self, web_safe_key):
        doc_key = web_safe_key.replace("--", "/")
        return self.find_data_by_doc_key(doc_key)

    def get_child_hashes_in_previous_batch(self, current_batch_id, parent_hashstring):
        sql = "select max(batch_id) as previous_batch_id from tasks where batch_id < ?"
        self.cursor.execute(sql, (current_batch_id,))
        row = self.cursor.fetchone()
        previous_batch_id = row['previous_batch_id']

        sql = "select * from tasks where batch_id = ? and created_by_doc = ? order by doc_key, started_at"
        self.cursor.execute(sql, (previous_batch_id, parent_hashstring))
        return self.cursor.fetchall()

    def max_batch_id(self):
        sql = "select max(batch_id) as max_batch_id from tasks"
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        return row['max_batch_id']

    def next_batch_id(self):
        max_batch_id = self.max_batch_id()
        if max_batch_id:
            return max_batch_id + 1
        else:
            return self.START_BATCH_ID

    def add_task_before_running(self, task):
        if hasattr(task, 'doc'):
            doc_key = task.doc.key
        else:
            doc_key = task.key

        args_to_serialize = task.args.copy()
        if args_to_serialize.has_key('wrapper'):
            del args_to_serialize['wrapper']
        if args_to_serialize.has_key('contents'):
            del args_to_serialize['contents']
            if hasattr(task, 'get_contents_hash'):
                args_to_serialize['contentshash'] = task.get_contents_hash()
                args_to_serialize['data-class-alias'] = task.data_class_alias()

        try:
            serialized_args = json.dumps(args_to_serialize)
        except UnicodeDecodeError:
            msg = "Unable to serialize args. Keys are %s" % args_to_serialize.keys()
            raise dexy.exceptions.InternalDexyProblem(msg)

        attrs = {
                'args' : serialized_args,
                'doc_key' : doc_key,
                'batch_id' : task.wrapper.batch_id,
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

        if hasattr(task, 'ext'):
            ext = task.ext
            data_type = task.output_data_type
            storage_type = task.output_data.storage_type
        else:
            ext = None
            data_type = None
            storage_type = None

        attrs = {
                'completed_at' : datetime.now(),
                'ext' : ext,
                'data_type' : data_type,
                'storage_type' : storage_type,
                'hashstring' : hashstring
                }
        unique_key = task.key_with_batch_id()
        self.update_record(unique_key, attrs)

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

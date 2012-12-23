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
    """
    Implementation of dexy database using sqlite3.
    """
    START_BATCH_ID = 1001
    ALIASES = ['sqlite3', 'sqlite']
    FIELDS = [
            ("unique_key", "text"),
            ("batch_id" , "integer"),
            ("key" , "text"),
            ("args" , "text"),
            ("doc_key" , "text"),
            ("canonical_name", "text"),
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
        self._pending_transaction_counter = 0

    def docs(self, n=10):
        """
        Returns the first n tasks of type Doc in the batch.
        """
        sql = "select unique_key, key from tasks where batch_id = ? and class_name = 'Doc' LIMIT ?"
        values = (self.wrapper.batch_id, n,)
        self.cursor.execute(sql, values)
        rows = self.cursor.fetchall()
        return rows

    def query_docs(self, query):
        sql = "select * from tasks where batch_id = ? and key like ? and class_name='Doc'"
        self.cursor.execute(sql, (self.max_batch_id(), "%%%s%%" % query))
        return self.cursor.fetchall()

    def find_filter_artifact_for_doc_key(self, doc_key):
        sql = "select data_type, key, ext, canonical_name, hashstring, args, storage_type from tasks where key=? and batch_id=? AND class_name like '%Artifact'"
        self.cursor.execute(sql, (doc_key, self.wrapper.batch_id,))
        row = self.cursor.fetchone()

        return dexy.data.Data.retrieve(
                row['data_type'],
                row['key'],
                row['ext'],
                row['canonical_name'],
                row['hashstring'],
                json.loads(row['args']),
                self.wrapper,
                row['storage_type'])

    def find_filter_artifact_for_hashstring(self, hashstring):
        sql = "select data_type, key, ext, canonical_name, hashstring, args, storage_type from tasks where hashstring=? and batch_id=? AND class_name like '%Artifact'"
        self.cursor.execute(sql, (hashstring, self.wrapper.batch_id,))
        row = self.cursor.fetchone()

        return dexy.data.Data.retrieve(
                row['data_type'],
                row['key'],
                row['ext'],
                row['canonical_name'],
                row['hashstring'],
                json.loads(row['args']),
                self.wrapper,
                row['storage_type'])

    def find_data_by_websafe_key(self, web_safe_key):
        doc_key = web_safe_key.replace("--", "/")
        return self.find_data_by_doc_key(doc_key)

    def calculate_previous_batch_id(self, current_batch_id):
        sql = "select max(batch_id) as previous_batch_id from tasks where batch_id < ?"
        self.cursor.execute(sql, (current_batch_id,))
        row = self.cursor.fetchone()
        return row['previous_batch_id']

    def get_child_hashes_in_previous_batch(self, parent_hashstring):
        sql = "select * from tasks where batch_id = ? and created_by_doc = ? order by doc_key, started_at"
        self.cursor.execute(sql, (self.wrapper.batch.previous_batch_id, parent_hashstring))
        return self.cursor.fetchall()

    def task_from_previous_batch(self, hashstring):
        sql = "select * from tasks where class_name = 'FilterArtifact' and batch_id = ? and hashstring = ?"
        self.cursor.execute(sql, (self.wrapper.batch.previous_batch_id, hashstring))
        return self.cursor.fetchall()

    def task_from_current_batch(self, hashstring):
        sql = "select * from tasks where class_name = 'FilterArtifact' and batch_id = ? and hashstring = ?"
        self.cursor.execute(sql, (self.wrapper.batch.batch_id, hashstring))
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

    def serialize_task_args(self, task):
        args_to_serialize = task.args.copy()
        if args_to_serialize.has_key('wrapper'):
            del args_to_serialize['wrapper']
        if args_to_serialize.has_key('inputs'):
            del args_to_serialize['inputs']
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

        return serialized_args

    def add_task_before_running(self, task):
        if hasattr(task, 'doc'):
            doc_key = task.doc.key
        else:
            doc_key = task.key

        attrs = {
                'doc_key' : doc_key,
                'batch_id' : task.wrapper.batch.batch_id,
                'class_name' : task.__class__.__name__,
                'created_by_doc' : task.created_by_doc,
                'hashstring' : task.hashstring,
                'key' : task.key,
                'started_at' : datetime.now(),
                'unique_key' : task.key_with_batch_id()
                }
        self.create_record(attrs)

    def update_task_after_running(self, task):
        if hasattr(task, 'ext'):
            ext = task.ext
            data_type = task.output_data_type
            storage_type = task.output_data.storage_type
            name = task.output_data.name
        else:
            ext = None
            data_type = None
            storage_type = None
            name = None

        attrs = {
                'args' : self.serialize_task_args(task),
                'canonical_name' : name,
                'completed_at' : datetime.now(),
                'ext' : ext,
                'data_type' : data_type,
                'storage_type' : storage_type
                }
        unique_key = task.key_with_batch_id()
        self.update_record(unique_key, attrs)

    def commit(self):
        self.wrapper.log.debug("committing db changes")
        self.conn.commit()

    def save(self):
        self.commit()
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

        # make sure we don't go too long before committing changes to sqlite
        self._pending_transaction_counter += 1
        if self._pending_transaction_counter > 200:
            self.commit()
            self._pending_transaction_counter = 0

    def fetch_record(self, unique_key):
        sql = "select * from tasks where unique_key=?"
        self.cursor.execute(sql, (unique_key,))
        rows = self.cursor.fetchall()
        return rows

from dexy.plugin import Metadata
from ordereddict import OrderedDict
import hashlib
import sqlite3

class Sqlite3(Metadata):
    """
    Class that stores metadata for a task.
    """

    FIELDS = [
            ("hashstring" , "text"),
            ("parent_hash" , "text"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("mtime", "int"),
            ("ctime", "int"),
            ("inode", "int")
            ]

    def __init__(self, run_params):
        for k in [tup[0] for tup in self.FIELDS]:
            setattr(self, k, None)

        if not hasattr(self, 'conn') or not self.conn:
            self.setup_db_conn(run_params.db_file)

    @classmethod
    def setup_db_conn(klass, db_file):
        klass.db_file = db_file
        klass.conn = sqlite3.connect(klass.db_file)
        klass.conn.row_factory = sqlite3.Row

        klass.field_keys = [k[0] for k in klass.FIELDS]
        klass.whitelist_keys = ['key']
        klass.field_names = ['id'] + klass.field_keys + klass.whitelist_keys
        klass.db_attributes = [k for k in klass.field_names if not k in ["created_at", "id"]]

        klass.create_table()
        klass.conn.commit()

    @classmethod
    def create_table_sql(klass):
        sql = "create table artifacts (id integer primary key, %s)"
        fields = ["%s %s" % k for k in klass.FIELDS]
        fields.extend("%s text" % k for k in klass.whitelist_keys)
        return sql % (", ".join(fields))

    @classmethod
    def create_table(klass):
        try:
            klass.conn.execute(klass.create_table_sql())
        except sqlite3.OperationalError as e:
            if e.message != "table artifacts already exists":
                raise e

    def previous_record_for_key(self):
        sql = "select * from artifacts where key = ? order by id DESC LIMIT 1"
        return self.conn.execute(sql, (self.key,)).fetchone()

    def create_record(self):
        qs = ("?," * len(self.db_attributes))[:-1]
        sql = "insert into artifacts (%s) VALUES (%s)" % (",".join(self.db_attributes), qs)
        attrs = self.get_attributes()
        self.conn.execute(sql, attrs)

    def get_attributes(self):
        return [getattr(self, k) for k in self.db_attributes]

    def persist(self):
        self.conn.commit()

    ### @export "compute-hash"
    def compute_hash(self):
        ordered = OrderedDict()
        for k in sorted(self.__dict__):
            if not k in ('hashstring', 'created_at'):
                ordered[k] = str(self.__dict__[k])

        text = str(ordered)
        return hashlib.md5(text).hexdigest()

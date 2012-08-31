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

    def __init__(self, runner):
        self.runner = runner
        if not hasattr(self.__class__, 'field_keys'):
            self.__class__.field_keys = [k[0] for k in self.__class__.FIELDS]
            self.__class__.whitelist_keys = ['key']
            self.__class__.field_names = ['id'] + self.__class__.field_keys + self.__class__.whitelist_keys
            self.__class__.db_attributes = [k for k in self.__class__.field_names if not k in ["created_at", "id"]]

        for k in [tup[0] for tup in self.FIELDS]:
            setattr(self, k, None)

        self.create_table()

    @classmethod
    def create_table_sql(klass):
        sql = "create table artifacts (id integer primary key, %s)"
        fields = ["%s %s" % k for k in klass.FIELDS]
        fields.extend("%s text" % k for k in klass.whitelist_keys)
        return sql % (", ".join(fields))

    def create_table(self):
        try:
            self.runner.conn.execute(self.create_table_sql())
            self.runner.conn.commit()
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
        self.runner.conn.execute(sql, attrs)

    def get_attributes(self):
        return [getattr(self, k) for k in self.db_attributes]

    ### @export "compute-hash"
    def compute_hash(self):
        ordered = OrderedDict()
        for k in sorted(self.__dict__):
            if not k in ('runner', 'hashstring', 'created_at'):
                ordered[k] = str(self.__dict__[k])

        self.runner.log.debug("==================== Calculating hash for %s" % self.key)
        for k, v in ordered.iteritems():
            str_v = str(v).split("\n")[0][0:150]
            self.runner.log.debug("%s: %s" % (k, str_v))

        text = str(ordered)
        return hashlib.md5(text).hexdigest()

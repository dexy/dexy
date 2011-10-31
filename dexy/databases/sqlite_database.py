from dexy.constants import Constants
from ordereddict import OrderedDict
import sqlite3
import dexy.database
import json
import os

class SqliteDatabase(dexy.database.Database):
    """
    The Database class stores metadata around dexy batches/runs. This metadata
    is used for reporting and can be used as a version history of the documents
    you process with dexy.
    The database can also be used to parallelize/distribute the processing of
    dexy runs and to store ctime/mtime/inode data to speed up cache detection.
    """

    FIELDS = [
            ("batch_id" , "int"),
            ("batch_order" , "int"),
            ("elapsed" , "int"),
            ("hashstring" , "text"),
            ("source" , "text")
            ]

    def create_table_sql(self):
        sql = "create table artifacts (id text primary key, %s)"
        fields = ["%s %s" % k for k in self.FIELDS]
        fields.extend("%s text" % k for k in self.whitelist_keys)
        return sql % (", ".join(fields))

    def create_table(self):
        try:
            self.conn.execute(self.create_table_sql())
        except sqlite3.OperationalError:
            pass

    def __init__(self, logsdir=Constants.DEFAULT_LDIR, dbfile=Constants.DEFAULT_DBFILE):
        self.logsdir = logsdir or ""
        if dbfile:
            filename = os.path.join(self.logsdir, dbfile)
            self.filename = filename
            # TODO test that schema hasn't changed
        else:
            # use in-memory db
            self.filename = ":memory:"

        self.conn = sqlite3.connect(self.filename)
        self.conn.row_factory = sqlite3.Row

        self.field_keys = [k[0] for k in self.FIELDS]
        self.whitelist_keys = sorted(Constants.ARTIFACT_HASH_WHITELIST)
        self.field_names = ['id'] + self.field_keys + self.whitelist_keys
        self.create_table()
        self.batch_orders = {}

    def persist(self):
        self.conn.commit()

    def max_batch_id(self):
        return self.conn.execute("select max(batch_id) from artifacts").fetchone()[0] or 0

    def next_batch_id(self):
        return self.max_batch_id() + 1

    def max_batch_order(self, batch_id, incr=False):
        # using a hash for calculating batch order since hitting the DB each
        # time is too slow. should be getting this from topo sort? should be
        # per-artifact rather than per-document? This isn't used for anything
        # currently, so not a big deal.
        if not self.batch_orders.has_key(batch_id):
            self.batch_orders[batch_id] = 0
        elif incr:
            self.batch_orders[batch_id] += 1
        return self.batch_orders[batch_id]

    def next_batch_order(self, batch_id):
        return self.max_batch_order(batch_id, True)

    def get_attributes_for_artifact(self, artifact):
        hd = artifact.hash_dict()
        values = [artifact.unique_key()]

        # add attrs not in hash whitelist
        values.extend(getattr(artifact, k) for k in self.field_keys)

        # get attrs from the hash whitelist, converting any OrderedDicts into JSON
        artifact_values = (hd.get(k, None) for k in self.whitelist_keys)
        convert_to_json = lambda v: isinstance(v, OrderedDict) and json.dumps(v) or v
        values.extend(convert_to_json(v) for v in artifact_values)

        return values

    def append_artifacts(self, artifacts):
        qs = ("?," * len(self.field_names))[:-1]
        sql = "INSERT INTO artifacts VALUES (%s)" % qs
        for a in artifacts:
            self.conn.execute(sql, self.get_attributes_for_artifact(a))

    def update_artifact(self, artifact):
        values = self.get_attributes_for_artifact(artifact)[1:]
        values.append(artifact.unique_key())
        sql = "UPDATE artifacts SET %s where id = ?" % (", ".join("%s = ? " % k for k in self.field_names[1:]))
        self.conn.execute(sql, values)

    def artifact_row(self, artifact):
        """Returns the db row corresponding to an artifact."""
        sql = "SELECT * from artifacts where id = ?"
        return self.conn.execute(sql, (artifact.unique_key(),)).fetchone()

    def references_for_batch_id(self, batch_id=None):
        """
        Return information for a given batch.
        """
        if not batch_id:
            # use most recent batch
            batch_id = self.max_batch_id()
        sql = "SELECT * from artifacts where batch_id = ?"
        return self.conn.execute(sql, (batch_id,)).fetchall()

    def all(self):
        return self.conn.execute("SELECT * from artifacts").fetchall()

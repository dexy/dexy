try:
    import web
    import sqlite3
#    DB_AVAILABLE = True
    DB_AVAILABLE = False # Disable this for now.
    web.config.debug = False
except ImportError:
    DB_AVAILABLE = False

class Db(object):
    DATABASE_FILE = 'testdb'
    DATABASE_TYPE = 'sqlite'

    def __init__(self):
        self.conn = web.database(dbn=self.DATABASE_TYPE, db=self.DATABASE_FILE)

        try:
            self.conn.query("""CREATE TABLE tasks (
                artifact_hashstring text,
                document_key text,
                batch_id integer,
                batch_order integer,
                host text,
                pid integer,
                exit_status integer,
                complete boolean default 'f'
            );""")
        except sqlite3.OperationalError:
            # In this case, the db already exists.
            pass

    def next_batch_id(self):
        # TODO Replace with UUID?
        old_batch_id = self.conn.select("tasks", what="max(batch_id)")[0]["max(batch_id)"]
        if not old_batch_id:
            old_batch_id = 0
        return old_batch_id + 1

    def next_batch_order(self, batch_id):
        old_batch_order = self.conn.select("tasks", what="max(batch_order)", where="batch_id=%s" % batch_id)[0]["max(batch_order)"]
        if not old_batch_order:
            old_batch_order = 0 # Need to start at 0, not -1, since 0 evals to false.
        return old_batch_order + 1

    def insert_artifact(self, artifact, batch_id):
        self.conn.insert("tasks",
            batch_id=batch_id,
            batch_order=self.next_batch_order(batch_id),
            document_key=artifact.name,
            artifact_hashstring = artifact.hashstring
        )

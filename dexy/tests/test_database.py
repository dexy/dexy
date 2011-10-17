from dexy.database import Database
import dexy.introspect
import os

INIT_ARGS = {
        "CsvDatabase" : { "logsdir" : "logs", "dbfile" : "db.csv" }
}

def test_db_api():
    database_classes = dexy.introspect.database_classes()
    for klass_name, klass in database_classes.iteritems():
        print "testing", klass_name
        args = INIT_ARGS[klass_name]
        print "initializing db with", args
        db = klass(**args)
        for req in ['persist', 'next_batch_id', 'next_batch_order', 'append', 'references_for_batch_id']:
            assert hasattr(db, req), "db class %s must implement a %s method" % (klass_name, req)


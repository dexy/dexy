import dexy.introspect

INIT_ARGS = {
        "SqliteDatabase" : { "logsdir" : None, "dbfile" : None }
}

REQUIRED_METHODS = [
    'persist',
    'max_batch_id',
    'next_batch_id',
    'next_batch_order',
    'append_artifacts',
    'update_artifact',
    'references_for_batch_id'
]

def test_db_api():
    database_classes = dexy.introspect.database_classes()
    for klass_name, klass in database_classes.iteritems():
        print "testing", klass_name
        args = INIT_ARGS[klass_name]
        print "initializing db with", args
        db = klass(**args)
        for req in REQUIRED_METHODS:
            assert hasattr(db, req), "db class %s must implement a %s method" % (klass_name, req)


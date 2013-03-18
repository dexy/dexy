from dexy.commands.utils import init_wrapper
from dexy.utils import defaults

def grep_command(
        __cli_options=False, # nodoc
        expr=None, # The expression to search for
        keyexpr="", # Only search for keys matching this expression, implies keys=True
        keys=False, # if True, try to list the keys in any found files
        recurse=False, # if True, recurse into keys to look for sub keys (implies keys=True)
        artifactsdir=defaults['artifacts_dir'], # location of directory in which to store artifacts
        logdir=defaults['log_dir'] # location of directory in which to store logs
        ):
    """
    Search for a Dexy document in the database matching the expression.

    For sqlite the expression will be wrapped in % for you.
    """
    wrapper = init_wrapper(locals())

#    for row in wrapper.db.query_docs("%%%s%%" % expr):
#        print row['key']
#        if keys or len(keyexpr) > 0 or recurse:
#            artifact_classes = dexy.introspect.artifact_classes()
#            artifact_class = artifact_classes[artifactclass]
#            artifact = artifact_class.retrieve(row['hashstring'])
#            if artifact.ext in [".json", ".kch", ".sqlite3"]:
#                if len(keyexpr) > 0:
#                    rows = artifact.kv_storage().query("%%%s%%" % keyexpr)
#                else:
#                    rows = artifact.kv_storage().keys()
#
#                if rows:
#                    print "  key-value store keys:"
#                for k in rows:
#                    print "    %s" % k
#                    if recurse:
#                        v = artifact.retrieve_from_kv_storage(k)
#                        try:
#                            if not hasattr(v, "keys"):
#                                v = json.loads(v)
#                            if hasattr(v, "keys"):
#                                for kk in v.keys():
#                                    print "      %s" % kk
#                        except Exception as e:
#                            pass
#
#            if len(artifact.data_dict.keys()) > 1:
#                print "  data dict keys:"
#            for k in artifact.data_dict.keys():
#                if not k == '1':
#                    print "    %s" % k

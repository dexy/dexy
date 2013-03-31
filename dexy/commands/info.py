from dexy.commands.utils import init_wrapper
from dexy.utils import defaults
from dexy.batch import Batch

INFO_ATTRS = [
        'name',
        'ext',
        'key',
        'storage_type'
        ]
INFO_METHODS = [
        'title',
        'basename',
        'filesize',
        'baserootname',
        'parent_dir',
        'long_name',
        'web_safe_document_key'
        ]
STORAGE_METHODS = [
        'data_file',
        'data_file_exists'
        ]
def info_command(
        __cli_options=False,
        expr=None, # The doc key to query. Use dexy grep to search doc keys.
        artifactsdir=defaults['artifacts_dir'], # location of directory in which to store artifacts
        logdir=defaults['log_dir'] # location of directory in which to store logs
        ):
    wrapper = init_wrapper(locals())
    batch = Batch.load_most_recent(wrapper)

    matches = [data for data in batch if expr in data.key]

    print "search expr:", expr

    for match in matches:
        print
        print "  doc key:", match.key

        print "    data attributes:"
        for fname in sorted(INFO_ATTRS):
            print "      %s: %s" % (fname, getattr(match, fname))
        print
    
        print "    data methods:"
        for fname in sorted(INFO_METHODS):
            print "      %s(): %s" % (fname, getattr(match, fname)())
        print
    
        print "    storage methods:"
        for fname in sorted(STORAGE_METHODS):
            print "      %s(): %s" % (fname, getattr(match.storage, fname)())
        print

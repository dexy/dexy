from dexy.batch import Batch
from dexy.commands.utils import init_wrapper
from dexy.utils import defaults
from operator import attrgetter
import dexy.exceptions

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
        expr="", # The doc key to query. Use dexy grep to search doc keys.
        key="", # The doc key to match exactly. Use dexy grep to search doc keys.
        artifactsdir=defaults['artifacts_dir'], # location of directory in which to store artifacts
        logdir=defaults['log_dir'] # location of directory in which to store logs
        ):
    wrapper = init_wrapper(locals())
    batch = Batch.load_most_recent(wrapper)

    if expr:
        matches = sorted([data for data in batch if expr in data.key], key=attrgetter('key'))
        print "search expr:", expr
    elif key:
        matches = sorted([data for data in batch if key == data.key], key=attrgetter('key'))
    else:
        raise dexy.exceptions.UserFeedback("Must specify either expr or key")


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

from dexy.batch import Batch
from dexy.commands.utils import init_wrapper
from dexy.utils import defaults
from operator import attrgetter
import dexy.exceptions

### "info-keys"
info_attrs = [
        'name',
        'ext',
        'key'
        ]

info_methods = [
        'title',
        'basename',
        'filesize',
        'baserootname',
        'parent_dir',
        'long_name',
        'web_safe_document_key'
        ]

storage_methods = []
### @end

def info_command(
        __cli_options=False,
        expr="", # The doc key to query. Use dexy grep to search doc keys.
        key="", # The doc key to match exactly. Use dexy grep to search doc keys.
        artifactsdir=defaults['artifacts_dir'], # Where dexy stores working files.
        logdir=defaults['log_dir'] # DEPRECATED
        ):
    wrapper = init_wrapper(locals())
    batch = Batch.load_most_recent(wrapper)

    if expr:
        print "search expr:", expr
        matches = sorted([data for data in batch if expr in data.key],
                key=attrgetter('key'))
    elif key:
        matches = sorted([data for data in batch if key == data.key],
                key=attrgetter('key'))
    else:
        raise dexy.exceptions.UserFeedback("Must specify either expr or key")

    for match in matches:
        print ''
        print "  doc key:", match.key

        print "    data attributes:"
        for fname in sorted(info_attrs):
            print "      %s: %s" % (fname, getattr(match, fname))
        print ''
    
        print "    data methods:"
        for fname in sorted(info_methods):
            print "      %s(): %s" % (fname, getattr(match, fname)())
        print ''

        if storage_methods:
            print "    storage methods:"
            for fname in sorted(storage_methods):
                print "      %s(): %s" % (fname, getattr(match.storage, fname)())
            print ''

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

### "info-com"
def info_command(
        __cli_options=False,
        expr="", # An expression partially matching document name.
        key="", # The exact document key.
        **kwargs
        ):
    """
    Prints metadata about a dexy document.

    Dexy must have already run successfully.

    You can specify an exact document key or an expression which matches part
    of a document name/key. The `dexy grep` command is available to help you
    search for documents and print document contents.
    """
    artifactsdir = kwargs.get('artifactsdir', defaults['artifacts_dir'])
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
        print "  data type:", match.alias
        print ''

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

        print "    For more information about methods available on this data type"
        print "    run `dexy datas -alias %s`" % match.alias

from dexy.commands.utils import init_wrapper
from dexy.utils import defaults

INFO_ATTRS = [
        'name',
        'ext',
        'key',
        'hashstring',
        'storage_type'
        ]
INFO_METHODS = [
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
        k=None, # The doc key to query. Use dexy grep to search doc keys.
        artifactsdir=defaults['artifacts_dir'], # location of directory in which to store artifacts
        logdir=defaults['log_dir'] # location of directory in which to store logs
        ):
    wrapper = init_wrapper(locals())
    wrapper.setup_read()
    data = wrapper.db.find_data_by_doc_key(k)

    print k

    print "  attributes:"
    for fname in sorted(INFO_ATTRS):
        print "    %s: %s" % (fname, getattr(data, fname))

    print "  methods:"
    for fname in sorted(INFO_METHODS):
        print "    %s: %s" % (fname, getattr(data, fname)())

    print "  storage methods:"
    for fname in sorted(STORAGE_METHODS):
        print "    %s: %s" % (fname, getattr(data.storage, fname)())

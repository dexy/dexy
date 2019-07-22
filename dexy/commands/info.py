from dexy.batch import Batch
from dexy.commands.utils import init_wrapper
from dexy.commands.utils import print_indented
from dexy.commands.utils import print_rewrapped
from dexy.utils import defaults
from operator import attrgetter
import dexy.exceptions
import sys

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

def links_command(
        **kwargs
        ):
    """
    Print list of links and sections found in dexy documents.
    """
    artifactsdir = kwargs.get('artifactsdir', defaults['artifacts_dir'])
    wrapper = init_wrapper(locals())
    batch = Batch.load_most_recent(wrapper)

    if not batch:
        print("you need to run dexy first")
        sys.exit(1)

    wrapper.setup_log()
    wrapper.batch = batch

    wrapper.add_lookups()

    if wrapper.lookup_nodes:
        print_indented("Nodes:")
    for label in sorted(wrapper.lookup_nodes):
        nodes = wrapper.lookup_nodes[label]
        if len(nodes) > 1:
            print('')
            print_indented("'%s'" % label, 2)
            print_indented("Multiple nodes match %s:" % label, 4)
            for node in nodes:
                print_indented(">> %r" % node, 6)
        elif len(nodes) == 0:
            print_indented("'%s'" % label, 2)
            print_indented("NO nodes match %s" % label, 4)
        else:
            node = nodes[0]
            print_indented("'%s'" % label, 2)
            print_indented("%r" % node, 4)
        print('')

    print('')

    if wrapper.lookup_sections:
        print_indented("Sections:")
    for label in sorted(wrapper.lookup_sections):
        node = wrapper.lookup_sections[label][0]
        print_indented("'%s'" % label, 2)
        print_indented("%r" % node, 4)
        print('')

### "info-com"
def info_command(
        __cli_options=False,
        expr="", # An expression partially matching document name.
        key="", # The exact document key.
        ws=False, # Whether to print website reporter keys and values.
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
    wrapper.setup_log()
    batch = Batch.load_most_recent(wrapper)
    wrapper.batch = batch

    if expr:
        print("search expr:", expr)
        matches = sorted([data for data in batch if expr in data.key],
                key=attrgetter('key'))
    elif key:
        matches = sorted([data for data in batch if key == data.key],
                key=attrgetter('key'))
    else:
        raise dexy.exceptions.UserFeedback("Must specify either expr or key")

    for match in matches:
        print("")
        print("  Info for Document '%s'" % match.key)
        print("")
        print("  document output data type:", match.alias)
        print("")

        print_indented("settings:", 2)
        for k in sorted(match._instance_settings):
            if not k in ('aliases', 'help'):
                print_indented("%s: %s" % (k, match.setting(k)), 4)

        print("")
        print_indented("attributes:", 2)
        for fname in sorted(info_attrs):
            print_indented("%s: %s" % (fname, getattr(match, fname)), 4)
        print("")
    
        print_indented("methods:", 2)
        for fname in sorted(info_methods):
            print_indented("%s(): %s" % (fname, getattr(match, fname)()), 4)
        print("")

        if storage_methods:
            print_indented("storage methods:", 2)
            for fname in sorted(storage_methods):
                print_indented("%s(): %s" % (fname, getattr(match.storage, fname)), 4)
            print('')

        if ws:
            print_indented("website reporter methods:", 2)
            print('')
            reporter = dexy.reporter.Reporter.create_instance('ws')
            reporter.wrapper = wrapper
            reporter.setup_navobj()
            reporter.help(match)
            print('')
            print_indented("active template plugins are:", 2)
            print_indented(", ".join(reporter.setting('plugins')), 4)
            print('')


        else:
            print_indented("For website reporter tags, run this command with -ws option", 4)
            print('')


        print_rewrapped("""For more information about methods available on this
        data type run `dexy datas -alias %s`""" % match.alias)

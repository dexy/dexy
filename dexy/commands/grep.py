from dexy.batch import Batch
from dexy.commands.utils import init_wrapper
from dexy.data import Generic
from dexy.data import KeyValue
from dexy.data import Sectioned
from dexy.utils import defaults
from operator import attrgetter
import dexy.exceptions
import json
import sys

def grep_command(
        __cli_options=False, # nodoc
        contents=False, # print out the contents of each matched file
        expr="", # An expression partially matching document name.
        key="", # An exact document key
        keyexpr="", # Only search for keys matching this expression
        keylimit=10, # Maximum number of matching keys to print
        keys=False, # List keys in documents
        limit=10, # Maximum number of matching documents to print
        lines=False, # maximum number of lines of content to print
        **kwargs
        ):
    """
    Search for documents and sections within documents.

    Dexy must have already run successfully.

    You can search for documents based on exact key or inexpect expression. The
    number of documents returned is controlled by --limit.

    You can print all keys in found documents by requesting --keys, number of
    results is controlled by --keylimit.

    You can search the section names/keys in found documents by passing a
    --keyexpr

    You can print contents of documents by requesting --contents, number of
    lines of content can be controlled by --lines.

    This does not search contents of documents, just document names and
    internal section names.
    """

    artifactsdir = kwargs.get('artifactsdir', defaults['artifacts_dir'])
    wrapper = init_wrapper(locals())
    batch = Batch.load_most_recent(wrapper)
   
    if not batch:
        print("you need to run dexy first")
        sys.exit(1)
    else:
        if expr:
            matches = sorted([data for data in batch if expr in data.key],
                    key=attrgetter('key'))
        elif key:
            matches = sorted([data for data in batch if key == data.key],
                    key=attrgetter('key'))
        else:
            raise dexy.exceptions.UserFeedback("Must specify either expr or key")

        n = len(matches)
        if n > limit:
            print("only printing first %s of %s total matches" % (limit, n))
            matches = matches[0:limit]

        for match in matches:
            print_match(match, keys, keyexpr, contents, keylimit, lines)

def print_match(match, keys, keyexpr, contents, keylimit, lines):
    print(match.key, "\tcache key:", match.storage_key)

    if hasattr(match, 'keys'):
        if keyexpr:
            print_keys([key for key in list(match.keys()) if keyexpr in key], keylimit, lines)
        elif keys:
            print_keys(list(match.keys()), keylimit, lines)

    if contents:
        if isinstance(match, Sectioned):
            for section_name, section_contents in match.data().items():
                print("  section: %s" % section_name)
                print()
                print_contents(section_contents, lines)
                print()
        elif isinstance(match, KeyValue):
            pass
        elif isinstance(match, Generic):
            try:
                json.dumps(str(match))
                print_contents(str(match), lines)
            except UnicodeDecodeError:
                print("  not printable")

def print_keys(pkeys, keylimit, lines):
    n = len(pkeys)
    if n > keylimit:
        pkeys = pkeys[0:keylimit]
    
    for key in pkeys:
        print('  ', key)

    if n > keylimit:
        print("  only printed first %s of %s total keys" % (keylimit, n))

def print_contents(text, lines):
    text_lines = text.splitlines()
    for i, line in enumerate(text_lines):
        if lines and i > lines-1:
            continue
        print("  ", line)

    if lines and lines < len(text_lines):
        print("   only printed first %s of %s total lines" % (lines, len(text_lines)))

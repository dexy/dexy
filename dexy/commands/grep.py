from dexy.batch import Batch
from dexy.commands.utils import init_wrapper
from dexy.data import Generic
from dexy.data import KeyValue
from dexy.data import Sectioned
from dexy.utils import defaults
from operator import attrgetter
import dexy.exceptions
import json

def grep_command(
        __cli_options=False, # nodoc
        expr="", # The expression to search for
        key="", # The exact document key to search for
        keyexpr="", # Only search for keys matching this expression, implies keys=True
        keys=False, # if True, try to list the keys in any found files
        keylimit=10, # maximum number of matching keys to print
        limit=10, # maximum number of matching records to print
        contents=False, # print out the contents of each matched file
        lines=False, # maximum number of lines of content to print
        artifactsdir=defaults['artifacts_dir'], # location of directory in which to store artifacts
        logdir=defaults['log_dir'] # location of directory in which to store logs
        ):
    """
    Search for a Dexy document in the previously run batch. Prints out document
    keys which include the expression.
    """
    wrapper = init_wrapper(locals())
    batch = Batch.load_most_recent(wrapper)

    def print_keys(pkeys):
        n = len(pkeys)
        if n > keylimit:
            pkeys = pkeys[0:keylimit]
        
        for key in pkeys:
            print '  ', key

        if n > keylimit:
            print "  only printed first %s of %s total keys" % (keylimit, n)

    def print_contents(text):
        text_lines = text.splitlines()
        for i, line in enumerate(text_lines):
            if lines and i > lines-1:
                continue
            print "  ", line

        if lines and lines < len(text_lines):
            print "   only printed first %s of %s total lines" % (lines, len(text_lines))

    def print_match(match):
        print match.key, "\tcache key:", match.storage_key

        if hasattr(match, 'keys'):
            if keyexpr:
                print_keys([key for key in match.keys() if keyexpr in key])
            elif keys:
                print_keys(match.keys())

        if contents:
            if isinstance(match, Sectioned):
                for section_name, section_contents in match.data().iteritems():
                    print "  section: %s" % section_name
                    print
                    print_contents(section_contents)
                    print
            elif isinstance(match, KeyValue):
                pass
            elif isinstance(match, Generic):
                try:
                    json.dumps(unicode(match))
                    print_contents(unicode(match))
                except UnicodeDecodeError:
                    print "  not printable"

    def print_matches(matches):
        for match in matches:
            print_match(match)
   
    if not batch:
        print "you need to run dexy first"
    else:
        if expr:
            matches = sorted([data for data in batch if expr in data.key], key=attrgetter('key'))
        elif key:
            matches = sorted([data for data in batch if key == data.key], key=attrgetter('key'))
        else:
            raise dexy.exceptions.UserFeedback("Must specify either expr or key")

        n = len(matches)
        if n > limit:
            print_matches(matches[0:limit])
            print "only printed first %s of %s total matches" % (limit, n)
        else:
            print_matches(matches)

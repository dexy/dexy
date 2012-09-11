from StringIO import StringIO
from dexy.artifact import FilterArtifact
from dexy.common import OrderedDict
from dexy.exceptions import InactiveFilter
from dexy.params import RunParams
from dexy.runner import Runner
from dexy.utils import char_diff
from modargs import args as modargs
from nose.exc import SkipTest
import dexy.commands
import dexy.data
import dexy.metadata
import os
import random
import shutil
import sys
import tempfile

def create_ordered_dict_from_dict(d):
    od = OrderedDict()
    for k, v in d.iteritems():
        od[k] = v
    return od

class tempdir():
    def __enter__(self):
        self.tempdir = tempfile.mkdtemp()
        self.location = os.path.abspath(os.curdir)
        os.chdir(self.tempdir)

    def __exit__(self, type, value, traceback):
        os.chdir(self.location)
        shutil.rmtree(self.tempdir)

class temprun(tempdir):
    """
    Create a temporary directory and initialize a runner.
    """
    def __enter__(self):
        self.tempdir = tempfile.mkdtemp()
        self.location = os.path.abspath(os.curdir)
        os.chdir(self.tempdir)
        runner = Runner()
        runner.setup_dexy_dirs()
        runner.setup_log()
        runner.setup_db()
        return runner

class runfilter(tempdir):
    """
    Create a temporary directory, initialize a doc and a runner, run the doc.

    Raises SkipTest on inactive filters.
    """
    def __init__(self, filter_alias, doc_contents, ext=".txt"):
        self.filter_alias = filter_alias
        self.doc_contents = doc_contents
        self.ext = ext

    def __enter__(self):
        # Create a temporary working dir and move to it
        self.tempdir = tempfile.mkdtemp()
        self.location = os.path.abspath(os.curdir)
        os.chdir(self.tempdir)

        # Create a document. Skip testing documents with inactive filters.
        try:
            params = RunParams()
            doc_key = "example%s|%s" % (self.ext, self.filter_alias)
            doc_spec = [[doc_key, {"contents" : self.doc_contents}]]
            runner = Runner(params, doc_spec)
            runner.run()
        except InactiveFilter:
            print "Skipping tests for inactive filter", self.filter_alias
            raise SkipTest

        return runner.docs[0]

def assert_output(filter_alias, doc_contents, expected_output, ext=".txt"):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_in_output must start with dot")

    if isinstance(expected_output, dict):
        expected_output = create_ordered_dict_from_dict(expected_output)

    with runfilter(filter_alias, doc_contents, ext=ext) as doc:
        try:
            assert doc.output().data() == expected_output
        except AssertionError as e:
            print char_diff(doc.output().data_or_dict(), expected_output)
            raise e

def assert_in_output(filter_alias, doc_contents, expected_output, ext=".txt"):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_in_output must start with dot")

    with runfilter(filter_alias, doc_contents, ext=ext) as doc:
        assert expected_output in doc.output().data()

def assert_not_in_output(filter_alias, doc_contents, expected_output):
    with runfilter(filter_alias, doc_contents) as doc:
        assert not expected_output in doc.output().data()

class divert_stdout():
    def __enter__(self):
        self.old_stdout = sys.stdout
        self.my_stdout = StringIO()
        sys.stdout = self.my_stdout
        return self.my_stdout

    def __exit__(self, type, value, traceback):
        sys.stdout = self.old_stdout
        self.my_stdout.close()

class divert_stderr():
    def __enter__(self):
        self.old_stderr = sys.stderr
        self.my_stderr = StringIO()
        sys.stderr = self.my_stderr
        return self.my_stderr

    def __exit__(self, type, value, traceback):
        sys.stderr = self.old_stderr
        self.my_stderr.close()

def controller_args(additional_args = {}):
    fn = modargs.function_for(dexy.commands, "dexy")
    args = modargs.determine_kwargs(fn)
    args.update(additional_args)

    if not os.path.exists(args['logsdir']):
        os.mkdir(args['logsdir'])
    if not os.path.exists(args['artifactsdir']):
        os.mkdir(args['artifactsdir'])

    return args

def run_filter(filter_class, data=None, ordered_dict=None):
    """
    Creates just a single filter artifact with enough metadata to be able to run a filter.
    """
    with temprun() as runner:
        artifact = FilterArtifact("key.txt")
        artifact.input_data = dexy.data.Json("%s" % random.randint(10000,99999), ".txt", runner)
        artifact.output_data = dexy.data.Json("%s" % random.randint(10000,99999), ".txt", runner)

        if ordered_dict:
            artifact.input_data._ordered_dict = ordered_dict
        elif data:
            artifact.input_data._data = data
        else:
            raise Exception("Must supply either data or ordered_dict")

        f = filter_class()
        f.artifact = artifact
        f.process()

        yield artifact.output_data

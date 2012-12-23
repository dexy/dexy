from StringIO import StringIO
from dexy.common import OrderedDict
from dexy.utils import char_diff
from mock import MagicMock
from nose.exc import SkipTest
import dexy.plugins # make sure plugins are loaded
import dexy.wrapper
import os
import re
import shutil
import sys
import tempfile

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def create_ordered_dict_from_dict(d):
    od = OrderedDict()
    for k, v in d.iteritems():
        od[k] = v
    return od

class tempdir(object):
    def make_temp_dir(self):
        self.tempdir = tempfile.mkdtemp()
        self.location = os.path.abspath(os.curdir)
        os.chdir(self.tempdir)

    def remove_temp_dir(self):
        os.chdir(self.location)
        try:
            shutil.rmtree(self.tempdir)
        except Exception as e:
            print e
            print "was not able to remove tempdir '%s'" % self.tempdir

    def __enter__(self):
        self.make_temp_dir()

    def __exit__(self, type, value, traceback):
        if not isinstance(value, Exception):
            self.remove_temp_dir()

class wrap(tempdir):
    """
    Create a temporary directory and initialize a dexy wrapper.
    """
    def __enter__(self):
        self.make_temp_dir()
        wrapper = dexy.wrapper.Wrapper()
        wrapper.setup(setup_dirs=True)
        return wrapper

    def __exit__(self, type, value, traceback):
        self.remove_temp_dir()
        if isinstance(value, dexy.exceptions.InactiveFilter):
            raise SkipTest
            return True # swallow InactiveFilter error

class runfilter(wrap):
    """
    Create a temporary directory, initialize a doc and a wrapper, and run the doc.
    """
    def __init__(self, filter_alias, doc_contents, ext=".txt"):
        self.filter_alias = filter_alias
        self.doc_contents = doc_contents
        self.ext = ext

    def __enter__(self):
        self.make_temp_dir()

        doc_key = "subdir/example%s|%s" % (self.ext, self.filter_alias)
        doc_spec = [doc_key, {"contents" : self.doc_contents}]

        try:
            wrapper = dexy.wrapper.Wrapper(doc_spec)
            wrapper.setup(setup_dirs=True)
            wrapper.run()
        except dexy.exceptions.InactiveFilter:
            raise SkipTest

        return wrapper.batch.tree[0].children[0]

def assert_output(filter_alias, doc_contents, expected_output, ext=".txt"):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_in_output must start with dot")

    if isinstance(expected_output, dict):
        expected_output = create_ordered_dict_from_dict(expected_output)
    if isinstance(doc_contents, dict):
        doc_contents = create_ordered_dict_from_dict(doc_contents)

    with runfilter(filter_alias, doc_contents, ext=ext) as doc:
        if expected_output:
            try:
                assert doc.output().data() == expected_output
            except AssertionError as e:
                if not isinstance(expected_output, OrderedDict):
                    print char_diff(unicode(doc.output()), expected_output)
                else:
                    print "Output: %s" % doc.output().data()
                    print "Expected: %s" % expected_output

                raise e
        else:
            raise Exception("Output is '%s'" % doc.output().data())

def assert_output_matches(filter_alias, doc_contents, expected_regex, ext=".txt"):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_in_output must start with dot")

    with runfilter(filter_alias, doc_contents, ext=ext) as doc:
        if expected_regex:
            assert re.match(expected_regex, unicode(doc.output()))
        else:
            raise Exception(unicode(doc.output()))

def assert_output_cached(filter_alias, doc_contents, ext=".txt", min_filesize=None):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_output_cached must start with dot")

    with runfilter(filter_alias, doc_contents, ext=ext) as doc:
        assert doc.output().is_cached()
        if min_filesize:
            assert doc.output().filesize() > min_filesize

def assert_in_output(filter_alias, doc_contents, expected_output, ext=".txt"):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_in_output must start with dot")

    with runfilter(filter_alias, doc_contents, ext=ext) as doc:
        if expected_output:
            assert expected_output in unicode(doc.output())
        else:
            raise Exception(unicode(doc.output()))

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

class run_templating_plugin():
    def __init__(self, klass, mock_attrs=None):
        if not mock_attrs:
            mock_attrs = {}
        self.f = MagicMock(**mock_attrs)
        self.plugin = klass(self.f)

    def __enter__(self):
        env = self.plugin.run()
        assert isinstance(env, dict)
        return env

    def __exit__(self, type, value, traceback):
        pass

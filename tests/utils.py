from io import StringIO
from dexy.data import Sectioned
from dexy.doc import Doc
from dexy.exceptions import InactivePlugin
from dexy.utils import char_diff
from dexy.utils import tempdir
from mock import MagicMock
from nose.exc import SkipTest
import os
import re
import sys

import dexy.load_plugins

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def make_wrapper():
    from dexy.wrapper import Wrapper
    return Wrapper(log_level = 'DEBUG', debug=True)

class wrap(tempdir):
    """
    Create a temporary directory and initialize a dexy wrapper.
    """
    def __enter__(self):
        self.make_temp_dir()
        wrapper = make_wrapper()
        wrapper.create_dexy_dirs()
        wrapper = make_wrapper()
        wrapper.to_valid()
        return wrapper

    def __exit__(self, type, value, traceback):
        self.remove_temp_dir()
        if isinstance(value, InactivePlugin):
            print(value.message)
            raise SkipTest
            return True # swallow InactivePlugin error

class runfilter(wrap):
    """
    Create a temporary directory, initialize a doc and a wrapper, and run the doc.
    """
    def __init__(self, filter_alias, doc_contents, ext=".txt", basename=None):
        self.filter_alias = filter_alias
        self.doc_contents = doc_contents
        self.ext = ext
        self.basename = basename

    def __enter__(self):
        self.make_temp_dir()

        def run_example(doc_key, doc_contents):
            wrapper = make_wrapper()

            if isinstance(doc_contents, str):
                data_class = 'generic'
            else:
                data_class = 'sectioned'

            doc = Doc(
                    doc_key,
                    wrapper,
                    [],
                    contents = doc_contents,
                    data_class = data_class
                    )
            wrapper.run_docs(doc)
            return doc

        try:
            wrapper = make_wrapper()
            wrapper.create_dexy_dirs()

            if self.basename:
                filename = "%s%s" % (self.basename, self.ext)
            else:
                filename = "example%s" % self.ext

            doc_key = "subdir/%s|%s" % (filename, self.filter_alias)

            doc = run_example(doc_key, self.doc_contents)

        except InactivePlugin:
            raise SkipTest

        return doc

def assert_output(filter_alias, doc_contents, expected_output, ext=".txt", basename=None):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_in_output must start with dot")

    if isinstance(doc_contents, dict):
        raise Exception("doc contents can't be dict")

    with runfilter(filter_alias, doc_contents, ext=ext, basename=basename) as doc:
        actual_output_data = doc.output_data()
        if isinstance(actual_output_data, Sectioned):
            for section_name, expected_section_contents in expected_output.items():
                try:
                    actual_section_contents = str(actual_output_data[section_name])
                    assert actual_section_contents == expected_section_contents
                except AssertionError:
                    print("Sections %s are not the same" % section_name)
                    print(char_diff(actual_section_contents, expected_section_contents))
        else:
            actual_output_data = str(doc.output_data())
            try:
                assert actual_output_data == expected_output
            except AssertionError:
                print(char_diff(actual_output_data, expected_output))

def assert_output_matches(filter_alias, doc_contents, expected_regex, ext=".txt"):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_in_output must start with dot")

    with runfilter(filter_alias, doc_contents, ext=ext) as doc:
        if expected_regex:
            assert re.match(expected_regex, str(doc.output_data()))
        else:
            raise Exception(str(doc.output_data()))

def assert_output_cached(filter_alias, doc_contents, ext=".txt", min_filesize=None):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_output_cached must start with dot")

    with runfilter(filter_alias, doc_contents, ext=ext) as doc:
        if doc.wrapper.state == 'ran':
            assert doc.output_data().is_cached()
            if min_filesize:
                assert doc.output_data().filesize() > min_filesize
        elif doc.wrapper.state == 'error':
            if isinstance(doc.wrapper.error, InactivePlugin):
                raise SkipTest()
            else:
                raise doc.wrapper.error
        else:
            raise Exception("state is '%s'" % doc.wrapper.state)

def assert_in_output(filter_alias, doc_contents, expected_output, ext=".txt"):
    if not ext.startswith("."):
        raise Exception("ext arg to assert_in_output must start with dot")

    with runfilter(filter_alias, doc_contents, ext=ext) as doc:
        if expected_output:
            actual_output = str(doc.output_data())
            msg = "did not find expected '%s' in actual output '%s'"
            assert expected_output in actual_output, msg % (expected_output, actual_output)
        else:
            raise Exception(str(doc.output_data()))

class capture_stdout():
    def __enter__(self):
        self.old_stdout = sys.stdout
        self.my_stdout = StringIO()
        sys.stdout = self.my_stdout
        return self.my_stdout

    def __exit__(self, type, value, traceback):
        sys.stdout = self.old_stdout
        self.my_stdout.close()

class capture_stderr():
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

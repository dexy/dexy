from dexy.filter import Filter
from tests.utils import runfilter
from nose.exc import SkipTest
from nose.tools import raises
from dexy.utils import s
from dexy.utils import split_path
from dexy.utils import iter_paths

def test_iter_path():
    full_path = "/foo/bar/baz"

    expected_paths = {
            0 : '/',
            1 : '/foo',
            2 : '/foo/bar',
            3 : '/foo/bar/baz'
            }

    for i, path in enumerate(iter_paths(full_path)):
        assert expected_paths[i] == path

def test_split_path():
    path = "foo/bar/baz"
    assert split_path(path) == ['foo', 'bar', 'baz']

def test_split_path_with_root():
    path = "/foo/bar/baz"
    assert split_path(path) == ['', 'foo', 'bar', 'baz']

def test_s():
    text = """This is some text
    which goes onto
    many lines and has
    indents at the start."""
    assert s(text) == 'This is some text which goes onto many lines and has indents at the start.'

class InactiveDexyFilter(Filter):
    """
    filter which is always inactive, for testing
    """
    aliases = ['inactive']

    def is_active(self):
        return False

@raises(SkipTest)
def test_inactive_filters_skip():
    with runfilter("inactive", "hello"):
        pass

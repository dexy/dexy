from dexy.filter import Filter
from dexy.tests.utils import runfilter
from nose.exc import SkipTest
from nose.tools import raises
from dexy.utils import s

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
    NODOC = True
    ALIASES = ['inactive']
    @classmethod
    def is_active(klass):
        return False

@raises(SkipTest)
def test_inactive_filters_skip():
    with runfilter("inactive", "hello"):
        pass

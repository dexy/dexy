from dexy.filter import Filter
from dexy.tests.utils import runfilter
from nose.exc import SkipTest
from nose.tools import raises

class InactiveDexyFilter(Filter):
    ALIASES = ['inactive']
    @classmethod
    def is_active(klass):
        return False

@raises(SkipTest)
def test_inactive_filters_skip():
    with runfilter("inactive", "hello"):
        pass

from tests.utils import tempdir
from nose.exc import SkipTest

try:
    from dexy_filter_examples import Cowsay
except ImportError:
    raise SkipTest()

def test_cowsay():
    with tempdir():
        for batch in Cowsay().dexy():
            print batch

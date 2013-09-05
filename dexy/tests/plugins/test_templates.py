from dexy.tests.utils import tempdir
from nose.exc import SkipTest

try:
    from dexy_filter_examples import Cowsay
except ImportError:
    raise SkipText()

def test_cowsay():
    with tempdir():
        for batch in Cowsay().dexy():
            print batch

from dexy.tests.utils import tempdir
from dexy_filter_examples import Cowsay

def test_cowsay():
    with tempdir():
        for batch in Cowsay.dexy():
            print batch

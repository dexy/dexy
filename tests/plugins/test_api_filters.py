from tests.utils import wrap
from mock import patch
import dexy.filter
import os

@patch('os.path.expanduser')
def test_docmd_create_keyfile(mod):
    mod.return_value = '.dexyapis'
    with wrap():
        assert not os.path.exists(".dexyapis")
        dexy.filter.Filter.create_instance("apis").docmd_create_keyfile()
        assert os.path.exists(".dexyapis")

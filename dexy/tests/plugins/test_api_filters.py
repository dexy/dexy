from dexy.plugins.api_filters import ApiFilter
from dexy.tests.utils import wrap
from mock import patch
import os

@patch('os.path.expanduser')
def test_docmd_create_keyfile(mod):
    mod.return_value = '.dexyapis'
    with wrap():
        assert not os.path.exists(".dexyapis")
        ApiFilter.docmd_create_keyfile()
        assert os.path.exists(".dexyapis")

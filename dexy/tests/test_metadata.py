from dexy.metadata import Md5

def test_hashstring_for_kind():
    meta = Md5()

    assert meta.hashstring_for_kind('file') == 'd751713988987e9331980363e24189ce'
    assert meta.hash_info_for_kinds(skip=['children']) == "[('args', 'd751713988987e9331980363e24189ce'), ('env', 'd751713988987e9331980363e24189ce'), ('file', 'd751713988987e9331980363e24189ce'), ('inputs', 'd751713988987e9331980363e24189ce')]"
    assert meta.hash_info_for_kinds(skip=['children', 'inputs']) == "[('args', 'd751713988987e9331980363e24189ce'), ('env', 'd751713988987e9331980363e24189ce'), ('file', 'd751713988987e9331980363e24189ce')]"

    assert meta.compute_hash() == 'd25e7984f990cb23c93787bc2e8e8a4c'
    assert meta.compute_hash_without_inputs() == '1846b79eada4ad757ff32694faa03aad'

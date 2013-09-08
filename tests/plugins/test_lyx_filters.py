from tests.utils import assert_output

def test_lyx():
    assert_output("lyxjinja",
            "dexy:foo.py|idio:multiply",
            "<< d['foo.py|idio']['multiply'] >>",
            ".tex")

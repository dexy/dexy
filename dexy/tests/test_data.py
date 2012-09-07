from dexy.runner import Runner
import dexy.data

def test_init_data():
    runner = Runner()
    data = dexy.data.GenericData("doc.txt", ".abc", "def123", runner)

    assert data.key == "doc.txt"
    assert data.name == "doc.abc"
    assert data.ext == ".abc"
    assert data.hashstring == "def123"

    assert not data.has_data()
    assert not data.is_cached()

def test_calculate_name():
    values = (
            ("doc.txt|abc|def", ".xyz", "doc.xyz"),
            ("doc.txt|abc|def", ".pdq", "doc.pdq"),
            ("doc.txt-abc-def.txt", ".pdq", "doc.txt-abc-def.pdq")
            )

    runner = Runner()
    for key, ext, name in values:
        data = dexy.data.Data(key, ext, "abc123", runner)
        assert data.name == name

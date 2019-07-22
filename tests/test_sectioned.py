from dexy.data import Sectioned
from dexy.exceptions import UserFeedback
from tests.utils import wrap
import os

def test_create_new_sectioned_data():
    with wrap() as wrapper:
        settings = {
                'canonical-name' : "doc.txt"
                }
        data = Sectioned("doc.txt", ".txt", "def123", settings, wrapper)
        data.setup()

        data['alpha'] = "This is the first section."
        data['alpha']['abc'] = 123
        assert str(data['alpha']) == "This is the first section."

        data['beta'] = "This is the second section."
        data['beta']['def'] = 456

        assert str(data['alpha']) == "This is the first section."
        assert str(data['beta']) == "This is the second section."
        assert data['alpha']['abc'] == 123
        assert data['beta']['def'] == 456

        data['gamma'] = "This is the third section."
        del data['beta']
        assert list(data.keys()) == ['alpha', 'gamma']

def test_load_json():
    with wrap() as wrapper:
        os.makedirs(".dexy/this/de")
        with open(".dexy/this/de/def123.txt", "w") as f:
            f.write("""
            [
                { "foo" : "bar" },
                { "name" : "alpha", "contents" : "This is the first section.", "abc" : 123 } ,
                { "name" : "beta", "contents" : "This is the second section.", "def" : 456 } 
            ]
            """)

        settings = {
                'canonical-name' : "doc.txt"
                }
        data = Sectioned("doc.txt", ".txt", "def123", settings, wrapper)
        data.setup_storage()

        assert list(data.keys()) == ["alpha", "beta"]
        assert str(data) == "This is the first section.\nThis is the second section."
        assert str(data) == "This is the first section.\nThis is the second section."
        assert data.keyindex("alpha") == 0
        assert data.keyindex("beta") == 1
        assert data.keyindex("gamma") == -1

        assert str(data["alpha"]) == "This is the first section."
        assert str(data["beta"]) == "This is the second section."
        assert str(data["alpha"]) == "This is the first section."
        assert str(data["beta"]) == "This is the second section."

        assert data["foo"] == "bar"

        assert data['alpha']['abc'] == 123
        assert data['beta']['def'] == 456

        try:
            data["zxx"]
            assert False, "should raise error"
        except UserFeedback as e:
            assert "No value for zxx" in str(e)

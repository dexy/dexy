from dexy.doc import Doc
from tests.utils import wrap
import dexy.data
import dexy.exceptions
import os

def test_sectioned_data_setitem_delitem():
    with wrap() as wrapper:
        contents=[
                {},
                {
                    "name" : "Welcome",
                    "contents" : "This is the first section."
                }
            ]

        doc = Doc("hello.txt",
                wrapper,
                [],
                data_type="sectioned",
                contents=contents
                )

        wrapper.run_docs(doc)
        data = doc.output_data()

        assert data.alias == 'sectioned'
        assert len(data) == 1

        # Add a new section
        data["Conclusions"] = "This is the final section."

        assert len(data) == 2
        
        assert str(data['Welcome']) == "This is the first section."
        assert str(data["Conclusions"]) == "This is the final section."

        # Modify an existing section
        data["Welcome"] = "This is the initial section."

        assert len(data) == 2

        assert str(data['Welcome']) == "This is the initial section."
        assert str(data["Conclusions"]) == "This is the final section."

        del data["Conclusions"]

        assert len(data) == 1
        assert list(data.keys()) == ["Welcome"]

def test_generic_data_unicode():
    with wrap() as wrapper:
        doc = Doc("hello.txt",
                wrapper,
                [],
                contents="\u2042 we know\n"
                )

        wrapper.run_docs(doc)
        data = doc.output_data()

        assert data.alias == 'generic'
        assert str(data) == "\u2042 we know\n"

        assert isinstance(str(data), str)

def test_generic_data_stores_string():
    with wrap() as wrapper:
        doc = Doc("hello.txt",
                wrapper,
                [],
                contents="hello"
                )

        wrapper.run_docs(doc)
        data = doc.output_data()

        assert data.alias == 'generic'
        assert data._data == "hello"

def test_sectioned_data_stores_list_of_dicts():
    with wrap() as wrapper:
        contents=[
                {},
                {
                    "name" : "Welcome",
                    "contents" : "This is the first section."
                }
            ]

        doc = Doc("hello.txt",
                wrapper,
                [],
                data_type="sectioned",
                contents=contents
                )

        wrapper.run_docs(doc)
        data = doc.output_data()

        assert data.alias == 'sectioned'
        assert data._data == contents
        assert data['Welcome']['contents'] == "This is the first section."
        assert data[0]['contents'] == "This is the first section."

def test_keyvalue_data_stores_dict():
    with wrap() as wrapper:
        doc = Doc("hello.json",
                wrapper,
                [],
                data_type="keyvalue",
                contents="dummy contents"
                )

        wrapper.run_docs(doc)
        data = doc.output_data()

        assert data.alias == 'keyvalue'
        assert list(data.keys()) == []

        data.append("foo", 123)
        data.append("bar", 456)

        assert sorted(data.keys()) == ["bar", "foo"]

def test_canonical_name():
    with wrap() as wrapper:
        doc = Doc("hello.txt",
                wrapper,
                [],
                contents="hello",
                output_name="yello.abc")

        wrapper.run_docs(doc)
        assert doc.output_data().output_name() == "yello.abc"
        wrapper.report()
        assert os.path.exists(os.path.join('output', 'yello.abc'))

def test_attempt_write_outside_project_root():
    with wrap() as wrapper:
        try:
            doc = Doc("../../example.txt",
                wrapper,
                [],
                contents = "hello")
            doc.setup()
            doc.setup_datas()
            assert False, 'should raise UserFeedback'
        except dexy.exceptions.UserFeedback as e:
            print(str(e))
            assert 'trying to write' in str(e)

def test_key_value_data():
    with wrap() as wrapper:
        settings = {
                'canonical-name' : 'doc.json',
                'storage-type' : 'json'
                }
        data = dexy.data.KeyValue("doc.json", ".json", "doc.json", settings, wrapper)
        data.setup_storage()

        assert not data._data
        assert data.storage._data == {}

        # We use the append method to add key-value pairs.
        data.append('foo', 'bar')
        assert len(list(data.keys())) == 1

        assert data.value('foo') == 'bar'
        assert data.storage['foo'] == 'bar'

def test_key_value_data_sqlite():
    with wrap() as wrapper:
        wrapper.to_walked()
        wrapper.to_checked()

        settings = {
                'canonical-name' : 'doc.sqlite3'
                }

        data = dexy.data.KeyValue("doc.sqlite3", ".sqlite3", "abc000", settings, wrapper)
        data.setup_storage()
        data.storage.connect()

        data.append('foo', 'bar')
        assert len(list(data.keys())) == 1

        assert data.value('foo') == 'bar'
        assert ["%s: %s" % (k, v) for k, v in data.items()][0] == "foo: bar"

def test_generic_data():
    with wrap() as wrapper:
        wrapper.to_walked()
        wrapper.to_checked()

        CONTENTS = "contents go here"

        # Create a GenericData object
        settings = {
                'canonical-name' : 'doc.txt'
                }
        data = dexy.data.Generic("doc.txt", ".txt", "abc000", settings, wrapper)
        data.setup_storage()

        # Assign some text contents
        data._data = CONTENTS
        assert data.has_data()
        assert not data.is_cached(True)

        # Save data to disk
        data.save()
        assert data.has_data()
        assert data.is_cached(True)
        assert data.filesize(True) > 10

        # Clear data from memory
        data._data = None

        # Load it again from disk
        data.load_data(True)
        assert data._data == CONTENTS

        assert data.as_text() == CONTENTS

def test_init_data():
    with wrap() as wrapper:
        settings = {
                'canonical-name' : 'doc.abc'
                }
        data = dexy.data.Generic("doc.txt", ".abc", "def123", settings, wrapper)
        data.setup_storage()

        assert data.key == "doc.txt"
        assert data.name == "doc.abc"
        assert data.ext == ".abc"
        assert data.storage_key == "def123"

        assert not data.has_data()
        assert not data.is_cached()

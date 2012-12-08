from dexy.doc import Doc
from dexy.tests.utils import wrap
from dexy.wrapper import Wrapper
import dexy.data
import dexy.exceptions
import os

def test_canonical_name():
    with wrap() as wrapper:
        doc = Doc("hello.txt",
                contents="hello",
                canonical_name="yello.abc",
                wrapper=wrapper)

        wrapper.run_docs(doc)
        assert doc.output().name == "yello.abc"
        wrapper.report()
        assert os.path.exists(os.path.join('output', 'yello.abc'))

def test_attempt_write_outside_project_root():
    with wrap() as wrapper:
        doc = Doc("../../example.txt",
                contents = "hello",
                wrapper=wrapper)

        try:
            wrapper.run_docs(doc)
            wrapper.report()
            assert False, 'should raise UserFeedback'
        except dexy.exceptions.UserFeedback as e:
            assert 'trying to write' in str(e)

def test_key_value_data():
    with wrap() as wrapper:
        data = dexy.data.KeyValue("doc.json", ".json", "doc.json", "hash1", {}, wrapper, storage_type='json')

        assert not data._data
        assert data.storage._data == {}

        # We use the append method to add key-value pairs.
        data.append('foo', 'bar')
        assert len(data.keys()) == 1

        assert data.value('foo') == 'bar'
        assert data.storage['foo'] == 'bar'
        assert data.as_text() == "foo: bar"
        data.as_sectioned()['foo'] == 'bar'

def test_key_value_data_sqlite():
    with wrap() as wrapper:
        data = dexy.data.KeyValue("doc.sqlite3", ".sqlite3", "doc.sqlite3", "hash1", {}, wrapper)

        data.append('foo', 'bar')
        assert len(data.keys()) == 1

        assert data.value('foo') == 'bar'
        assert ["%s: %s" % (k, v) for k, v in data.storage][0] == "foo: bar"

        data.as_text() == "foo: bar"

def test_generic_data():
    with wrap() as wrapper:
        CONTENTS = "contents go here"

        # Create a GenericData object
        data = dexy.data.Generic("doc.txt", ".txt", "doc.txt", "hash1", {}, wrapper)

        # Assign some text contents
        data._data = CONTENTS
        assert data.has_data()
        assert not data.is_cached()
        assert not data.filesize()

        # Save data to disk
        data.save()
        assert data.has_data()
        assert data.is_cached()
        assert data.filesize() > 10

        # Clear data from memory
        data._data = None
        assert data.has_data()

        # Load it again from disk
        data.load_data()
        assert data._data == CONTENTS

        # The convenience methods load from disk if needed.
        data._data = None
        assert data.as_text() == CONTENTS

        data._data = None
        assert data.as_sectioned()['1'] == CONTENTS

def test_init_data():
    wrapper = Wrapper()
    data = dexy.data.Generic("doc.txt", ".abc", "doc.abc", "def123", {}, wrapper)

    assert data.key == "doc.txt"
    assert data.name == "doc.abc"
    assert data.ext == ".abc"
    assert data.hashstring == "def123"

    assert not data.has_data()
    assert not data.is_cached()

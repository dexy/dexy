from dexy.doc import Doc
from dexy.tests.utils import wrap

def test_filter_args():
    with wrap() as wrapper:
        doc = Doc(
                "hello.txt|filterargs",
                contents="hello",
                foo="bar",
                filterargs={"abc" : 123, "foo" : "baz" },
                wrapper=wrapper)

        wrapper.run_docs(doc)

        result = doc.output().data()

        assert "Here are the arguments you passed:" in result
        assert "abc: 123" in result
        assert "foo: baz" in result
        assert not "foo: bar" in result


from dexy.tests.utils import wrap
import dexy.filter

def test_filter_iter():
    for instance in dexy.filter.Filter:
        print instance, instance.setting('aliases')

def test_filter_args():
    with wrap() as wrapper:
        import dexy.node
        doc = dexy.node.Node.create_instance('doc',
                "hello.txt|filterargs",
                wrapper,
                [],
                contents="hello",
                foo="bar",
                filterargs={"abc" : 123, "foo" : "baz" }
                )

        wrapper.run_docs(doc)

        result = str(doc.output_data())

        assert "Here are the filter settings:" in result
        assert "abc: 123" in result
        assert "foo: baz" in result
        assert "foo: bar" in result


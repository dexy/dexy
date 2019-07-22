from tests.utils import wrap
import dexy.filter

def test_filters_by_tag():
    tags_filters = dexy.filter.filters_by_tag()
    assert 'latex' in list(tags_filters.keys())

def test_filter_aliases_by_tag():
    first_expected_tag = 'R'
    first_actual = dexy.filter.filter_aliases_by_tag()[0][0]
    assert first_actual == first_expected_tag, first_actual

def test_filter_iter():
    for instance in dexy.filter.Filter:
        assert instance.setting('aliases')

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


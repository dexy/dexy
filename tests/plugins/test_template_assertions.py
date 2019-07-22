from tests.plugins.test_templating_filters import run_jinja_filter
from dexy.doc import Doc
from tests.utils import wrap
import inspect

def test_assert_equals():
    assert str(run_jinja_filter("{{ 'foo' | assert_equals('foo') }}")) == 'foo'

def test_assert_equals_invalid():
    try:
        str(run_jinja_filter("{{ 'foo' | assert_equals('bar') }}"))
        raise Exception("should raise AssertionError")
    except AssertionError as e:
        assert str(e) == "input text did not equal 'bar'"

def test_assert_contains():
    assert str(run_jinja_filter("{{ 'foo bar' | assert_contains('foo') }}")) == 'foo bar'

def test_assert_contains_invalid():
    try:
        str(run_jinja_filter("{{ 'foo bar' | assert_contains('baz') }}"))
        raise Exception("should raise AssertionError")
    except AssertionError as e:
        assert str(e) == "input text did not contain 'baz'"

def test_assert_does_not_contain():
    assert str(run_jinja_filter("{{ 'foo bar' | assert_does_not_contain('baz') }}")) == 'foo bar'

def test_assert_does_not_contain_invalid():
    try:
        str(run_jinja_filter("{{ 'foo bar baz' | assert_does_not_contain('baz') }}"))
        raise Exception("should raise AssertionError")
    except AssertionError as e:
        assert str(e) == "input text contained 'baz'"

def test_assert_startswith():
    assert str(run_jinja_filter("{{ 'foo bar' | assert_startswith('foo') }}")) == 'foo bar'

def test_assert_startswith_invalid():
    try:
        str(run_jinja_filter("{{ 'foo bar' | assert_startswith('bar') }}"))
        raise Exception("should raise AssertionError")
    except AssertionError as e:
        assert str(e) == "input text did not start with 'bar'"

def test_assert_matches():
    assert str(run_jinja_filter("{{ 'foo bar baz' | assert_matches('^foo') }}")) == 'foo bar baz'

def test_assert_matches_invalid():
    try:
        str(run_jinja_filter("{{ 'foo bar' | assert_matches('^baz') }}"))
        raise Exception("should raise AssertionError")
    except AssertionError as e:
        assert str(e) == "input text did not match regexp ^baz"

def test_assert_selector():
    with wrap() as wrapper:
        node = Doc("hello.txt|jinja",
                wrapper,
                [
                    Doc("input.html",
                        wrapper,
                        [],
                        contents = inspect.cleandoc("""
                        <div id="foo">
                        This is contents of foo div.
                        </div>
                        """
                        ))
                    ],
                contents = "{{ d['input.html'] | assert_selector_text('#foo', 'This is contents of foo div.') }}"
                )
        wrapper.run_docs(node)

def test_assert_selector_invalid():
    with wrap() as wrapper:
        node = Doc("hello.txt|jinja",
                wrapper,
                [
                    Doc("input.html",
                        wrapper,
                        [],
                        contents = inspect.cleandoc("""
                        <div id="foo">
                        This is contents of foo div.
                        </div>
                        """
                        ))
                    ],
                contents = "{{ d['input.html'] | assert_selector_text('#foo', 'Not right.') }}"
                )

        try:
            wrapper.run_docs(node)
            raise Exception("should raise AssertionError")
        except AssertionError as e:
            assert str(e) == "element '#foo' did not contain 'Not right.'"

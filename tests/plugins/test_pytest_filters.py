from tests.utils import wrap
from dexy.doc import Doc
from nose.exc import SkipTest

def test_pytest_filter():
    raise SkipTest() # this is running dexy's tests, not cashew's tests
    with wrap() as wrapper:
        doc = Doc(
                "modules.txt|pytest",
                wrapper,
                [],
                contents="cashew"
                )
        wrapper.run_docs(doc)
        data = doc.output_data()

        testname = "test_cashew.test_standardize_alias_or_aliases"
        assert data[testname + ':doc'] == "docstring for test"
        assert data[testname + ':name'] == "test_standardize_alias_or_aliases"
        assert data[testname + ':comments'] == "# comment before test\n"
        assert bool(data[testname + ':passed'])
        assert "def test_standardize_alias_or_aliases():" in data[testname + ':source']

from tests.utils import wrap
from dexy.doc import Doc

def test_pytest_filter():
    with wrap() as wrapper:
        doc = Doc(
                "modules.txt|pytest",
                wrapper,
                [],
                contents="dexy_viewer"
                )
        wrapper.run_docs(doc)
        data = doc.output_data()

        testname = "test_viewer.basic_test"
        assert data[testname + ':doc'] == "docstring for test"
        assert data[testname + ':name'] == "basic_test"
        assert data[testname + ':comments'] == "# comment before test\n"
        assert bool(data[testname + ':passed'])
        assert "def basic_test():" in data[testname + ':source']

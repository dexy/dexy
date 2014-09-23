from tests.utils import wrap
from dexy.doc import Doc

python_file_content = """
import math

# Comment for foo
def foo():
    '''
    docstring for foo
    '''
    return True

# Comment for bar
def bar():
    '''
    docstring for bar
    '''
    return False

"""

def test_pyparse_filter_on_python_files():
    with wrap() as wrapper:
        doc = Doc("source.py|pyparse", wrapper, [], contents=python_file_content)
        wrapper.run_docs(doc)

        data = doc.output_data()
        keys = data.keys()

        assert 'bar:source' in keys
        assert 'foo:source' in keys
        
        assert data['foo:doc'] == "docstring for foo"
        #assert data['foo:comments'] == "# Comment for foo\n"

        assert data['bar:doc'] == "docstring for bar"
        #assert data['bar:comments'] == "# Comment for bar\n"

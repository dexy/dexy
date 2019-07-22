from tests.utils import wrap
from dexy.doc import Doc

def test_pydoc_filter_on_module_names():
    with wrap() as wrapper:
        doc = Doc("modules.txt|pydoc", wrapper, [], contents="os math")
        wrapper.run_docs(doc)
        data = doc.output_data()
        assert len(list(data.keys())) > 100
        assert data['math.e:value'].startswith("2.71828")

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

def test_pydoc_filter_on_python_files():
    with wrap() as wrapper:
        doc = Doc("source.py|pydoc", wrapper, [], contents=python_file_content)
        wrapper.run_docs(doc)

        data = doc.output_data()
        keys = list(data.keys())

        assert 'bar:source' in keys
        assert 'foo:source' in keys
        
        assert data['foo:doc'] == "docstring for foo"
        assert data['foo:comments'] == "# Comment for foo\n"

        assert data['bar:doc'] == "docstring for bar"
        assert data['bar:comments'] == "# Comment for bar\n"
        

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


# Comment before decorator
@decorator
@another
def decorated():
    pass

@decorator(some, args)
def decorated_with_args():
    pass


class Foo(object):
    @decorator
    @another
    def decorated(self):
        pass


@decorator
class Decorated(object):
    pass
"""

def test_pyparse_filter_on_python_files():
    with wrap() as wrapper:
        doc = Doc("source.py|pyparse", wrapper, [], contents=python_file_content)
        wrapper.run_docs(doc)

        data = doc.output_data()
        keys = list(data.keys())

        assert 'bar:source' in keys
        assert 'foo:source' in keys
        
        assert data['foo:doc'] == "docstring for foo"
        assert data['foo:source'].startswith("def foo():\n")

        assert data['bar:doc'] == "docstring for bar"
        assert data['bar:source'].startswith("def bar():\n")

        assert data['decorated:source'].startswith("@decorator\n@another\ndef decorated():\n")

        assert data['Foo:source'].startswith("class Foo(object):\n")

        assert data['Foo.decorated:source'].startswith("    @decorator\n    @another\n    def decorated(self):\n")

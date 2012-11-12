from dexy.parser import AbstractSyntaxTree
from dexy.tests.utils import wrap

def test_ast():
    with wrap() as wrapper:
        ast = AbstractSyntaxTree()
        ast.wrapper = wrapper

        ast.add_task_info("abc.txt", foo='bar')
        ast.add_dependency("abc.txt", "def.txt")
        ast.add_task_info("def.txt", foo='baz')

        assert ast.tree == ['doc:abc.txt']
        assert ast.task_kwargs('doc:abc.txt')['foo'] == 'bar'
        assert ast.task_kwargs('doc:def.txt')['foo'] == 'baz'

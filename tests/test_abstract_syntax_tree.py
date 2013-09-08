from dexy.parser import AbstractSyntaxTree
from tests.utils import wrap
import dexy.batch

def test_ast():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)

        ast.add_node("abc.txt", foo='bar', contents = 'abc')
        ast.add_dependency("abc.txt", "def.txt")
        ast.add_node("def.txt", foo='baz', contents = 'def')

        assert ast.tree == ['doc:abc.txt']
        assert ast.args_for_node('doc:abc.txt')['foo'] == 'bar'
        assert ast.args_for_node('doc:def.txt')['foo'] == 'baz'
        assert ast.inputs_for_node('abc.txt') == ['doc:def.txt']
        assert not ast.inputs_for_node('def.txt')

        ast.walk()
        assert len(wrapper.roots) == 1
        assert len(wrapper.nodes) == 2

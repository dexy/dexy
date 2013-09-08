from dexy.exceptions import UserFeedback
from dexy.parser import AbstractSyntaxTree
from dexy.parsers.doc import Yaml
from tests.utils import capture_stderr
from tests.utils import wrap
from dexy.wrapper import Wrapper
import dexy.batch
import os

def test_hard_tabs_in_config():
    with wrap():
        with capture_stderr() as stderr:
            os.makedirs("abc/def")
            with open("abc/def/dexy.yaml", "w") as f:
                f.write("""foo:\t- .txt""")

            wrapper = Wrapper()

            try:
                wrapper.run_from_new()
            except UserFeedback as e:
                assert "hard tabs" in str(e)

            assert "abc/def/dexy.yaml" in stderr.getvalue()

def test_subdir_config_with_bundle():
    with wrap():
        with open("dexy.yaml", "w") as f:
            f.write("""
            foo:
                - .txt
            """)

        os.makedirs("abc/def")
        with open("abc/def/dexy.yaml", "w") as f:
            f.write("""
            bar:
                - .py
            """)

        with open("abc/def/hello.py", "w") as f:
            f.write("print 'hello'")

        wrapper = Wrapper()
        wrapper.run_from_new()
        assert "doc:abc/def/hello.py" in wrapper.nodes

        wrapper = Wrapper(recurse=False)
        wrapper.run_from_new()
        assert not "doc:abc/def/hello.py" in wrapper.nodes

        wrapper = Wrapper(recurse=False, configs="abc/def/dexy.yaml")
        wrapper.run_from_new()
        assert "doc:abc/def/hello.py" in wrapper.nodes

def test_except_patterndoc():
    with wrap() as wrapper:
        with open("exceptme.abc", "w") as f:
            f.write("hello")

        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', """.abc:\n  - except : 'exceptme.abc' """)
        ast.walk()

        assert len(wrapper.nodes) == 1

def test_except_patterndoc_pattern():
    with wrap() as wrapper:
        with open("exceptme.abc", "w") as f:
            f.write("hello")

        wrapper = Wrapper()
        wrapper.to_valid()

        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', """.abc:\n  - except : 'exceptme.*' """)
        ast.walk()
        wrapper.transition('walked')
        wrapper.to_checked()

        wrapper.run()

        assert len(wrapper.nodes) == 1

def test_children_siblings_order():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', """
        p1:
            - c1
            - c2:
                - g1
                - g2
                - g3
            - c3
        """)
        ast.walk()
        wrapper.transition('walked')

        wrapper.to_checked()

        wrapper.run()

        p1 = wrapper.nodes['bundle:p1']
        assert [i.key_with_class() for i in p1.walk_inputs()] == [
                'bundle:c1',
                'bundle:c2',
                'bundle:g1',
                'bundle:g2',
                'bundle:g3',
                'bundle:c3'
                ]

        c1 = wrapper.nodes['bundle:c1']
        assert len(c1.inputs) == 0

        c2 = wrapper.nodes['bundle:c2']
        assert [i.key_with_class() for i in c2.walk_inputs()] == [
                'bundle:g1',
                'bundle:g2',
                'bundle:g3'
                ]

        c3 = wrapper.nodes['bundle:c3']
        assert len(c3.inputs) == 0

        g3 = wrapper.nodes['bundle:g3']
        assert len(g3.inputs) == 0

def test_single_file_doc():
    with wrap() as wrapper:
        with open("hello.txt", "w") as f:
            f.write("hello")

        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', "hello.txt")
        ast.walk()
        wrapper.transition('walked')

        wrapper.to_checked()

        wrapper.run()
        assert "doc:hello.txt" in wrapper.nodes

def test_single_bundle_doc():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', "hello")
        ast.walk()
        wrapper.transition('walked')
        wrapper.to_checked()
        assert "bundle:hello" in wrapper.nodes

def test_single_bundle_doc_with_args():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', """
        more:
            - hello
            - one-more-task
            - foo: bar

        hello:
            - foo: bar
            - filter_fruit: orange
            - args:
                - ping: pong
            - another-task:
                - foo: baz
                - yet-another-task:
                    - foo: bar
            - one-more-task
        """)
        ast.walk()

        assert wrapper.roots[0].key_with_class() == "bundle:more"
        assert len(wrapper.nodes) == 5

def test_single_bundle_doc_with_args_2():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', """

      -  hello:
            - foo: bar
            - filter_fruit: orange
            - args:
                - ping: pong
            - another-task:
                - foo: baz
                - yet-another-task:
                    - foo: bar
            - one-more-task

      -  more:
            - hello
            - one-more-task
            - foo: bar

        """)

        ast.walk()

        assert wrapper.roots[0].key_with_class() == "bundle:more"
        assert len(wrapper.nodes) == 5

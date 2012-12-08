from dexy.plugins.parsers import YamlFileParser
from dexy.tests.utils import wrap
from dexy.tests.utils import tempdir
import os
import dexy.wrapper

def test_subdir_config_with_bundle():
    with tempdir():

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

        wrapper = dexy.wrapper.Wrapper()
        wrapper.setup(setup_dirs=True)
        wrapper.run()

def test_except_patterndoc():
    with wrap() as wrapper:
        with open("exceptme.abc", "w") as f:
            f.write("hello")

        parser = YamlFileParser(wrapper)
        parser.parse(""".abc:\n  - except : 'exceptme.abc' """)
        wrapper.batch.run()

        assert len(wrapper.batch.lookup_table) == 1

def test_except_patterndoc_pattern():
    with wrap() as wrapper:
        with open("exceptme.abc", "w") as f:
            f.write("hello")

        parser = YamlFileParser(wrapper)
        parser.parse(""".abc:\n  - except : 'exceptme.*' """)
        wrapper.batch.run()

        assert len(wrapper.batch.lookup_table) == 1

def test_children_siblings_order():
    with wrap() as wrapper:
        parser = YamlFileParser(wrapper)
        parser.parse("""
        p1:
            - c1
            - c2:
                - g1
                - g2
                - g3
            - c3
        """)

        wrapper.batch.run()

        p1 = wrapper.batch.lookup_table['BundleDoc:p1']
        assert p1.deps.keys() == [
                'BundleDoc:c1',
                'BundleDoc:c2',
                'BundleDoc:g1',
                'BundleDoc:g2',
                'BundleDoc:g3',
                'BundleDoc:c3'
                ]

        c1 = wrapper.batch.lookup_table['BundleDoc:c1']
        assert c1.deps.keys() == []

        c2 = wrapper.batch.lookup_table['BundleDoc:c2']
        assert c2.deps.keys() == [
                'BundleDoc:c1',
                'BundleDoc:g1',
                'BundleDoc:g2',
                'BundleDoc:g3'
                ]

        c3 = wrapper.batch.lookup_table['BundleDoc:c3']
        assert c3.deps.keys() == [
                'BundleDoc:c1',
                'BundleDoc:c2'
                ]

        g3 = wrapper.batch.lookup_table['BundleDoc:g3']
        assert g3.deps.keys() == [
                'BundleDoc:g1',
                'BundleDoc:g2'
                ]

def test_single_file_doc():
    with wrap() as wrapper:
        with open("hello.txt", "w") as f:
            f.write("hello")

        parser = YamlFileParser(wrapper)
        parser.parse("hello.txt")

        wrapper.batch.run()
        assert "Doc:hello.txt" in wrapper.batch.lookup_table

def test_single_bundle_doc():
    with wrap() as wrapper:
        parser = YamlFileParser(wrapper)
        parser.parse("hello")

        wrapper.batch.run()
        assert "BundleDoc:hello" in wrapper.batch.lookup_table

def test_single_bundle_doc_with_args():
    with wrap() as wrapper:
        parser = YamlFileParser(wrapper)
        parser.parse("""
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

        wrapper.batch.run()

        assert wrapper.batch.tree[0].key_with_class() == "BundleDoc:more"
        assert len(wrapper.batch.lookup_table) == 5

def test_single_bundle_doc_with_args_2():
    with wrap() as wrapper:
        parser = YamlFileParser(wrapper)
        parser.parse("""

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

        wrapper.batch.run()

        assert wrapper.batch.tree[0].key_with_class() == "BundleDoc:more"
        assert len(wrapper.batch.lookup_table) == 5

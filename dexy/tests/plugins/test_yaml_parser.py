from dexy.plugins.parsers import YamlFileParser
from dexy.tests.utils import wrap

def test_except_patterndoc():
    with wrap() as wrapper:
        with open("exceptme.abc", "w") as f:
            f.write("hello")

        parser = YamlFileParser(wrapper)
        parser.parse(""".abc:\n  - except : 'exceptme.abc' """)
        wrapper.run()

        assert len(wrapper.tasks) == 1

def test_except_patterndoc_pattern():
    with wrap() as wrapper:
        with open("exceptme.abc", "w") as f:
            f.write("hello")

        parser = YamlFileParser(wrapper)
        parser.parse(""".abc:\n  - except : 'exceptme.*' """)
        wrapper.run()

        assert len(wrapper.tasks) == 1

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

        wrapper.run()

        p1 = wrapper.tasks['BundleDoc:p1']
        assert p1.deps.keys() == [
                'BundleDoc:c1',
                'BundleDoc:c2',
                'BundleDoc:g1',
                'BundleDoc:g2',
                'BundleDoc:g3',
                'BundleDoc:c3'
                ]

        c1 = wrapper.tasks['BundleDoc:c1']
        assert c1.deps.keys() == []

        c2 = wrapper.tasks['BundleDoc:c2']
        assert c2.deps.keys() == [
                'BundleDoc:c1',
                'BundleDoc:g1',
                'BundleDoc:g2',
                'BundleDoc:g3'
                ]

        c3 = wrapper.tasks['BundleDoc:c3']
        assert c3.deps.keys() == [
                'BundleDoc:c1',
                'BundleDoc:c2'
                ]

        g3 = wrapper.tasks['BundleDoc:g3']
        assert g3.deps.keys() == [
                'BundleDoc:g1',
                'BundleDoc:g2'
                ]

        assert wrapper.tasks.keys() == [
                'BundleDoc:c1',
                'BundleDoc:g1',
                'BundleDoc:g2',
                'BundleDoc:g3',
                'BundleDoc:c2',
                'BundleDoc:c3',
                'BundleDoc:p1'
                ]

def test_single_file_doc():
    with wrap() as wrapper:
        with open("hello.txt", "w") as f:
            f.write("hello")

        parser = YamlFileParser(wrapper)
        parser.parse("hello.txt")

        wrapper.run()
        assert "Doc:hello.txt" in wrapper.tasks

def test_single_bundle_doc():
    with wrap() as wrapper:
        parser = YamlFileParser(wrapper)
        parser.parse("hello")

        wrapper.run()
        assert "BundleDoc:hello" in wrapper.tasks

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

        wrapper.run()

        assert wrapper.root_nodes[0].key_with_class() == "BundleDoc:more"
        assert len(wrapper.tasks) == 5

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

        wrapper.run()

        assert wrapper.root_nodes[0].key_with_class() == "BundleDoc:more"
        assert len(wrapper.tasks) == 5

from dexy.plugins.parsers import YamlFileParser
from dexy.tests.utils import wrap

def test_single_file_doc():
    with wrap() as wrapper:
        with open("hello.txt", "w") as f:
            f.write("hello")

        parser = YamlFileParser(wrapper)
        parser.parse("hello.txt")

        wrapper.run()

def test_single_bundle_doc():
    with wrap() as wrapper:
        parser = YamlFileParser(wrapper)
        parser.parse("hello")

        wrapper.run()

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

        assert wrapper.docs_to_run[0].key_with_class() == "BundleDoc:more"
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

        assert wrapper.docs_to_run[0].key_with_class() == "BundleDoc:more"
        assert len(wrapper.tasks) == 5

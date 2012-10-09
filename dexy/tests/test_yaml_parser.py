from dexy.parser import YamlFileParser
from dexy.tests.utils import wrap

def test_single_file_doc():
    with wrap() as wrapper:
        with open("hello.txt", "w") as f:
            f.write("hello")

        parser = YamlFileParser(wrapper)
        docs = parser.parse("hello.txt")

        wrapper.run_docs(docs)

def test_single_bundle_doc():
    with wrap() as wrapper:
        parser = YamlFileParser(wrapper)
        docs = parser.parse("hello")

        wrapper.run_docs(docs)

def test_single_bundle_doc_with_args():
    with wrap() as wrapper:
        parser = YamlFileParser(wrapper)
        docs = parser.parse("""
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

        more:
            - foo: bar
        """)

        assert len(docs) == 2
        wrapper.run_docs(docs)
        assert len(wrapper.tasks) == 5

def test_single_bundle_doc_with_args_2():
    with wrap() as wrapper:
        parser = YamlFileParser(wrapper)
        docs = parser.parse("""

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
            - foo: bar

        """)

        assert len(docs) == 2
        wrapper.run_docs(docs)
        assert len(wrapper.tasks) == 5

        assert docs[0] in docs[1].children

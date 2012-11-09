from dexy.plugins.parsers import OriginalDexyParser
from dexy.plugins.parsers import TextFileParser
from dexy.plugins.parsers import YamlFileParser
from dexy.tests.utils import wrap
import dexy.exceptions

def test_invalid_yaml():
    with wrap() as wrapper:
        parser = YamlFileParser()
        parser.wrapper = wrapper
        try:
            parser.parse(INVALID_YAML)
            assert False, "should raise UserFeedback"
        except dexy.exceptions.UserFeedback as e:
            assert 'YAML' in e.message

def test_yaml_parser():
    with wrap() as wrapper:
        parser = YamlFileParser()
        parser.wrapper = wrapper
        parser.parse(YAML)
        docs = wrapper.root_nodes
        for doc in docs:
            assert doc.__class__.__name__ == 'BundleDoc'
            assert doc.key in ['code', 'wordpress']

def test_text_parser_blank_lines():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper = wrapper
        parser.parse("\n\n")
        docs = wrapper.root_nodes
        assert len(docs) == 0

def test_text_parser_comments():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper = wrapper
        parser.parse("""
        valid.doc
        # commented-out.doc
        """)

        docs = wrapper.root_nodes
        assert len(docs) == 1
        assert docs[0].key == "valid.doc"

def test_text_parser_valid_json():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper=wrapper
        parser.parse("""
        doc.txt { "contents" : 123 }
        """)

        docs = wrapper.root_nodes
        assert docs[0].key == "doc.txt"
        assert docs[0].args['contents'] == 123

def test_text_parser_invalid_json():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper = wrapper

        try:
            parser.parse("""
            doc.txt { "contents" : 123
            """)
            assert False, 'should raise UserFeedback'
        except dexy.exceptions.UserFeedback as e:
            assert 'unable to parse' in e.message

def test_text_parser():
    with wrap() as wrapper:
        with open("f1.py", "w") as f:
            f.write("print 'hello'")

        with open("f2.py", "w") as f:
            f.write("print 'hello'")

        with open("index.md", "w") as f:
            f.write("")

        parser = TextFileParser()
        parser.wrapper = wrapper
        parser.parse("""
        *.py
        *.py|pyg
        *.md|jinja
        """)

        wrapper.run()

        docs = wrapper.registered_docs()
        assert len(docs) == 5

def test_text_parser_virtual_file():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper = wrapper
        parser.parse("""
        virtual.txt { "contents" : "hello" }
        """)

        wrapper.run()
        docs = wrapper.root_nodes

        assert docs[0].key == "virtual.txt"
        assert docs[0].output().as_text() == "hello"

def test_original_parser():
    with wrap() as wrapper:
        conf = """{
        "*.txt" : {}
        }"""

        parser = OriginalDexyParser()
        parser.wrapper = wrapper
        parser.parse(conf)

        assert wrapper.root_nodes[0].key_with_class() == "PatternDoc:*.txt"

def test_original_parser_allinputs():
    with wrap() as wrapper:
        conf = """{
        "*.txt" : {},
        "hello.txt" : { "contents" : "Hello!" },
        "*.md|jinja" : { "allinputs" : true }
        }"""

        parser = OriginalDexyParser(wrapper)
        parser.wrapper = wrapper
        parser.parse(conf)

        assert len(wrapper.root_nodes) == 1
        assert wrapper.root_nodes[0].key_with_class() == "PatternDoc:*.md|jinja"

INVALID_YAML = """\
code:
    - abc
    def
"""

YAML = """\
code:
    - .R|pyg:
         "pyg" : { "foo" : "bar" }
    - .R|idio

wordpress:
    - code
    - test.txt|jinja
    - .md|jinja|markdown|wp
"""

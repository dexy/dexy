from dexy.parsers.standard import Yaml
from dexy.parsers.standard import TextFile
from dexy.parsers.standard import Original
from dexy.tests.utils import wrap
import dexy.exceptions
import os
from dexy.parser import AbstractSyntaxTree

def test_text_parser():
    with wrap() as wrapper:

        with open("f1.py", "w") as f:
            f.write("print 'hello'")

        with open("f2.py", "w") as f:
            f.write("print 'hello'")

        with open("index.md", "w") as f:
            f.write("")

        ast = AbstractSyntaxTree(wrapper)
        parser = TextFile(wrapper, ast)
        parser.parse(".", """
        *.py
        *.py|pyg
        *.md|jinja
        """)

        docs = wrapper.batch.docs()
        assert len(docs) == 5

YAML_WITH_INACTIVE = """
foo:
    - inactive: True
"""

def test_parse_inactive():
    with wrap() as wrapper:
        parser = Yaml(wrapper)
        parser.parse(YAML_WITH_INACTIVE)

        wrapper.batch.run()
        assert len(wrapper.batch.tasks()) == 0

YAML_WITH_DEFAULT_OFF = """
foo:
    - default: False
"""

def test_parse_default():
    with wrap() as wrapper:
        parser = Yaml()
        parser.wrapper = wrapper
        parser.parse(YAML_WITH_DEFAULT_OFF)

        wrapper.batch.run()
        assert len(wrapper.batch.tasks()) == 1

    with wrap() as wrapper:
        wrapper.full = True
        parser = Yaml()
        parser.wrapper = wrapper
        parser.parse(YAML_WITH_DEFAULT_OFF)

        wrapper.batch.run()
        assert len(wrapper.batch.tasks()) == 1

def test_yaml_with_defaults():
    with wrap() as wrapper:
        os.makedirs("s1/s2")

        with open("s1/s2/hello.txt", "w") as f:
            f.write("hello")

        wrapper.walk()
        parser = Yaml()
        parser.wrapper = wrapper
        parser.parse(YAML_WITH_DEFAULTS)

        assert wrapper.batch.tree[0].args['foo'] == 'bar'
    
def test_invalid_yaml():
    with wrap() as wrapper:
        parser = Yaml()
        parser.wrapper = wrapper
        try:
            parser.parse(INVALID_YAML)
            assert False, "should raise UserFeedback"
        except dexy.exceptions.UserFeedback as e:
            assert 'YAML' in e.message

def test_yaml_parser():
    with wrap() as wrapper:
        parser = Yaml()
        parser.wrapper = wrapper
        parser.parse(YAML)
        docs = wrapper.batch.tree
        for doc in docs:
            assert doc.__class__.__name__ == 'BundleNode'
            assert doc.key in ['code', 'wordpress']
            for inpt in doc.walk_inputs():
                print inpt

        wrapper.run()


def test_text_parser_blank_lines():
    with wrap() as wrapper:
        parser = TextFile(wrapper)
        parser.parse("\n\n")
        docs = wrapper.batch.tree
        assert len(docs) == 0

def test_text_parser_comments():
    with wrap() as wrapper:
        parser = TextFile()
        parser.wrapper = wrapper
        parser.parse("""
        valid.doc { "contents" : "foo" }
        # commented-out.doc
        """)

        docs = wrapper.batch.tree
        assert len(docs) == 1
        assert docs[0].key == "valid.doc"

def test_text_parser_valid_json():
    with wrap() as wrapper:
        parser = TextFile()
        parser.wrapper=wrapper
        parser.parse("""
        doc.txt { "contents" : "123" }
        """)

        docs = wrapper.batch.tree
        assert docs[0].key == "doc.txt"
        assert docs[0].args['contents'] == "123"

def test_text_parser_invalid_json():
    with wrap() as wrapper:
        parser = TextFile()
        parser.wrapper = wrapper

        try:
            parser.parse("""
            doc.txt { "contents" : 123
            """)
            assert False, 'should raise UserFeedback'
        except dexy.exceptions.UserFeedback as e:
            assert 'unable to parse' in e.message

def test_text_parser_virtual_file():
    with wrap() as wrapper:
        parser = TextFile()
        parser.wrapper = wrapper
        parser.parse("""
        virtual.txt { "contents" : "hello" }
        """)

        wrapper.batch.run()
        docs = wrapper.batch.tree

        assert docs[0].key == "virtual.txt"
        assert str(docs[0].children[0].output()) == "hello"

def test_original_parser():
    with wrap() as wrapper:
        conf = """{
        "*.txt" : {}
        }"""

        parser = Original()
        parser.wrapper = wrapper
        parser.parse(conf)

        assert wrapper.batch.tree[0].key_with_class() == "PatternNode:*.txt"

def test_original_parser_allinputs():
    with wrap() as wrapper:
        conf = """{
        "*.txt" : {},
        "hello.txt" : { "contents" : "Hello!" },
        "*.md|jinja" : { "allinputs" : true }
        }"""

        parser = Original(wrapper)
        parser.wrapper = wrapper
        parser.parse(conf)

        assert len(wrapper.batch.tree) == 1
        assert wrapper.batch.tree[0].key_with_class() == "PatternNode:*.md|jinja"

INVALID_YAML = """
code:
    - abc
    def
"""

YAML = """
code:
    - .R|pyg:
         "pyg" : { "foo" : "bar" }
    - .R|idio

wordpress:
    - code
    - test.txt|jinja:
        - contents: 'test'
    - .md|jinja|markdown|wp
"""

YAML_WITH_DEFAULTS = """
defaults:
    pyg: { lexer : moin }
    foo: bar

code:
    - .R|pyg

s1/s2/hello.txt|jinja:
    code
"""

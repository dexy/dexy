from dexy.parser import AbstractSyntaxTree
from dexy.parsers.doc import Original
from dexy.parsers.doc import TextFile
from dexy.parsers.doc import Yaml
from tests.utils import wrap
from dexy.wrapper import Wrapper
import dexy.exceptions
import os

def test_text_parser():
    with wrap() as wrapper:
        with open("f1.py", "w") as f:
            f.write("print 'hello'")

        with open("f2.py", "w") as f:
            f.write("print 'hello'")

        with open("index.md", "w") as f:
            f.write("")

        wrapper = Wrapper()
        wrapper.to_valid()

        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = TextFile(wrapper, ast)
        parser.parse(".", """
        *.py
        *.py|pyg
        *.md|jinja
        """)
        ast.walk()
        assert len(wrapper.nodes) == 8

YAML_WITH_INACTIVE = """
foo:
    - inactive: True
"""

def test_parse_inactive():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', YAML_WITH_INACTIVE)
        ast.walk()
        assert len(wrapper.nodes) == 0

YAML_WITH_DEFAULT_OFF = """
foo:
    - default: False
"""

def test_parse_default():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', YAML_WITH_DEFAULT_OFF)
        ast.walk()
        assert len(wrapper.nodes) == 0

    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        wrapper.full = True
        parser = Yaml(wrapper, ast)
        parser.parse('.', YAML_WITH_DEFAULT_OFF)
        ast.walk()
        assert len(wrapper.nodes) == 1

def test_yaml_with_defaults():
    with wrap() as wrapper:
        os.makedirs("s1/s2")

        with open("s1/s2/hello.txt", "w") as f:
            f.write("hello")

        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', YAML_WITH_DEFAULTS)
        ast.walk()

        assert wrapper.roots[0].args['foo'] == 'bar'
    
def test_invalid_yaml():
    with wrap() as wrapper:
        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        try:
            parser.parse('.', INVALID_YAML)
            assert False, "should raise UserFeedback"
        except dexy.exceptions.UserFeedback as e:
            assert 'YAML' in e.message

def test_yaml_parser():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', YAML)
        for doc in wrapper.roots:
            assert doc.__class__.__name__ == 'BundleNode'
            assert doc.key in ['code', 'wordpress']

        wrapper.run_docs()

def test_text_parser_blank_lines():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = TextFile(wrapper, ast)
        parser.parse('.', "\n\n")
        ast.walk()
        docs = wrapper.roots
        assert len(docs) == 0

def test_text_parser_comments():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = TextFile(wrapper, ast)
        parser.parse('.', """
        valid.doc { "contents" : "foo" }
        # commented-out.doc
        """)
        ast.walk()

        assert len(wrapper.roots) == 1
        assert wrapper.roots[0].key == "valid.doc"

def test_text_parser_valid_json():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = TextFile(wrapper, ast)
        parser.parse('.', """
        doc.txt { "contents" : "123" }
        """)
        ast.walk()

        docs = wrapper.roots
        assert docs[0].key == "doc.txt"
        assert docs[0].args['contents'] == "123"

def test_text_parser_invalid_json():
    with wrap() as wrapper:
        ast = AbstractSyntaxTree(wrapper)
        parser = TextFile(wrapper, ast)
        try:
            parser.parse('.', """
            doc.txt { "contents" : 123
            """)
            assert False, 'should raise UserFeedback'
        except dexy.exceptions.UserFeedback as e:
            assert 'unable to parse' in e.message

def test_text_parser_virtual_file():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = TextFile(wrapper, ast)
        parser.parse('.', """
        virtual.txt { "contents" : "hello" }
        """)
        ast.walk()

        wrapper.transition('walked')
        wrapper.to_checked()

        wrapper.run()
        docs = wrapper.roots

        assert docs[0].key == "virtual.txt"
        assert str(docs[0].output_data()) == "hello"

def test_original_parser():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        conf = """{
        "*.txt" : {}
        }"""
        ast = AbstractSyntaxTree(wrapper)
        parser = Original(wrapper, ast)
        parser.parse('.', conf)
        ast.walk()

        assert wrapper.roots[0].key_with_class() == "pattern:*.txt"

def test_original_parser_allinputs():
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        conf = """{
        "*.txt" : {},
        "hello.txt" : { "contents" : "Hello!" },
        "*.md|jinja" : { "allinputs" : true }
        }"""

        ast = AbstractSyntaxTree(wrapper)
        parser = Original(wrapper, ast)
        parser.parse('.', conf)
        ast.walk()

        assert len(wrapper.roots) == 1
        assert wrapper.roots[0].key_with_class() == "pattern:*.md|jinja"

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

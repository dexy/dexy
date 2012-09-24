from dexy.parser import OriginalDexyParser
from dexy.parser import TextFileParser
from dexy.parser import YamlFileParser
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
        docs = wrapper.docs
        for doc in docs:
            assert doc.__class__.__name__ == 'BundleDoc'
            assert doc.key in ['code', 'wordpress']

def test_text_parser_blank_lines():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper = wrapper
        parser.parse("\n\n")
        docs = wrapper.docs
        assert len(docs) == 0

def test_text_parser_comments():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper = wrapper
        parser.parse("""
        valid.doc
        # commented-out.doc
        """)

        docs = wrapper.docs
        assert len(docs) == 1
        assert docs[0].key == "valid.doc"

def test_text_parser_valid_json():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper=wrapper
        parser.parse("""
        doc.txt { "contents" : 123 }
        """)

        docs = wrapper.docs
        assert docs[0].key == "doc.txt"
        assert docs[0].args['contents'] == 123

def test_text_parser_invalid_json():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper = wrapper
        parser.parse("""
        doc.txt { "contents" : 123
        """)
        docs = wrapper.docs
        assert docs[0].key == "doc.txt"
        assert not "contents" in docs[0].args

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
        *.py|idio
        *.md|jinja
        """)

        docs = [task for task in wrapper.registered if task.__class__.__name__ == 'Doc']

        assert len(docs) == 5

        assert docs[0] in docs[1].children

        assert docs[0] in docs[2].children
        assert docs[1] in docs[2].children

        assert docs[0] in docs[3].children
        assert docs[1] in docs[3].children
        assert docs[2] in docs[3].children

        assert docs[0] in docs[4].children
        assert docs[1] in docs[4].children
        assert docs[2] in docs[4].children
        assert docs[3] in docs[4].children

        assert docs[4].key == "index.md|jinja"

def test_text_parser_virtual_file():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper = wrapper
        parser.parse("""
        virtual.txt { "contents" : "hello" }
        """)

        wrapper.run()
        docs = wrapper.docs

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

        assert wrapper.docs[0].key_with_class() == "PatternDoc:*.txt"

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

        assert wrapper.docs[0].key_with_class() == "PatternDoc:*.txt"
        assert wrapper.docs[1].key_with_class() == "Doc:hello.txt"
        assert wrapper.docs[2].key_with_class() == "PatternDoc:*.md|jinja"

INVALID_YAML = """\
code:
    - abc
    def
"""

YAML = """\
code:
    - "*.R|pyg":
         "pyg" : { "foo" : "bar" }
    - "*.R|idio"

wordpress:
    - code
    - test.txt|jinja
    - \*.md|jinja|markdown|wp
"""

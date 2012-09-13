from dexy.parser import OriginalDexyParser
from dexy.parser import TextFileParser
from dexy.tests.utils import wrap

def test_text_parser_blank_lines():
    with wrap() as wrapper:
        parser = TextFileParser()
        parser.wrapper = wrapper
        docs = parser.parse("\n\n")
        assert len(docs) == 0

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

def test_original_parser():
    conf = """{
    "*.txt" : {}
    }"""

    parser = OriginalDexyParser()
    result = parser.parse(conf)
    print result

def test_original_parser_allinputs():
    conf = """{
    "*.txt" : {},
    "*.md|jinja" : { "allinputs" : true }
    }"""

    parser = OriginalDexyParser()
    result = parser.parse(conf)
    print result

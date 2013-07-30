from dexy.doc import Doc
from dexy.tests.utils import wrap
from dexy.exceptions import UserFeedback
from dexy.tests.utils import TEST_DATA_DIR
import os
from dexy.filters.id import parser as id_parser
from dexy.filters.id import lexer as id_lexer
from dexy.filters.id import start_new_section, token_info

def test_force_text():
    with wrap() as wrapper:
        node = Doc("example.py|idio|t",
                wrapper,
                [],
                contents="print 'hello'\n")

        wrapper.run_docs(node)
        assert str(node.output_data()) == "print 'hello'\n"

def setup_parser():
    with wrap() as wrapper:
        id_parser.outputdir = wrapper.log_dir
        id_parser.errorlog = wrapper.log
        id_lexer.outputdir = wrapper.log_dir
        id_lexer.errorlog = wrapper.log
        id_lexer.remove_leading = True
        id_parser.write_tables = False
        _lexer = id_lexer.clone()
        _lexer.sections = []
        _lexer.level = 0
        start_new_section(_lexer, 0, 0, _lexer.level)
        yield(id_parser, _lexer)

def parse(text):
    for id_parser, _lexer in setup_parser():
        id_parser.parse(text, lexer=_lexer)
        return _lexer.sections

def tokens(text):
    for id_parser, _lexer in setup_parser():
        return token_info(text, _lexer)

def test_parse_code():
    output = parse("foo\n")
    assert output[0]['contents'] == 'foo\n'

def test_parse_oldstyle_comments():
    for comment in ('###', '///', '%%%'):
        text = "%s @export foo\nfoo\n" % comment
        output = parse(text)
        assert output[0]['name'] == 'foo'
        assert output[0]['contents'] == 'foo\n'

def test_parse_comments():
    for comment in ('###', '///', '%%%'):
        text = "%s 'foo-bar'\nfoo\n" % comment
        output = parse(text)
        assert output[0]['name'] == 'foo-bar'
        assert output[0]['contents'] == 'foo\n'

def test_parse_closed_style_sections():
    comments = (
        "/*** @export foo*/\n",
        "/*** @export foo */\n",
        "/*** @section foo */\n",
        "/*** @export 'foo'*/\n",
        "/*** @export 'foo' */\n",
        "/*** @export 'foo' python*/\n",
        "/*** @export 'foo' python */\n",
        """/*** @export "foo" python*/\n""",
        "<!-- @export foo -->\n",
        "<!-- @section foo -->\n"
        "<!-- section foo -->\n"
        "<!-- section 'foo' -->\n"
        )

    for text in comments:
        output = parse(text)
        assert output[0]['contents'] == ''
        assert output[0]['name'] == 'foo'

def test_parse_closed_style_end():
    comments = (
        "foo\n/*** @end */\nbar\n",
        "foo\n<!-- @end -->\nbar\n",
        "foo\n<!-- section 'end' -->\nbar\n"
        )
    for text in comments:
        output = parse(text)
        assert output[0]['contents'] == 'foo\n'
        assert output[1]['contents'] == 'bar\n'
        assert output[0]['name'] == '1'
        assert output[1]['name'] == '2'

def test_parse_closed_falsestart():
    comments = (
        "<!-- @bob -->\n",
        "/*** @bob */\n"
        )

    for text in comments:
        output = parse(text)
        assert output[0]['contents'] == text

def test_ignore_faux_comment():
    for comment in ('#', '/', '%', '##%', '//#', '%#%', '##', '//', '%%', '///'):
        text = "  %s foo bar\nfoo\n" % comment
        output = parse(text)
        assert output[0]['contents'] == text

def test_accidental_comment_in_string():
    for comment in ('###",', '%%%",', '"###",', '"%%%"', '"### (%%%)",'):
        text = "foo bar %s\n" % comment
        output = parse(text)
        assert output[0]['contents'] == text

def test_malformatted_comment_throws_error():
    for comment in ('###', '///', '%%%'):
        text = "%s 'foo bar'\nfoo\n" % comment
        try:
            parse(text)
            assert False, "Should not get here."
        except UserFeedback:
            pass

def test_idio_invalid_input():
    with wrap() as wrapper:
        wrapper.debug = False
        doc = Doc("hello.py|idio",
                wrapper, [],
                contents="### @ ")
        wrapper.run_docs(doc)
        assert wrapper.state == 'error'

def test_multiple_sections():
    with wrap() as wrapper:
        src = """
### @export "vars"
x = 6
y = 7

### @export "multiply"
x*y

"""
        doc = Doc("example.py|idio",
                wrapper,
                [],
                contents=src)

        wrapper.run_docs(doc)
        assert doc.output_data().keys() == ['1', 'vars', 'multiply']

def test_force_latex():
    with wrap() as wrapper:
        doc = Doc("example.py|idio|l",
                wrapper,
                [],
                contents="print 'hello'\n")

        wrapper.run_docs(doc)

        assert "begin{Verbatim}" in str(doc.output_data())

def test_parse_docutils_latex():
    with open(os.path.join(TEST_DATA_DIR, "doc.tex"), "r") as f:
        latex = f.read()
    parse(latex)

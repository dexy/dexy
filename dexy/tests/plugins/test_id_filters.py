from dexy.doc import Doc
from dexy.tests.utils import wrap
from dexy.filters.id import IdParser
from dexy.exceptions import UserFeedback

def id_parser(wrapper):
    settings = {
            'ply-debug' : False,
            'ply-outputdir' : wrapper.log_dir,
            'ply-optimize' : True,
            'ply-lextab' : 'id_lextab',
            'ply-parsetab' : 'id_parsetab',
            'ply-write-tables' : False,
            'remove-leading' : True
            }
    return IdParser(settings, wrapper.log)

def parse(text):
    with wrap() as wrapper:
        parser = id_parser(wrapper)
        return parser.parse(text)

def token_info(text):
    with wrap() as wrapper:
        parser = id_parser(wrapper)
        return parser.token_info(text)

def test_no_trailing_newline():
    output = parse("}")
    assert output['1']['contents'] == '}'

def test_parse_code():
    output = parse("foo\n")
    assert output['1']['contents'] == 'foo\n'

def test_parse_oldstyle_comments():
    for comment in ('###', '///', '%%%'):
        text = "%s @export foo\nfoo\n" % comment
        output = parse(text)
        assert output['foo']['contents'] == 'foo\n'

def test_parse_comments():
    for comment in ('###', '///', '%%%'):
        text = "%s foo-bar\nfoo\n" % comment
        output = parse(text)
        assert output['foo-bar']['contents'] == 'foo\n'

def test_parse_closed_style_sections():
    comments = (
        "/*** @export foo */\n",
        "/*** @section foo */\n",
        "<!-- @export foo -->\n",
        "<!-- @section foo -->\n"
        )

    for text in comments:
        output = parse(text)
        assert output['foo']['contents'] == ''

def test_parse_closed_style_end():
    comments = (
        "foo\n/*** @end */\nbar\n",
        "foo\n<!-- @end -->\nbar\n"
        )
    for text in comments:
        output = parse(text)
        assert output['1']['contents'] == 'foo\n'
        assert output['2']['contents'] == 'bar\n'

def test_parse_closed_falsestart():
    comments = (
        "<!-- @bob -->\n",
        "/*** @bob */\n"
        )

    for text in comments:
        output = parse(text)
        assert output['1']['contents'] == text

def test_ignore_faux_comment():
    for comment in ('#', '/', '%', '##%', '//#', '%#%', '##', '//', '%%'):
        text = "%s foo bar\nfoo\n" % comment
        output = parse(text)
        assert output['1']['contents'] == text

def test_malformatted_comment_throws_error():
    for comment in ('###', '///', '%%%'):
        text = "%s foo bar\nfoo\n" % comment
        try:
            parse(text)
            assert False, "Should not get here."
        except UserFeedback as e:
            print e

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

        print doc.output_data().keys()
        assert doc.output_data().keys() == ['1', 'vars', 'multiply']

def test_force_text():
    with wrap() as wrapper:
        node = Doc("example.py|idio|t",
                wrapper,
                [],
                contents="print 'hello'\n")

        wrapper.run_docs(node)
        assert str(node.output_data()) == "print 'hello'\n"

def test_force_latex():
    with wrap() as wrapper:
        doc = Doc("example.py|idio|l",
                wrapper,
                [],
                contents="print 'hello'\n")

        wrapper.run_docs(doc)

        assert "begin{Verbatim}" in str(doc.output_data())

from dexy.doc import Doc
from dexy.tests.utils import wrap
from dexy.filters.id_filter import IdParser
from dexy.exceptions import UserFeedback

def id_parser(wrapper):
    settings = {
            'ply-debug' : False,
            'ply-write-tables' : False,
            'remove-leading' : True
            }
    return IdParser(settings, wrapper.log)

def parse(text):
    with wrap() as wrapper:
        parser = id_parser(wrapper)
        return parser.parse(text)

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

def test_ignore_faux_comment():
    for comment in ('3', '/', '%', '##%', '//#', '%#%', '##', '//', '%%'):
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

def test_idio_bad_file_extension():
    with wrap() as wrapper:
        wrapper.debug = False
        doc = Doc("hello.xyz|idio", wrapper, [], contents=" ")
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

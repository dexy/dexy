from dexy.tests.utils import wrap
from dexy.doc import Doc
from dexy.common import OrderedDict

def test_regetron_filter():
    with wrap() as wrapper:
        doc = Doc("example.regex|regetron",
                    Doc("input1.txt",
                        contents="hello",
                        wrapper=wrapper),
                    Doc("input2.txt",
                        contents="""\
this is some text
9
nine
this is 100 mixed text and numbers
""",
                        wrapper=wrapper),
                contents="^[a-z\s]+$",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output()['input1.txt'] == """\
> ^[a-z\s]+$
0000: hello > 

"""
        assert doc.output()['input2.txt'] == """\
> ^[a-z\s]+$
0000: this is some text
0002: nine
> 

"""

def test_used_filter():
    with wrap() as wrapper:
        doc = Doc("input.txt|used",
                Doc("example.sed",
                    contents="s/e/E/g",
                    wrapper=wrapper),
                contents="hello",
                wrapper=wrapper)

        wrapper.run_docs(doc)
        assert str(doc.output()) == "hEllo"

def test_sed_filter_single_simple_input_file():
    with wrap() as wrapper:
        doc = Doc("example.sed|sed",
                Doc("input.txt",
                    contents="hello",
                    wrapper=wrapper),
                contents="s/e/E/g",
                wrapper=wrapper)

        wrapper.run_docs(doc)
        assert str(doc.output()) == "hEllo"

def test_sed_filter_single_input_file_with_sections():
    with wrap() as wrapper:
        doc = Doc("example.sed|sed",
                Doc("input.txt",
                    contents=OrderedDict([
                        ('foo', 'hello'),
                        ('bar', 'telephone')
                        ]),
                    wrapper=wrapper),
                contents="s/e/E/g",
                wrapper=wrapper)

        wrapper.run_docs(doc)
        assert doc.output()['foo'] == 'hEllo'
        assert doc.output()['bar'] == 'tElEphonE'

def test_sed_filter_multiple_inputs():
    with wrap() as wrapper:
        doc = Doc("example.sed|sed",
                Doc("foo.txt",
                    contents='hello',
                    wrapper=wrapper),
                Doc("bar.txt",
                    contents='telephone',
                    wrapper=wrapper),
                contents="s/e/E/g",
                wrapper=wrapper)

        wrapper.run_docs(doc)
        assert doc.output()['foo.txt'] == 'hEllo'
        assert doc.output()['bar.txt'] == 'tElEphonE'

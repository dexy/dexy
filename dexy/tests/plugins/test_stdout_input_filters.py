from dexy.common import OrderedDict
from dexy.node import DocNode
from dexy.tests.utils import wrap

REGETRON_INPUT_1 = "hello\n"
REGETRON_INPUT_2 = """\
this is some text
9
nine
this is 100 mixed text and numbers
"""

def test_regetron_filter():
    with wrap() as wrapper:
        node = DocNode("example.regex|regetron",
                inputs = [
                    DocNode("input1.txt",
                        contents=REGETRON_INPUT_1,
                        wrapper=wrapper),
                    DocNode("input2.txt",
                        contents=REGETRON_INPUT_2,
                        wrapper=wrapper)
                    ],
                contents="^[a-z\s]+$",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]

        assert doc.output()['input1.txt'] == """\
> ^[a-z\s]+$
0000: hello
> 

"""
        assert doc.output()['input2.txt'] == """\
> ^[a-z\s]+$
0000: this is some text
0002: nine
> 

"""

def test_used_filter():
    with wrap() as wrapper:
        node = DocNode("input.txt|used",
                inputs = [
                    DocNode("example.sed",
                        contents="s/e/E/g",
                        wrapper=wrapper)
                    ],
                contents="hello",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert str(doc.output()) == "hEllo"

def test_sed_filter_single_simple_input_file():
    with wrap() as wrapper:
        node = DocNode("example.sed|sed",
                inputs = [
                    DocNode("input.txt",
                        contents="hello",
                        wrapper=wrapper)
                    ],
                contents="s/e/E/g",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert str(doc.output()) == "hEllo"

def test_sed_filter_single_input_file_with_sections():
    with wrap() as wrapper:
        node = DocNode("example.sed|sed",
                contents="s/e/E/g",
                inputs = [
                    DocNode("input.txt",
                        contents=OrderedDict([
                            ('foo', 'hello'),
                            ('bar', 'telephone')
                            ]),
                        wrapper=wrapper)
                        ],
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output()['foo'] == 'hEllo'
        assert doc.output()['bar'] == 'tElEphonE'

def test_sed_filter_multiple_inputs():
    with wrap() as wrapper:
        node = DocNode("example.sed|sed",
                contents="s/e/E/g",
                inputs = [
                    DocNode("foo.txt",
                        contents='hello',
                        wrapper=wrapper),
                    DocNode("bar.txt",
                        contents='telephone',
                        wrapper=wrapper)
                    ],
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output()['foo.txt'] == 'hEllo'
        assert doc.output()['bar.txt'] == 'tElEphonE'

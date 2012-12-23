from dexy.tests.utils import assert_output
from dexy.tests.utils import wrap
from dexy.node import DocNode
import dexy.exceptions

CPP_HELLO_WORLD = """#include <iostream>
using namespace std;

int main()
{
	cout << "Hello, world!";

	return 0;

}
"""

C_HELLO_WORLD = """#include <stdio.h>

int main()
{
    printf("HELLO, world\\n");
}
"""

C_FUSSY_HELLO_WORLD = """#include <stdio.h>

int main()
{
    printf("HELLO, world\\n");
    return 0;
}
"""

C_WITH_INPUT = """#include <stdio.h>

int main()
{
    int c;

    c = getchar();
    while (c != EOF) {
        putchar(c);
        c = getchar();
    }
}
"""

def test_cpp_filter():
    assert_output('cpp', CPP_HELLO_WORLD, "Hello, world!", ext=".cpp")

def test_clang_filter():
    assert_output('clang', C_HELLO_WORLD, "HELLO, world\n", ext=".c")

def test_c_filter():
    assert_output('gcc', C_HELLO_WORLD, "HELLO, world\n", ext=".c")
    assert_output('gcc', C_FUSSY_HELLO_WORLD, "HELLO, world\n", ext=".c")

def test_cfussy_filter():
    assert_output('cfussy', C_FUSSY_HELLO_WORLD, "HELLO, world\n", ext=".c")
    try:
        with wrap() as wrapper:
            doc = DocNode("hello.c|cfussy",
                    contents=C_HELLO_WORLD,
                    wrapper=wrapper)
            wrapper.run_docs(doc)
        assert False, 'should raise error'
    except dexy.exceptions.UserFeedback:
        assert True

def test_c_input():
    with wrap() as wrapper:
        node = DocNode("copy.c|cinput",
                inputs = [
                DocNode("input.txt",
                    contents = "hello, c",
                    wrapper=wrapper)
                ],
                contents = C_WITH_INPUT,
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert str(doc.output()) == "hello, c"

def test_clang_input():
    with wrap() as wrapper:
        node = DocNode("copy.c|clanginput",
                inputs = [
                DocNode("input.txt",
                    contents = "hello, c",
                    wrapper=wrapper)
                ],
                contents = C_WITH_INPUT,
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert str(doc.output()) == "hello, c"

def test_clang_multiple_inputs():
    with wrap() as wrapper:
        node = DocNode("copy.c|clanginput",
                inputs = [
                    DocNode("input1.txt",
                        contents = "hello, c",
                        wrapper=wrapper),
                    DocNode("input2.txt",
                        contents = "more data",
                        wrapper=wrapper)
                ],
                contents = C_WITH_INPUT,
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().data()['input1.txt'] == 'hello, c'
        assert doc.output().data()['input2.txt'] == 'more data'

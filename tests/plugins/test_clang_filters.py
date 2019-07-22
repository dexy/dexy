from dexy.doc import Doc
from nose import SkipTest
from tests.utils import assert_output
from tests.utils import wrap

FORTRAN_HELLO_WORLD = """program hello
   print *, "Hello World!"
end program hello
"""

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
def test_fortran_filter():
    assert_output('fortran', FORTRAN_HELLO_WORLD, "Hello, world!", ext=".f")

def test_cpp_filter():
    assert_output('cpp', CPP_HELLO_WORLD, "Hello, world!", ext=".cpp")

def test_clang_filter():
    assert_output('clang', C_HELLO_WORLD, "HELLO, world\n", ext=".c")

def test_c_filter():
    assert_output('gcc', C_HELLO_WORLD, "HELLO, world\n", ext=".c")
    assert_output('gcc', C_FUSSY_HELLO_WORLD, "HELLO, world\n", ext=".c")

def test_cfussy_filter():
    raise SkipTest()
    assert_output('cfussy', C_FUSSY_HELLO_WORLD, "HELLO, world\n", ext=".c")
    with wrap() as wrapper:
        wrapper.debug = False
        doc = Doc("hello.c|cfussy",
                contents=C_HELLO_WORLD,
                wrapper=wrapper)
        wrapper.run_docs(doc)
        assert wrapper.state == 'error'

def test_c_input():
    with wrap() as wrapper:
        node = Doc("copy.c|cinput",
                inputs = [
                Doc("input.txt",
                    contents = "hello, c",
                    wrapper=wrapper)
                ],
                contents = C_WITH_INPUT,
                wrapper=wrapper)

        wrapper.run_docs(node)
        assert str(node.output_data()) == "hello, c"

def test_clang_input():
    with wrap() as wrapper:
        node = Doc("copy.c|clanginput",
                inputs = [
                Doc("input.txt",
                    contents = "hello, c",
                    wrapper=wrapper)
                ],
                contents = C_WITH_INPUT,
                wrapper=wrapper)

        wrapper.run_docs(node)
        assert str(node.output_data()) == "hello, c"

def test_clang_multiple_inputs():
    with wrap() as wrapper:
        node = Doc("copy.c|clanginput",
                inputs = [
                    Doc("input1.txt",
                        contents = "hello, c",
                        wrapper=wrapper),
                    Doc("input2.txt",
                        contents = "more data",
                        wrapper=wrapper)
                ],
                contents = C_WITH_INPUT,
                wrapper=wrapper)

        wrapper.run_docs(node)
        assert str(node.output_data()['input1.txt']) == 'hello, c'
        assert str(node.output_data()['input2.txt']) == 'more data'

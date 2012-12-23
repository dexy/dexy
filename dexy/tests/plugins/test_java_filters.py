from dexy.node import DocNode
from dexy.tests.utils import assert_in_output
from dexy.tests.utils import assert_output
from dexy.tests.utils import wrap

JAVA_SRC = """public class hello {
  public static void main(String args[]) {
    System.out.println("Java Hello World!");
  }
}"""

def test_javac_filter():
    # not using runfilter() because file has to be named 'hello.java'
    with wrap() as wrapper:
        doc = DocNode("hello.java|javac",
                contents=JAVA_SRC,
                wrapper=wrapper)
        wrapper.run_docs(doc)
        assert doc.children[0].output().is_cached()

def test_java_filter():
    # not using runfilter() because file has to be named 'hello.java'
    with wrap() as wrapper:
        doc = DocNode("hello.java|java",
                contents=JAVA_SRC,
                wrapper=wrapper)
        wrapper.run_docs(doc)
        assert doc.children[0].output().data() == "Java Hello World!\n"

def test_jruby_filter():
    assert_output('jruby', "puts 1+1", "2\n")

def test_jirb_filter():
    assert_in_output('jirb', "puts 1+1",  ">> puts 1+1")

def test_jython_filter():
    assert_output('jython', "print 1+1", "2\n")

def test_jythoni_filter():
    assert_in_output('jythoni', "print 1+1",  ">>> print 1+1")

from dexy.doc import Doc
from tests.utils import assert_in_output
from tests.utils import assert_output
from tests.utils import wrap
from nose.exc import SkipTest

JAVA_SRC = """public class hello {
  public static void main(String args[]) {
    System.out.println("Java Hello World!");
  }
}"""

def test_javac_filter():
    # not using runfilter() because file has to be named 'hello.java'
    with wrap() as wrapper:
        doc = Doc("hello.java|javac",
                wrapper,
                [],
                contents=JAVA_SRC)
        wrapper.run_docs(doc)
        assert doc.output_data().is_cached()

def test_java_filter():
    # not using runfilter() because file has to be named 'hello.java'
    with wrap() as wrapper:
        doc = Doc("hello.java|java",
                wrapper,
                [],
                contents=JAVA_SRC)
        wrapper.run_docs(doc)
        assert str(doc.output_data()) == "Java Hello World!\n"

def test_jruby_filter():
    assert_output('jruby', "puts 1+1", "2\n")

def test_jirb_filter():
    assert_in_output('jirb', "puts 1+1",  ">> puts 1+1")

def test_jython_filter():
    assert_output('jython', "print 1+1", "2\n")

def test_jythoni_filter():
    raise SkipTest()
    assert_in_output('jythoni', "print 1+1",  ">>> print 1+1")

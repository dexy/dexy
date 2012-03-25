from dexy.tests.utils import run_dexy
from dexy.tests.utils import assert_output
from dexy.tests.utils import assert_in_output
from dexy.tests.utils import assert_matches_output

def test_sh_filter():
    assert_output("example.sh|sh", "ls", "example.sh\n")

def test_man_filter():
    assert_in_output("progs.txt|man", "bash", "bash - GNU Bourne-Again SHell")

def test_cowsay_filter():
    assert_in_output("moo.txt|cowsay", "moo", "< moo >")

def test_cowthink():
    assert_in_output("moo.txt|cowthink", "moo", "( moo )")

def test_python():
    assert_output("ex.py|py", "print 1+1", "2\n")

def test_irbout():
    assert_output("ex.rb|irbout", "1+1", ">> 1+1>> >> => 2\n>> ")

def test_rb():
    assert_output("ex.rb|rb", "puts 1+1", "2\n")

def test_lynxdump():
    assert_matches_output("input.html|lynxdump", "<p>Hello</p>", "\s*Hello\s*")

def test_ragel_ruby():
    machine = """
    %%{
      machine hello;
      expr = "h";
      main := expr @ { puts "hello world!" } ;
    }%%
    """
    assert_in_output("input.rl|rlrbd", machine, "digraph hello")

def test_sloccount():
    assert_in_output("code.py|sloccount", "print 'hello'", "python=1")

def test_lua():
    assert_output("code.lua|lua", """io.write("Hello world")""", "Hello world")

def test_php():
    assert_output("hello.php|php", "<?php echo('hello, world'); ?>", "hello, world")

def test_escript():
    assert_matches_output("hello.erl|escript", """\nmain(_) -> io:fwrite("Hello, world!\n").\n""", "\s*Hello, world!\s*")

def test_redcloth():
    assert_output("hello.txt|redcloth", "h1. hello", "<h1>hello</h1>\n")

def test_redclothl():
    assert_output("hello.txt|redclothl", "h1. hello", "\\section{hello}\n\n")

def test_rst2html():
    assert_in_output("text.rst|rst2html", "* hello", "<li>hello</li>")

def test_rst2latex():
    assert_in_output("text.rst|rst2latex", "* hello", "\\item hello")

def test_wiki2beamer():
    assert_in_output("text.wiki|wiki2beamer", "* hello", "\\item hello")

def test_rdconv_filter():
    assert_in_output("abc.Rd|rdconv", "\\title{abc}\n\\name{abc}", "\HeaderA{abc}{abc}{abc}",  { "rdconv" : {"ext" : ".tex"}})

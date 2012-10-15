from dexy.tests.utils import assert_in_output
from dexy.tests.utils import assert_output
from dexy.tests.utils import assert_output_matches
import inspect
import os

def test_rd_stdout_filter():
    rd = """
     \\name{load}
     \\alias{load}
     \\title{Reload Saved Datasets}
     \description{
       Reload the datasets written to a file with the function
       \code{save}.
     }
    """
    expected = u'Reload the datasets written to a file with the function \u2018save\u2019.'
    assert_in_output('rdconv', rd, expected, ext=".Rd")

def test_redcloth_stdout_filter():
    expected = "<p>hello <strong>bold</strong></p>" + os.linesep
    assert_output("redcloth", "hello *bold*", expected)

def test_redcloth_stdout_latex_filter():
    expected = "hello \\textbf{bold}" + os.linesep + os.linesep
    assert_output("redclothl", "hello *bold*", expected)

def test_lynx_dump_stdout_filter():
    html = "<p>hello</p>"
    assert_output_matches('lynxdump', html, "\s*hello\s*", ext=".html")

def test_strings_stdout_filter():
    assert_output('strings', "hello\bmore", "hello\nmore\n")

def test_php_stdout_filter():
    php = inspect.cleandoc("""<?php
    echo(1+1);
    ?>""")
    assert_output('php', php, "2")

def test_ragel_ruby_dot_filter():
    ragel = inspect.cleandoc("""
        %%{
          machine hello_and_welcome;
          main := ( 'h' @ { puts "hello world!" }
                  | 'w' @ { puts "welcome" }
                  )*;
        }%%
          data = 'whwwwwhw'
          %% write data;
          %% write init;
          %% write exec;
        """)
    assert_in_output('ragelrubydot', ragel, "digraph hello_and_welcome", ext=".rl")

def test_python_stdout_filter():
    assert_output('py', 'print 1+1', "2" + os.linesep)

def test_bash_stdout_filter():
    assert_output('bash', 'echo "hello"', "hello\n")

def test_rhino_stdout_filter():
    assert_output('rhino', "print(6*7)", "42\n")

def test_cowsay_stdout_filter():
    assert_in_output('cowsay', 'hello', 'hello')

def test_cowthink_stdout_filter():
    assert_in_output('cowthink', 'hello', 'hello')

def test_figlet_stdout_filter():
    assert_in_output('figlet', 'hello', "| |__   ___| | | ___  ")

def test_man_page_stdout_filter():
    assert_in_output('man', 'ls', 'list directory contents')

def test_ruby_subprocess_stdout_filter():
    assert_output('rb', 'puts "hello"', "hello\n")

def test_sloccount_subprocess_stdout_filter():
    assert_in_output('sloccount', 'puts "hello"', "ruby=1", ext=".rb")

def test_irb_subprocess_stdout_filter():
    assert_in_output('irbout', 'puts "hello"', '> puts "hello"')

def test_lua_subprocess_stdout_filter():
    assert_output('lua', 'print ("Hello")', "Hello\n")

def test_wiki2beamer_stdout_filter():
    wiki = inspect.cleandoc("""==== A simple frame ====
    * with a funky
    * bullet list
    *# and two
    *# numbered sub-items
    """)

    assert_in_output('wiki2beamer', wiki, "\\begin{frame}")
    assert_in_output('wiki2beamer', wiki, "\\begin{enumerate}")

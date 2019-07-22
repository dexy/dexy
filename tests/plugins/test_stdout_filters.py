from tests.utils import assert_in_output
from tests.utils import assert_output
from tests.utils import assert_output_matches
import inspect
import os

def test_node():
    assert_output("nodejs", "console.log('hello');", "hello\n")

def test_rd():
    rd = """
     \\name{load}
     \\alias{load}
     \\title{Reload Saved Datasets}
     \description{
       Reload the datasets written to a file with the function
       \code{save}.
     }
    """
    expected = "Reload the datasets written to a file with the function \u2018save\u2019."
    assert_in_output('rdconv', rd, expected, ext=".Rd")

def test_redcloth():
    expected = "<p>hello <strong>bold</strong></p>" + os.linesep
    assert_output("redcloth", "hello *bold*", expected)

def test_redclothl():
    expected = "hello \\textbf{bold}" + os.linesep + os.linesep
    assert_output("redclothl", "hello *bold*", expected)

def test_lynxdump():
    assert_output_matches('lynxdump', "<p>hello</p>", "\s*hello\s*", ext=".html")

def test_strings():
    assert_output('strings', "hello\bmore", "hello\nmore\n")

def test_php():
    php = inspect.cleandoc("""<?php
    echo(1+1);
    ?>""")
    assert_output('php', php, "2")

def test_ragel_ruby_dot():
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

def test_python():
    assert_output('py', 'print(1+1)', "2" + os.linesep)

def test_bash():
    assert_output('bash', 'echo "hello"', "hello\n")

def test_rhino():
    assert_output('rhino', "print(6*7)", "42\n")

def test_cowsay():
    assert_in_output('cowsay', 'hello', 'hello')

def test_cowthink():
    assert_in_output('cowthink', 'hello', 'hello')

def test_figlet():
    assert_in_output('figlet', 'hello', "| |__   ___| | | ___  ")

def test_man_page():
    assert_in_output('man', 'ls', 'list directory contents')

def test_ruby():
    assert_output('rb', 'puts "hello"', "hello\n")

def test_sloccount():
    assert_in_output('sloccount', 'puts "hello"', "ruby=1", ext=".rb")

def test_irb_subprocess_stdout_filter():
    assert_in_output('irbout', 'puts "hello"', '> puts "hello"')

def test_lua():
    assert_output('lua', 'print ("Hello")', "Hello\n")

def test_wiki2beamer():
    wiki = inspect.cleandoc("""==== A simple frame ====
    * with a funky
    * bullet list
    *# and two
    *# numbered sub-items
    """)

    assert_in_output('wiki2beamer', wiki, "\\begin{frame}")
    assert_in_output('wiki2beamer', wiki, "\\begin{enumerate}")

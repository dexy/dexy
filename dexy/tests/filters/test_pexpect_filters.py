from dexy.tests.utils import run_dexy
from dexy.tests.utils import assert_output
from dexy.tests.utils import assert_in_output
from dexy.tests.utils import assert_matches_output

def test_irb():
    assert_output("example.rb|irb", "1+1", ">> 1+1\n=> 2")

def test_python():
    assert_in_output("example.py|pycon", "1+1", ">>> 1+1\n2")

def test_ipython():
    assert_in_output("example.py|ipython", "1+1", ">>> 1+1\n2")

def test_r():
    assert_in_output("example.R|r", "1+1", "> 1+1\n[1] 2")

def test_rhino():
    assert_in_output("example.js|rhinoint", "1+1", "js> 1+1\n2")

def test_php():
    assert_in_output("example.php|phpint", "echo(1+1);", "php > echo(1+1);\n2")

def test_bash():
    assert_in_output("script.sh|shint", "pwd", "/artifacts/")
    assert_in_output("script.sh|shint", "pwd", "/artifacts/", { "shint" : { "args" : "-e" }})

def test_ksh():
    assert_in_output("script.sh|kshint", "pwd", "/artifacts/")
    assert_in_output("script.sh|kshint", "pwd", "/artifacts/", { "kshint" : { "args" : "-e" }})
    assert_in_output("script.sh|kshint", "pwd", "1$ pwd", { "kshint" : { "PS1" : "!$ ", "env" : { "HISTFILE" : "fake/histfile"} }})

def test_clojure():
    clojure = """(defn factorial
 ([n]
  (factorial n 1))
 ([n acc]
  (if  (= n 0)   acc
   (recur (dec n) (* acc n)))))
(factorial 10)"""
    assert_in_output("example.clj|clj", clojure, "3628800")

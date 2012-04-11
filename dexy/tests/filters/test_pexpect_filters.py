from dexy.tests.utils import run_dexy
from dexy.tests.utils import assert_output
from dexy.tests.utils import assert_in_output
from dexy.tests.utils import assert_matches_output

def test_irb():
    assert_output("example.rb|irb", "1+1", ">> 1+1\n=> 2")

    config = {"." : { "@example.rb|irb" : {"irb": {"ext" : ".json", "meta" : True}, "contents" : "1+1"}}}
    for doc in run_dexy(config):
        doc.run()

        artifact = doc.last_artifact
        assert artifact.output() == ">> 1+1\n=> 2"

        kv_artifact = artifact.inputs().values()[0]
        kv_artifact.setup_kv_storage()
        assert kv_artifact['1:files:example.rb'] == "1+1"
        assert kv_artifact['1:html-output']
        assert kv_artifact['1:latex-output']
        assert kv_artifact['1:output'] == ">> 1+1\n=> 2"

def test_python():
    assert_in_output("example.py|pycon", "1+1", ">>> 1+1\n2")

def test_python_create_files():
    contents = """with open("new-file.txt", "w") as f:\n    f.write("hello!")\n"""
    config = {"." : { "@example.py|pycon" : {"pycon": {"ext" : ".json", "meta" : True}, "contents" : contents }}}
    for doc in run_dexy(config):
        doc.run()
        artifact = doc.last_artifact

        kv_artifact = artifact.inputs().values()[0]
        kv_artifact.setup_kv_storage()
        assert kv_artifact['1:files:new-file.txt'] == "hello!"

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

def test_bash_create_additional_files():
    contents = """
    mkdir abc
    ls
    echo "hi" > abc/hello.txt
    """
    config = {"." : { "@script.sh|shint" : {"shint": {"meta" : True}, "contents" : contents }}}
    for doc in run_dexy(config):
        doc.run()
        artifact = doc.last_artifact

        kv_artifact = artifact.inputs().values()[0]
        kv_artifact.setup_kv_storage()
        assert kv_artifact['1:files:abc/hello.txt'] == "hi\n"

def test_bash_create_git_repo():
    contents = """
    mkdir abc
    ls
    echo "hi" > abc/hello.txt
    git init
    git add .
    """
    config = {"." : { "@script.sh|shint" : {"shint": {"ext" : ".json", "meta" : True}, "contents" : contents }}}
    for doc in run_dexy(config):
        doc.run()
        artifact = doc.last_artifact

        kv_artifact = artifact.inputs().values()[0]
        kv_artifact.setup_kv_storage()
        assert "[core]" in kv_artifact["1:files:.git/config"]

def test_bash_create_additional_artifacts():
    contents = """
    ls
    echo "hi" > dexy--hello.txt
    """
    config = {"." : { "@script.sh|fn|shint" : {"shint": {"ext" : ".json", "meta" : True}, "contents" : contents }}}
    for doc in run_dexy(config):
        doc.run()
        artifact = doc.last_artifact
        assert artifact.inputs()['hello.txt'].output_text() == "hi\n"

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

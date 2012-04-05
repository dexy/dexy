from dexy.controller import Controller
from dexy.tests.utils import controller_args
from dexy.tests.utils import run_dexy_without_tempdir
from dexy.tests.utils import tempdir
import json
import os

def test_config_multiple_directories():
    config = {
        "." : { "*.txt" : {} },
        "abc" : { "*.txt" : {} }
    }

    with tempdir():
        os.makedirs("abc")
        for filename in ["hello.txt", os.path.join("abc/hello.txt")]:
            with open(filename, "w") as f:
                f.write("hello")

        i = 0
        for doc in run_dexy_without_tempdir(config):
            i += 1
            doc.run()
            assert doc.output() == "hello"

        assert i == 2

def test_args_copied():
    config = {
        "." : {
            "*.md|jinja" : { "inputs" : ["*.txt"] },
            "*.txt" : { "meta" : 5 }
        },
    }

    with tempdir():
        for filename in ["abc.txt", "def.txt", "template.md"]:
            with open(filename, "w") as f:
                f.write("hello")

        i = 0
        for doc in run_dexy_without_tempdir(config):
            i += 1
            doc.run()
            if doc.key().endswith(".txt"):
                assert doc.output() == "hello"
                assert doc.last_artifact.args['meta'] == 5
                assert len(doc.inputs) == 0
            elif doc.key().endswith(".md"):
                assert len(doc.inputs) == 2

        assert i == 3

def test_config_applies_in_subdirectory():
    with tempdir():
        with open(".dexy", "wb") as f:
            json.dump({"*.txt" : {}}, f)

        os.makedirs("abc")

        args = controller_args()
        c = Controller(args)
        c.load_config()
        assert c.config['.'].has_key("*.txt")
        assert c.config['./abc'].has_key("*.txt")



from dexy.tests.utils import wrap
from dexy.tests.utils import tempdir
from dexy.tests.utils import TEST_DATA_DIR
import shutil
import dexy.doc
import dexy.node
import inspect
import os
from dexy.wrapper import Wrapper

LOGLEVEL = "INFO"

def test_example_project():
    with tempdir():
        def run_from_cache_a_bunch_of_times():
            for i in range(5):
                print i
                wrapper = Wrapper(log_level=LOGLEVEL)
                wrapper.run_from_new()
    
                for node in wrapper.nodes.values():
                    expected = 'consolidated'
                    msg = "'%s' not in state '%s' in iter %s, in state '%s'"
                    msgargs = (node.key, expected, i, node.state)
                    assert node.state == expected, msg % msgargs


        example_src = os.path.join(TEST_DATA_DIR, 'example')
        shutil.copytree(example_src, "example")
        os.chdir("example")

        wrapper = Wrapper(log_level=LOGLEVEL)
        wrapper.create_dexy_dirs()

        wrapper.run_from_new()

        for node in wrapper.nodes.values():
            assert node.state == 'ran'

        run_from_cache_a_bunch_of_times()

        # touch this file so it triggers cache updating
        os.utime("multiply.py", None)

        unaffected_keys = ('latex', 'pygments.sty|pyg', 's1/loop.py|pycon', 's1/loop.py|py',
                'main.rst|idio|h', 'main.rst|idio|l', 'main.rst|pyg|l', 'main.rst|pyg|h',
                's1/loop.py|idio|h', 's1/loop.py|idio|l', 's1/loop.py|pyg|l', 's1/loop.py|pyg|h',
                'dexy.yaml|idio|h', 'dexy.yaml|idio|l', 'dexy.yaml|pyg|l', 'dexy.yaml|pyg|h',
                )

        affected_keys = ('code', 'docs', "*|pyg|l", "*|pyg|h", "*|idio|l", "*|idio|h",
                "main.rst|jinja|rst|latex", "*.rst|jinja|rst|latex",
                "*.py|pycon", "*.py|py", "main.rst|jinja|rstbody|easyhtml",
                "*.rst|jinja|rstbody|easyhtml", "foo.txt",
                "multiply.py|idio|h", "multiply.py|idio|l", "multiply.py|pycon", "multiply.py|py",
                "multiply.py|pyg|h", "multiply.py|pyg|l",
                )

        wrapper = Wrapper(log_level=LOGLEVEL)
        wrapper.run_from_new()

        for node in wrapper.nodes.values():
            if node.key in unaffected_keys:
                assert node.state == 'consolidated'
            else:
                assert node.key in affected_keys, node.key
                assert node.state == 'ran'

        run_from_cache_a_bunch_of_times()

        import time
        time.sleep(0.5)

        with open("multiply.py", "r") as f:
            old_content = f.read()
        
        with open("multiply.py", "w") as f:
            f.write("raise")

        try:
            wrapper = Wrapper(log_level=LOGLEVEL)
            wrapper.run_from_new()
            assert False, "should raise error"
        except dexy.exceptions.UserFeedback as e:
            assert "nonzero exit status 1" in str(e)

        import time
        time.sleep(0.9)

        with open("multiply.py", "w") as f:
            f.write(old_content)

        wrapper = Wrapper(log_level="DEBUG")
        wrapper.run_from_new()

        for node in wrapper.nodes.values():
            if node.key in unaffected_keys:
                assert node.state == 'consolidated'
            else:
                assert node.key in affected_keys, node.key
                assert node.state == 'ran'

        os.chdir("..")

def test_ragel_state_chart_to_image():
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
    with wrap() as wrapper:
        graph_png = dexy.doc.Doc("example.rl|rlrbd|dot",
                wrapper,
                [],
                contents=ragel
                )

        syntax = dexy.doc.Doc("example.rl|rlrbd|pyg",
                wrapper,
                [],
                contents=ragel
                )

        wrapper.run_docs(graph_png, syntax)
        assert graph_png.state == 'ran'
        assert syntax.state == 'ran'

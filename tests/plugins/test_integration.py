from dexy.wrapper import Wrapper
from tests.utils import TEST_DATA_DIR
from tests.utils import tempdir
from tests.utils import wrap
import dexy.doc
import dexy.node
import inspect
import os
import random
import shutil

LOGLEVEL = "WARN"

def assert_node_state(node, expected, additional_info=''):
    msg = "'%s' not in state '%s',  in state '%s'. %s"
    msgargs = (node.key, expected, node.state, additional_info)
    assert node.state == expected, msg % msgargs

def test_example_project():
    with tempdir():
        def run_from_cache_a_bunch_of_times():
            n = random.randint(2, 10)
            print("running %s times:" % n)
            for i in range(n):
                print('', i+1)
                wrapper = Wrapper(log_level=LOGLEVEL, debug=True)
                wrapper.run_from_new()
    
                for node in list(wrapper.nodes.values()):
                    assert_node_state(node, 'consolidated', "In iter %s" % i)

                wrapper.report()

        example_src = os.path.join(TEST_DATA_DIR, 'example')
        shutil.copytree(example_src, "example")
        os.chdir("example")

        wrapper = Wrapper(log_level=LOGLEVEL)
        wrapper.create_dexy_dirs()

        wrapper.run_from_new()
        wrapper.report()

        for node in list(wrapper.nodes.values()):
            assert_node_state(node, 'ran', "in first run")

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
        wrapper.report()

        for node in list(wrapper.nodes.values()):
            if node.key in unaffected_keys:
                assert_node_state(node, 'consolidated', "after touching multiply.py")
            else:
                assert node.key in affected_keys, node.key
                assert_node_state(node, 'ran', "after touchimg multiply.py")

        run_from_cache_a_bunch_of_times()

        import time
        time.sleep(0.5)

        with open("multiply.py", "r") as f:
            old_content = f.read()
        
        with open("multiply.py", "w") as f:
            f.write("raise")

        wrapper = Wrapper(log_level=LOGLEVEL)
        wrapper.run_from_new()
        assert wrapper.state == 'error'

        import time
        time.sleep(0.9)

        with open("multiply.py", "w") as f:
            f.write(old_content)

        wrapper = Wrapper(log_level=LOGLEVEL)
        wrapper.run_from_new()

        for node in list(wrapper.nodes.values()):
            if node.key in unaffected_keys:
                assert_node_state(node, 'consolidated', "after restoring old multiply.py content")
            else:
                assert node.key in affected_keys, node.key
                assert_node_state(node, 'ran', "after restoring old multiply.py contnet")

        wrapper.remove_dexy_dirs()
        wrapper.remove_reports_dirs(keep_empty_dir=True)
        wrapper.create_dexy_dirs()

        assert len(os.listdir(".dexy")) == 1

        wrapper = Wrapper(log_level=LOGLEVEL, dry_run=True)
        wrapper.run_from_new()
        wrapper.report()

        assert len(os.listdir(".dexy")) == 6

        with open(".dexy/reports/graph.txt", "r") as f:
            graph_text = f.read()

        assert "BundleNode(docs) (uncached)" in graph_text

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

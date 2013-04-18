from dexy.commands.utils import init_wrapper
from dexy.exceptions import InternalDexyProblem
from dexy.exceptions import UserFeedback
from dexy.parser import AbstractSyntaxTree
from dexy.parsers.doc import Yaml
from dexy.tests.utils import capture_stdout
from dexy.tests.utils import tempdir
from dexy.tests.utils import wrap
from dexy.wrapper import Wrapper
from nose.exc import SkipTest
import dexy.batch
import os

def test_remove_trash_no_trash():
    with tempdir():
        wrapper = Wrapper()
        wrapper.empty_trash()

def test_remove_trash_with_trash():
    with tempdir():
        wrapper = Wrapper()
        os.mkdir(".trash")
        assert os.path.exists(".trash")
        wrapper.empty_trash()
        assert not os.path.exists(".trash")

def test_state_new_after_init():
    wrapper = Wrapper()
    wrapper.validate_state('new')

def test_error_if_to_valid_called_without_dirs_setup():
    with tempdir():
        wrapper = Wrapper()
        try:
            wrapper.to_valid()
            assert False, "should not get here"
        except InternalDexyProblem:
            assert True

def test_state_valid_after_to_valid():
    with tempdir():
        wrapper = Wrapper()
        wrapper.create_dexy_dirs()
        wrapper.to_valid()
        wrapper.validate_state('valid')

def test_walked():
    with tempdir():
        with open("dexy.yaml", "w") as f:
            f.write("foo.txt")

        with open("foo.txt", "w") as f:
            f.write("foo")

        wrapper = Wrapper()
        wrapper.create_dexy_dirs()
        wrapper.to_valid()
        wrapper.to_walked()
        wrapper.validate_state('walked')

def test_checked():
    with tempdir():
        with open("dexy.yaml", "w") as f:
            f.write("foo.txt")

        with open("foo.txt", "w") as f:
            f.write("foo")

        wrapper = Wrapper()
        wrapper.create_dexy_dirs()
        wrapper.to_valid()
        wrapper.to_walked()
        wrapper.to_checked()
        wrapper.validate_state('checked')

def test_ran():
    with tempdir():
        with open("dexy.yaml", "w") as f:
            f.write("foo.txt")

        with open("foo.txt", "w") as f:
            f.write("foo")

        wrapper = Wrapper()
        wrapper.create_dexy_dirs()
        wrapper.run_from_new()
        for node in wrapper.roots:
            assert node.state == 'ran'
        wrapper.validate_state('ran')

        wrapper = Wrapper()
        wrapper.run_from_new()
        for node in wrapper.roots:
            assert node.state == 'consolidated'
        wrapper.validate_state('ran')

def test_explicit_configs():
    wrapper = Wrapper()
    wrapper.configs = "foo.txt bar.txt   abc/def/foo.txt "
    assert wrapper.explicit_config_files() == ['foo.txt',
            'bar.txt', 'abc/def/foo.txt']

def test_parse_doc_configs_single_empty_config():
    with tempdir():
        wrapper = Wrapper()
        wrapper.create_dexy_dirs()

        with open("dexy.yaml", "w") as f:
            f.write("foo.txt")

        with open("foo.txt", "w") as f:
            f.write("foo")

        wrapper = Wrapper()
        wrapper.to_valid()
        wrapper.to_walked()

def test_parse_doc_configs_no_configs():
    with tempdir():
        with capture_stdout() as stdout:
            wrapper = Wrapper()
            wrapper.create_dexy_dirs()

            wrapper = Wrapper()
            wrapper.to_valid()
            wrapper.to_walked()
            value = stdout.getvalue()
        assert "didn't find any document config files" in value

def test_assert_dexy_dirs():
    with tempdir():
        wrapper = Wrapper()
        try:
            wrapper.assert_dexy_dirs_exist()
            assert False
        except UserFeedback:
            assert True

def test_create_remove_dexy_dirs():
    with tempdir():
        wrapper = Wrapper()
        wrapper.create_dexy_dirs()
        wrapper.to_valid()
        assert wrapper.dexy_dirs_exist()
        wrapper.remove_dexy_dirs()
        assert not wrapper.dexy_dirs_exist()

def test_init_wrapper_if_dexy_dirs_exist():
    with tempdir():
        wrapper = Wrapper()
        wrapper.create_dexy_dirs()

        with open("hello.txt", "w") as f:
            f.write("hello")

        wrapper = Wrapper()
        wrapper.to_valid()
        assert wrapper.project_root
        wrapper.to_walked()
        assert 'hello.txt' in wrapper.filemap
        assert 'dexy.log' in os.listdir('logs')
        assert 'logs' in wrapper.exclude_dirs()
        assert not 'logs/dexy.log' in wrapper.filemap

def test_nodexy_files():
    with tempdir():
        wrapper = Wrapper()
        wrapper.create_dexy_dirs()

        with open("hello.txt", "w") as f:
            f.write("hello")

        os.makedirs("s1/s2/s3")

        nodexy_path = "s1/s2/.nodexy"
        with open(nodexy_path, 'w') as f:
            f.write("dexy stop here")

        with open("s1/s2/ignore.txt", "w") as f:
            f.write("dexy should ignore this")

        with open("s1/s2/s3/ignore.txt", "w") as f:
            f.write("dexy should also ignore this")

        # Only the hello.txt file is visible to dexy
        wrapper = Wrapper()
        wrapper.to_valid()
        wrapper.to_walked()
        assert len(wrapper.filemap) == 1
        assert 'hello.txt' in wrapper.filemap

        os.remove(nodexy_path)

        # Now we can see all 3 text files.
        wrapper = Wrapper()
        wrapper.to_valid()
        wrapper.to_walked()
        assert len(wrapper.filemap) == 3
        assert 'hello.txt' in wrapper.filemap
        assert 's1/s2/ignore.txt' in wrapper.filemap
        assert 's1/s2/s3/ignore.txt' in wrapper.filemap

# old
def test_config_for_directory():
    with wrap() as wrapper:
        with open("docs.yaml", "w") as f:
            f.write(""".abc""")

        with open("root.abc", "w") as f:
            f.write("hello")

        with open("root.def", "w") as f:
            f.write("hello")

        os.makedirs("s1")
        os.makedirs("s2")

        with open("s1/s1.abc", "w") as f:
            f.write("hello")

        with open("s1/s1.def", "w") as f:
            f.write("hello")

        with open("s2/s2.abc", "w") as f:
            f.write("hello")

        with open("s2/s2.def", "w") as f:
            f.write("hello")

        with open(os.path.join('s1', 'docs.yaml'), 'w') as f:
            f.write(""".def|dexy""")

        wrapper = Wrapper()
        wrapper.to_valid()
        wrapper.to_walked()
        wrapper.to_checked()
        wrapper.run()

        assert len(wrapper.nodes) == 6

        p = wrapper.nodes["pattern:*.abc"]
        c = wrapper.nodes["doc:s2/s2.abc"]
        assert c in p.children

def test_config_file():
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("""{ "logfile" : "a.log" }""")

        wrapper = init_wrapper({'conf' : 'dexy.conf'})
        assert wrapper.log_file == "a.log"

def test_kwargs_override_config_file():
    with tempdir():
        with open("dexy.conf", "w") as f:
            f.write("""{ "logfile" : "a.log" }""")

        wrapper = init_wrapper({
            '__cli_options' : { 'logfile' : 'b.log' },
            'logfile' : "b.log",
            'conf' : 'dexy.conf'
            })
        assert wrapper.log_file == "b.log"

def test_wrapper_init():
    wrapper = Wrapper()
    assert wrapper.artifacts_dir == '.cache'

YAML = """foo:
    - bar
    - baz

foob:
    - foobar

xyz:
    - abc
    - def
"""

def run_yaml_with_target(target):
    with wrap() as wrapper:
        wrapper.nodes = {}
        wrapper.roots = []
        wrapper.batch = dexy.batch.Batch(wrapper)
        wrapper.filemap = wrapper.map_files()

        ast = AbstractSyntaxTree(wrapper)
        parser = Yaml(wrapper, ast)
        parser.parse('.', YAML)
        ast.walk()

        wrapper.transition('walked')
        wrapper.to_checked()

        assert len(wrapper.roots) == 3
        assert len(wrapper.nodes) == 8

        wrapper.target = target
        wrapper.run()

        yield wrapper

def test_run_target_foo():
    for wrapper in run_yaml_with_target("foo"):
        assert wrapper.nodes['bundle:foo'].state == 'ran'
        assert wrapper.nodes['bundle:bar'].state == 'ran'
        assert wrapper.nodes['bundle:baz'].state == 'ran'
        assert wrapper.nodes['bundle:foob'].state == 'uncached'
        assert wrapper.nodes['bundle:foobar'].state == 'uncached'
        assert wrapper.nodes['bundle:xyz'].state == 'uncached'

def test_run_target_fo():
    for wrapper in run_yaml_with_target("fo"):
        # foo and children have been run
        assert wrapper.nodes['bundle:foo'].state == 'ran'
        assert wrapper.nodes['bundle:bar'].state == 'ran'
        assert wrapper.nodes['bundle:baz'].state == 'ran'

        # foob and children have been run
        assert wrapper.nodes['bundle:foob'].state == 'ran'
        assert wrapper.nodes['bundle:foobar'].state == 'ran'

def test_run_target_bar():
    for wrapper in run_yaml_with_target("bar"):
        raise SkipTest("TODO implement matching non-root nodes")
        assert wrapper.nodes['bundle:foo'].state == 'checked'
        assert wrapper.nodes['bundle:bar'].state == 'ran'
        assert wrapper.nodes['bundle:baz'].state == 'checked'
        assert wrapper.nodes['bundle:foob'].state == 'checked'
        assert wrapper.nodes['bundle:foobar'].state == 'checked'

def test_run_target_ba():
    raise SkipTest("TODO implement matching non-root nodes")
    for wrapper in run_yaml_with_target("ba"):
        assert wrapper.nodes['bundle:foo'].state == 'new'
        assert wrapper.nodes['bundle:bar'].state == 'ran'
        assert wrapper.nodes['bundle:baz'].state == 'ran'
        assert wrapper.nodes['bundle:foob'].state == 'new'
        assert wrapper.nodes['bundle:foobar'].state == 'new'

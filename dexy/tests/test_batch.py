from dexy.tests.utils import wrap
from dexy.plugins.parsers import YamlFileParser

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
        parser = YamlFileParser()
        parser.wrapper = wrapper
        parser.parse(YAML)
        assert len(wrapper.batch.tree) == 3

        wrapper.batch.run(target)
        yield wrapper.batch

def test_run_target_foo():
    for batch in run_yaml_with_target("foo"):
        # foo and children have been run
        assert batch.lookup_table['BundleNode:foo'].state == 'complete'
        assert batch.lookup_table['BundleNode:bar'].state == 'complete'
        assert batch.lookup_table['BundleNode:baz'].state == 'complete'

        # foob and children have not been run
        assert batch.lookup_table['BundleNode:foob'].state == 'new'
        assert batch.lookup_table['BundleNode:foobar'].state == 'new'

def test_run_target_fo():
    for batch in run_yaml_with_target("fo"):
        # foo and children have been run
        assert batch.lookup_table['BundleNode:foo'].state == 'complete'
        assert batch.lookup_table['BundleNode:bar'].state == 'complete'
        assert batch.lookup_table['BundleNode:baz'].state == 'complete'

        # foob and children have been run
        assert batch.lookup_table['BundleNode:foob'].state == 'complete'
        assert batch.lookup_table['BundleNode:foobar'].state == 'complete'

def test_run_target_bar():
    for batch in run_yaml_with_target("bar"):
        assert batch.lookup_table['BundleNode:foo'].state == 'new'
        assert batch.lookup_table['BundleNode:bar'].state == 'complete'
        assert batch.lookup_table['BundleNode:baz'].state == 'new'
        assert batch.lookup_table['BundleNode:foob'].state == 'new'
        assert batch.lookup_table['BundleNode:foobar'].state == 'new'

def test_run_target_ba():
    for batch in run_yaml_with_target("ba"):
        assert batch.lookup_table['BundleNode:foo'].state == 'new'
        assert batch.lookup_table['BundleNode:bar'].state == 'complete'
        assert batch.lookup_table['BundleNode:baz'].state == 'complete'
        assert batch.lookup_table['BundleNode:foob'].state == 'new'
        assert batch.lookup_table['BundleNode:foobar'].state == 'new'

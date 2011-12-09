from dexy.artifact import Artifact
from dexy.filters.templating_filters import TemplateFilter
from dexy.filters.templating_filters import TemplatePlugin

class TestTemplatePlugin(TemplatePlugin):
    def run(self):
        return {'a' : 1}

class TestTemplateFilter(TemplateFilter):
    PLUGINS = [TestTemplatePlugin]

def test_template_filter():
    test_filter = TestTemplateFilter()
    test_filter.artifact = Artifact()
    env = test_filter.run_plugins()
    assert env.has_key('a')
    assert env['a'] == 1

    s = test_filter.process_text("The value of a is %(a)s")
    assert s == "The value of a is 1"

def test_template_filter_with_custom_plugins():
    test_filter = TestTemplateFilter()
    test_filter.artifact = Artifact()
    test_filter.artifact.args['plugins'] = ['TestTemplatePlugin']
    env = test_filter.run_plugins()
    assert env.has_key('a')
    assert env['a'] == 1

    s = test_filter.process_text("The value of a is %(a)s")
    assert s == "The value of a is 1"

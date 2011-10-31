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
    env = test_filter.run_plugins()
    assert env.has_key('a')
    assert env['a'] == 1

    s = test_filter.process_text("The value of a is %(a)s")
    assert s == "The value of a is 1"

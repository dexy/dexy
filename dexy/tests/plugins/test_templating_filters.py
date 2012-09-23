from dexy.doc import Doc
from dexy.plugins.templating_filters import TemplateFilter
from dexy.plugins.templating_plugins import TemplatePlugin
from dexy.tests.utils import wrap
import dexy.exceptions

def test_jinja_filter_inputs():
    with wrap() as wrapper:
        doc = Doc("template.txt|jinja",
                Doc("input.txt",
                    contents = "I am the input.",
                    wrapper=wrapper),
                contents = "The input is '{{ d['input.txt'] }}'",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "The input is 'I am the input.'"

def test_jinjatext_filter_undefined():
    with wrap() as wrapper:
        doc = Doc("template.txt|jinjatext",
                contents = "there is no {{ foo }}",
                wrapper=wrapper)

        try:
            wrapper.run_docs(doc)
            assert False, 'should raise UserFeedback'
        except dexy.exceptions.UserFeedback as e:
            assert "'foo' is undefined" in e.message

class TestSimple(TemplatePlugin):
    ALIASES = ['testtemplate']
    def run(self):
        return {'aaa' : 1}

class TestTemplateFilter(TemplateFilter):
    ALIASES = ['testtemplatefilter']

def test_template_filter_with_custom_filter_only():
    with wrap() as wrapper:
        doc = Doc("hello.txt|testtemplatefilter",
                contents = "aaa equals %(aaa)s",
                testtemplatefilter = { "plugins" : ["testtemplate"] },
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "aaa equals 1"
        plugins_used = doc.final_artifact.filter_instance.template_plugins()
        assert len(plugins_used) == 1
        assert plugins_used[0] == TestSimple

def test_jinjatext_filter():
    with wrap() as wrapper:
        doc = Doc("template.txt|jinjatext",
                contents = "1 + 1 is {{ 1+1 }}",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "1 + 1 is 2"

def test_jinjatext_filter_tex_extension():
    with wrap() as wrapper:
        doc = Doc("template.tex|jinjatext",
                contents = "1 + 1 is << 1+1 >>",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "1 + 1 is 2"

def test_jinjatext_filter_custom_delims():
    with wrap() as wrapper:
        doc = Doc("template.tex|jinjatext",
                contents = "1 + 1 is %- 1+1 -%",
                jinjatext = {
                    "variable_start_string" : "%-",
                    "variable_end_string" : "-%"
                    },
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "1 + 1 is 2"

def test_jinjatext_filter_set_vars():
    with wrap() as wrapper:
        doc = Doc("template.txt|jinjatext",
                contents = """{% set foo = 'bar' -%}\nfoo is {{ foo }}\n""",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "foo is bar"

def test_jinja_filter_set_vars():
    with wrap() as wrapper:
        doc = Doc("template.txt|jinja",
                contents = """{% set foo = 'bar' -%}\nfoo is {{ foo }}\n""",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "foo is bar"

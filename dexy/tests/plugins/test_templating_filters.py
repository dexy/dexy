from dexy.doc import Doc
from dexy.plugins.templating_filters import TemplateFilter
from dexy.plugins.templating_plugins import TemplatePlugin
from dexy.tests.utils import wrap
from nose.tools import raises
import dexy.exceptions

def test_jinja_indent_function():
    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja",
                Doc("lines.txt",
                    contents = "line one\nline two",
                    wrapper=wrapper),
                contents = """lines are:\n   {{ d['lines.txt'] | indent(3) }}""",
                wrapper=wrapper)
        wrapper.run_docs(doc)
        assert str(doc.output()) == """lines are:
   line one
   line two"""

def test_jinja_kv():
    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja",
                Doc("blank.txt|keyvalueexample",
                    contents = " ",
                    wrapper=wrapper),
                contents = """value of foo is '{{ d['blank.txt|keyvalueexample']['foo'] }}'""",
                wrapper=wrapper)
        wrapper.run_docs(doc)
        assert str(doc.output()) == "value of foo is 'bar'"

@raises(dexy.exceptions.UserFeedback)
def test_jinja_sectioned_invalid_section():
    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja",
                Doc("lines.txt|lines",
                    contents = "line one\nline two",
                    wrapper=wrapper),
                contents = """first line is '{{ d['lines.txt|lines']['3'] }}'""",
                wrapper=wrapper)
        wrapper.run_docs(doc)

def test_jinja_sectioned():
    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja",
                Doc("lines.txt|lines",
                    contents = "line one\nline two",
                    wrapper=wrapper),
                contents = """first line is '{{ d['lines.txt|lines']['1'] }}'""",
                wrapper=wrapper)
        wrapper.run_docs(doc)
        assert str(doc.output()) == "first line is 'line one'"

def test_jinja_json_convert_to_dict():
    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja",
                Doc("input.json",
                    contents = """{"foo":123}""",
                    wrapper=wrapper),
                contents = """foo is {{ d['input.json'].json_as_dict()['foo'] }}""",
                wrapper=wrapper)
        wrapper.run_docs(doc)
        assert str(doc.output()) == "foo is 123"

@raises(dexy.exceptions.UserFeedback)
def test_jinja_json():
    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja",
                Doc("input.json",
                    contents = """{"foo":123}""",
                    wrapper=wrapper),
                contents = """foo is {{ d['input.json']['foo'] }}""",
                wrapper=wrapper)
        wrapper.run_docs(doc)

@raises(dexy.exceptions.UserFeedback)
def test_jinja_undefined():
    with wrap() as wrapper:
        doc = Doc("template.txt|jinja",
                contents = """{{ foo }}""",
                wrapper=wrapper)

        wrapper.run_docs(doc)

@raises(dexy.exceptions.UserFeedback)
def test_jinja_syntax_error():
    with wrap() as wrapper:
        doc = Doc("template.txt|jinja",
                contents = """{% < set foo = 'bar' -%}\nfoo is {{ foo }}\n""",
                wrapper=wrapper)

        wrapper.run_docs(doc)

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

class TestSimple(TemplatePlugin):
    """
    test plugin
    """
    ALIASES = ['testtemplate']
    def run(self):
        return {'aaa' : 1}

class TestTemplateFilter(TemplateFilter):
    """
    test template
    """
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

def test_jinja_filter():
    with wrap() as wrapper:
        doc = Doc("template.txt|jinja",
                contents = "1 + 1 is {{ 1+1 }}",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "1 + 1 is 2"

def test_jinja_filter_tex_extension():
    with wrap() as wrapper:
        doc = Doc("template.tex|jinja",
                contents = "1 + 1 is << 1+1 >>",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "1 + 1 is 2"

def test_jinja_filter_custom_delims():
    with wrap() as wrapper:
        doc = Doc("template.tex|jinja",
                contents = "1 + 1 is %- 1+1 -%",
                jinja = {
                    "variable_start_string" : "%-",
                    "variable_end_string" : "-%"
                    },
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "1 + 1 is 2"

def test_jinja_filter_set_vars():
    with wrap() as wrapper:
        doc = Doc("template.txt|jinja",
                contents = """{% set foo = 'bar' -%}\nfoo is {{ foo }}\n""",
                wrapper=wrapper)

        wrapper.run_docs(doc)

        assert doc.output().as_text() == "foo is bar"

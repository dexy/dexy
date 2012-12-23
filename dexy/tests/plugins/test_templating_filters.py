from dexy.node import DocNode
from dexy.plugins.templating_filters import TemplateFilter
from dexy.plugins.templating_plugins import TemplatePlugin
from dexy.tests.utils import wrap
from nose.tools import raises
import dexy.exceptions

def test_jinja_indent_function():
    with wrap() as wrapper:
        node = DocNode("hello.txt|jinja",
                contents = """lines are:\n   {{ d['lines.txt'] | indent(3) }}""",
                inputs = [
                    DocNode("lines.txt",
                        contents = "line one\nline two",
                        wrapper=wrapper)
                    ],
                wrapper=wrapper)
        wrapper.run_docs(node)
        assert str(node.children[0].output()) == """lines are:
   line one
   line two"""

def test_jinja_kv():
    with wrap() as wrapper:
        node = DocNode("hello.txt|jinja",
                contents = """value of foo is '{{ d['blank.txt|keyvalueexample']['foo'] }}'""",
                inputs = [
                    DocNode("blank.txt|keyvalueexample",
                        contents = " ",
                        wrapper=wrapper)
                    ],
                wrapper=wrapper)
        wrapper.run_docs(node)
        doc = node.children[0]
        assert str(doc.output()) == "value of foo is 'bar'"

@raises(dexy.exceptions.UserFeedback)
def test_jinja_sectioned_invalid_section():
    with wrap() as wrapper:
        doc = DocNode("hello.txt|jinja",
                contents = """first line is '{{ d['lines.txt|lines']['3'] }}'""",
                inputs = [
                    DocNode("lines.txt|lines",
                        contents = "line one\nline two",
                        wrapper=wrapper)
                    ],
                wrapper=wrapper)
        wrapper.run_docs(doc)

def test_jinja_sectioned():
    with wrap() as wrapper:
        node = DocNode("hello.txt|jinja",
                contents = """first line is '{{ d['lines.txt|lines']['1'] }}'""",
                inputs = [
                    DocNode("lines.txt|lines",
                        contents = "line one\nline two",
                        wrapper=wrapper)
                    ],
                wrapper=wrapper)
        wrapper.run_docs(node)
        doc = node.children[0]
        assert str(doc.output()) == "first line is 'line one'"

def test_jinja_json_convert_to_dict():
    with wrap() as wrapper:
        node = DocNode("hello.txt|jinja",
                contents = """foo is {{ d['input.json'].json_as_dict()['foo'] }}""",
                inputs = [
                    DocNode("input.json",
                        contents = """{"foo":123}""",
                        wrapper=wrapper)
                    ],
                wrapper=wrapper)
        wrapper.run_docs(node)
        doc = node.children[0]
        assert str(doc.output()) == "foo is 123"

@raises(dexy.exceptions.UserFeedback)
def test_jinja_json():
    with wrap() as wrapper:
        node = DocNode("hello.txt|jinja",
                contents = """foo is {{ d['input.json']['foo'] }}""",
                inputs = [
                    DocNode("input.json",
                        contents = """{"foo":123}""",
                        wrapper=wrapper)
                    ],
                wrapper=wrapper)
        wrapper.run_docs(node)

@raises(dexy.exceptions.UserFeedback)
def test_jinja_undefined():
    with wrap() as wrapper:
        node = DocNode("template.txt|jinja",
                contents = """{{ foo }}""",
                wrapper=wrapper)

        wrapper.run_docs(node)

@raises(dexy.exceptions.UserFeedback)
def test_jinja_syntax_error():
    with wrap() as wrapper:
        node = DocNode("template.txt|jinja",
                contents = """{% < set foo = 'bar' -%}\nfoo is {{ foo }}\n""",
                wrapper=wrapper)

        wrapper.run_docs(node)

def test_jinja_filter_inputs():
    with wrap() as wrapper:
        node = DocNode("template.txt|jinja",
                contents = "The input is '{{ d['input.txt'] }}'",
                inputs = [
                    DocNode("input.txt",
                        contents = "I am the input.",
                        wrapper=wrapper)
                    ],
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
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
        node = DocNode("hello.txt|testtemplatefilter",
                contents = "aaa equals %(aaa)s",
                testtemplatefilter = { "plugins" : ["testtemplate"] },
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().as_text() == "aaa equals 1"
        plugins_used = doc.final_artifact.filter_instance.template_plugins()
        assert len(plugins_used) == 1
        assert plugins_used[0] == TestSimple

def test_jinja_filter():
    with wrap() as wrapper:
        node = DocNode("template.txt|jinja",
                contents = "1 + 1 is {{ 1+1 }}",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().as_text() == "1 + 1 is 2"

def test_jinja_filter_tex_extension():
    with wrap() as wrapper:
        node = DocNode("template.tex|jinja",
                contents = "1 + 1 is << 1+1 >>",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().as_text() == "1 + 1 is 2"

def test_jinja_filter_custom_delims():
    with wrap() as wrapper:
        node = DocNode("template.tex|jinja",
                contents = "1 + 1 is %- 1+1 -%",
                jinja = {
                    "variable_start_string" : "%-",
                    "variable_end_string" : "-%"
                    },
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().as_text() == "1 + 1 is 2"

def test_jinja_filter_set_vars():
    with wrap() as wrapper:
        node = DocNode("template.txt|jinja",
                contents = """{% set foo = 'bar' -%}\nfoo is {{ foo }}\n""",
                wrapper=wrapper)

        wrapper.run_docs(node)
        doc = node.children[0]
        assert doc.output().as_text() == "foo is bar"

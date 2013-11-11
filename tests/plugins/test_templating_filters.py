from dexy.doc import Doc
from dexy.filters.templating import TemplateFilter
from dexy.filters.templating_plugins import TemplatePlugin
from tests.utils import wrap
from dexy.exceptions import UserFeedback

def test_jinja_pass_through():
    with wrap() as wrapper:
        with open("_template.html", "w") as f:
            f.write("{{ content }}")

        wrapper.reports = 'ws'
        contents = u"{{ link('input.txt') }}"
        doc = Doc("lines.html|jinja",
                    wrapper,
                    [
                        Doc("input.txt",
                            wrapper,
                            [],
                            contents = "nothing to see here"
                            )
                        ],
                    contents=contents,
                    apply_ws_to_content = True
                    )
        wrapper.run_docs(doc)
        assert unicode(doc.output_data()) == contents

        wrapper.report()

        with open("output-site/lines.html", 'r') as f:
            lines_html = f.read()
            assert lines_html == """<a href="/input.txt">Input</a>"""

def test_jinja_pass_through_fails_if_not_whitelisted():
    with wrap() as wrapper:
        contents = u"{{ linxxx('foo') }}"
        doc = Doc("lines.txt|jinja",
                    wrapper,
                    [],
                    contents=contents
                    )

        try:
            wrapper.run_docs(doc)
        except UserFeedback as e:
            assert "a UndefinedError problem" in str(e)
            assert "'linxxx' is undefined" in str(e)

def test_jinja_indent_function():
    with wrap() as wrapper:
        node = Doc("hello.txt|jinja",
                wrapper,
                [
                    Doc("lines.txt",
                        wrapper,
                        [],
                        contents = "line one\nline two"
                        )
                    ],
                contents = """lines are:\n   {{ d['lines.txt'] | indent(3) }}"""
                )
        wrapper.run_docs(node)
        assert str(node.output_data()) == """lines are:
   line one
   line two"""

def test_jinja_kv():
    with wrap() as wrapper:
        node = Doc("hello.txt|jinja",
                wrapper,
                [
                    Doc("blank.txt|keyvalueexample",
                        wrapper,
                        [],
                        contents = " ")
                    ],
                contents = """value of foo is '{{ d['blank.txt|keyvalueexample']['foo'] }}'"""
                )
        wrapper.run_docs(node)
        assert str(node.output_data()) == "value of foo is 'bar'"

def test_jinja_sectioned_invalid_section():
    with wrap() as wrapper:
        wrapper.debug = False
        doc = Doc("hello.txt|jinja",
                wrapper,
                [
                    Doc("lines.txt|lines",
                        wrapper,
                        [],
                        contents = "line one\nline two"
                        )
                    ],
                contents = """first line is '{{ d['lines.txt|lines']['3'] }}'"""
                )
        wrapper.run_docs(doc)
        assert wrapper.state == 'error'

def test_jinja_sectioned():
    with wrap() as wrapper:
        node = Doc("hello.txt|jinja",
                wrapper,
                [
                    Doc("lines.txt|lines",
                        wrapper,
                        [],
                        contents = "line one\nline two")
                    ],
                contents = """first line is '{{ d['lines.txt|lines']['1'] }}'""")
        wrapper.run_docs(node)
        assert str(node.output_data()) == "first line is 'line one'"

def test_jinja_json():
    with wrap() as wrapper:
        node = Doc("hello.txt|jinja",
                wrapper,
                [
                    Doc("input.json",
                        wrapper, [],
                        contents = """{"foo":123}"""
                        )
                    ],
                contents = """foo is {{ d['input.json']['foo'] }}""")
        wrapper.run_docs(node)
        assert str(node.output_data()) == "foo is 123"

def test_jinja_undefined():
    with wrap() as wrapper:
        wrapper.debug = False
        node = Doc("template.txt|jinja",
                wrapper,
                [],
                contents = """{{ foo }}""")

        wrapper.run_docs(node)
        assert wrapper.state == 'error'

def test_jinja_syntax_error():
    with wrap() as wrapper:
        wrapper.debug = False
        node = Doc("template.txt|jinja",
                wrapper,
                [],
                contents = """{% < set foo = 'bar' -%}\nfoo is {{ foo }}\n"""
                )

        wrapper.run_docs(node)
        assert wrapper.state == 'error'

def test_jinja_filter_inputs():
    with wrap() as wrapper:
        node = Doc("template.txt|jinja",
                wrapper,
                [Doc("input.txt",
                    wrapper,
                    [],
                    contents = "I am the input.")
                ],
                contents = "The input is '{{ d['input.txt'] }}'")

        wrapper.run_docs(node)
        assert str(node.output_data()) == "The input is 'I am the input.'"

class TestSimple(TemplatePlugin):
    """
    test plugin
    """
    aliases = ['testtemplate']
    def run(self):
        return {'aaa' : ("docs", 1)}

class TestTemplateFilter(TemplateFilter):
    """
    test template
    """
    aliases = ['testtemplatefilter']

def test_template_filter_with_custom_filter_only():
    with wrap() as wrapper:
        node = Doc("hello.txt|testtemplatefilter",
                wrapper,
                [],
                contents = "aaa equals %(aaa)s",
                testtemplatefilter = { "plugins" : ["testtemplate"] }
                )

        wrapper.run_docs(node)
        assert node.output_data().as_text() == "aaa equals 1"
        plugins_used = node.filters[-1].template_plugins()
        assert len(plugins_used) == 1
        assert isinstance(plugins_used[0], TestSimple)

def test_jinja_filter():
    with wrap() as wrapper:
        node = Doc("template.txt|jinja",
                wrapper,
                [],
                contents = "1 + 1 is {{ 1+1 }}"
                )

        wrapper.run_docs(node)
        assert node.output_data().as_text() == "1 + 1 is 2"

def test_jinja_filter_tex_extension():
    with wrap() as wrapper:
        node = Doc("template.tex|jinja",
                wrapper,
                [],
                contents = "1 + 1 is << 1+1 >>")

        wrapper.run_docs(node)
        assert node.output_data().as_text() == "1 + 1 is 2"

def test_jinja_filter_custom_delims():
    with wrap() as wrapper:
        node = Doc("template.tex|jinja",
                wrapper,
                [],
                contents = "1 + 1 is %- 1+1 -%",
                jinja = {
                    "variable_start_string" : "%-",
                    "variable_end_string" : "-%"
                    }
                )

        wrapper.run_docs(node)
        assert node.output_data().as_text() == "1 + 1 is 2"

def test_jinja_filter_set_vars():
    with wrap() as wrapper:
        node = Doc("template.txt|jinja",
                wrapper,
                [],
                contents = """{% set foo = 'bar' -%}\nfoo is {{ foo }}\n"""
                )

        wrapper.run_docs(node)
        assert node.output_data().as_text() == "foo is bar"

def test_jinja_filter_using_inflection():
    with wrap() as wrapper:
        node = Doc("template.txt|jinja",
                wrapper,
                [],
                contents = """{{ humanize("abc_def") }}"""
                )

        wrapper.run_docs(node)
        assert node.output_data().as_text() == "Abc def"

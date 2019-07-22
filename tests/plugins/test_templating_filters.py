from dexy.doc import Doc
#from dexy.utils import char_diff
from dexy.filters.templating import TemplateFilter
from dexy.filters.templating_plugins import TemplatePlugin
from tests.utils import wrap
from dexy.exceptions import UserFeedback

def test_jinja_invalid_attribute():
    def make_sections_doc(wrapper):
        return Doc("sections.txt",
                wrapper,
                [],
                contents = [{}, {"name" : "foo", "contents" : "This is foo."}]
                )

    with wrap() as wrapper:
        node = Doc("ok.txt|jinja",
                wrapper,
                [make_sections_doc(wrapper)],
                contents = """hello! foo contents are: {{ d['sections.txt'].foo }}"""
                )

        wrapper.run_docs(node)
        assert str(node.output_data()) == """hello! foo contents are: This is foo."""

    with wrap() as wrapper:
        node = Doc("broken.txt|jinja",
                wrapper,
                [make_sections_doc(wrapper)],
                contents = """There is no {{ d['sections.txt'].bar }}"""
                )
        try:
            wrapper.run_docs(node)
        except UserFeedback as e:
            assert str(e) == "No value for bar available in sections or metadata."

def test_jinja_pass_through():
    with wrap() as wrapper:
        with open("_template.html", "w") as f:
            f.write("{{ content }}")

        wrapper.reports = 'ws'
        contents = "{{ link(\"input.txt\") }}"
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
        assert str(doc.output_data()) == contents

        wrapper.report()

        with open("output-site/lines.html", 'r') as f:
            lines_html = f.read()
            assert lines_html == """<a href="input.txt">Input</a>"""

def test_jinja_pass_through_fails_if_not_whitelisted():
    with wrap() as wrapper:
        contents = "{{ linxxx('foo') }}"
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
                contents = "lines are:\n   {{ d['lines.txt'] | indent(3) }}"
                )
        wrapper.run_docs(node)
        assert str(node.output_data()) == """lines are:
   line one
   line two"""

def run_jinja_filter(contents):
    with wrap() as wrapper:
        doc = Doc("hello.txt|jinja",
                wrapper,
                [],
                contents = contents
                )
        wrapper.run_docs(doc)
        data = doc.output_data()
        data.data() # make sure is loaded
        return data

def test_jinja_filters_bs4():
    data = run_jinja_filter("{{ '<p>foo</p>' | prettify_html }}")
    assert str(data) == "<p>\n foo\n</p>"

def test_beautiful_soup_should_not_be_available_as_filter():
    try:
        run_jinja_filter("{{ 'foo' | BeautifulSoup }}")
        assert False
    except UserFeedback as e:
        assert "no filter named 'BeautifulSoup'" in str(e)

def test_jinja_filters_head():
    data = run_jinja_filter("{{ 'foo\nbar\nbaz' | head(1) }}")
    assert str(data) == "foo"
    data = run_jinja_filter("{{ 'foo\nbar\nbaz' | head(2) }}")
    assert str(data) == "foo\nbar"

def test_jinja_filters_tail():
    data = run_jinja_filter("{{ 'foo\nbar\nbaz' | tail(1) }}")
    assert str(data) == "baz"
    data = run_jinja_filter("{{ 'foo\nbar\nbaz' | tail(2) }}")
    assert str(data) == "bar\nbaz"

def test_jinja_filters_highlight():
    data = run_jinja_filter("{{ '<p>foo</p>' | highlight('html') }}")
    assert str(data) == """<div class="highlight"><pre><span></span><a name="l-1"></a><span class="p">&lt;</span><span class="nt">p</span><span class="p">&gt;</span>foo<span class="p">&lt;/</span><span class="nt">p</span><span class="p">&gt;</span>
</pre></div>\n"""
    
def test_jinja_filters_pygmentize():
    data = run_jinja_filter("{{ '<p>foo</p>' | pygmentize('html') }}")
    assert str(data)=="""<div class="highlight"><pre><span></span><a name="l-1"></a><span class="p">&lt;</span><span class="nt">p</span><span class="p">&gt;</span>foo<span class="p">&lt;/</span><span class="nt">p</span><span class="p">&gt;</span>
</pre></div>\n"""

def test_jinja_filters_combined():
    data = run_jinja_filter("{{ '<p>foo</p>' | prettify_html | highlight('html') }}")
    assert str(data) == """<div class="highlight"><pre><span></span><a name="l-1"></a><span class="p">&lt;</span><span class="nt">p</span><span class="p">&gt;</span>
<a name="l-2"></a> foo
<a name="l-3"></a><span class="p">&lt;/</span><span class="nt">p</span><span class="p">&gt;</span>
</pre></div>
"""

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
                contents = """first line is '{{ d['lines.txt|lines'][3] }}'"""
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

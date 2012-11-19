from dexy.tests.utils import wrap
from dexy.doc import Doc

def test_yamlmeta_no_yaml():
    with wrap() as wrapper:
        doc = Doc("example.txt|yamlmeta",
                contents = "This is the content.",
                wrapper=wrapper)

        wrapper.run_docs(doc)
        assert doc.output().as_text() == "This is the content."

def test_yamlmeta():
    with wrap() as wrapper:
        doc = Doc("example.txt|yamlmeta",
                contents = "title: My Title\n---\r\nThis is the content.",
                wrapper=wrapper)

        wrapper.run_docs(doc)
        assert doc.title() == "My Title"
        assert doc.output().as_text() == "This is the content."

YAML = """filterargs:
  foo: 5
  bar: 42
  baz: xyz
"""

RESULT = """Here are the arguments you passed:
bar: 42
baz: xyz
foo: 5"""
def test_yamlmeta_filterargs():
    with wrap() as wrapper:
        doc = Doc("example.txt|yamlmeta|filterargs",
                contents = "%s\n---\r\nThis is the content." % YAML,
                wrapper=wrapper)

        wrapper.run_docs(doc)
        assert doc.output().as_text() == RESULT

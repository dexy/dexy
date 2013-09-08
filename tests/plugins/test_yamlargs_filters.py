from dexy.doc import Doc
from tests.utils import wrap
from dexy.wrapper import Wrapper

def test_yamlargs_with_caching():
    with wrap() as wrapper:
        doc = Doc("example.txt|yamlargs",
                wrapper,
                [],
                contents = "title: My Title\n---\r\nThis is the content."
                )
        wrapper.run_docs(doc)

        task = wrapper.nodes["doc:example.txt|yamlargs"]
        assert task.output_data().title() == "My Title"
        assert task.state == 'ran'

        wrapper = Wrapper()
        doc = Doc("example.txt|yamlargs",
                wrapper,
                [],
                contents = "title: My Title\n---\r\nThis is the content."
                )
        wrapper.run_docs(doc)
        task = wrapper.nodes["doc:example.txt|yamlargs"]
        assert task.output_data().title() == "My Title"
        assert task.state == 'consolidated'

        wrapper = Wrapper()
        doc = Doc("example.txt|yamlargs",
                wrapper,
                [],
                contents = "title: My Title\n---\r\nThis is the content."
                )
        wrapper.run_docs(doc)
        task = wrapper.nodes["doc:example.txt|yamlargs"]
        assert task.output_data().title() == "My Title"
        assert task.state == 'consolidated'

def test_yamlargs_no_yaml():
    with wrap() as wrapper:
        doc = Doc("example.txt|yamlargs",
                wrapper,
                [],
                contents = "This is the content.")

        wrapper.run_docs(doc)
        assert doc.output_data().as_text() == "This is the content."

def test_yamlargs():
    with wrap() as wrapper:
        doc = Doc("example.txt|yamlargs",
                wrapper,
                [],
                contents = "title: My Title\n---\r\nThis is the content."
                )

        wrapper.run_docs(doc)
        assert doc.output_data().title() == "My Title"
        assert doc.output_data().as_text() == "This is the content."

YAML = """filterargs:
  abc: xyz
  foo: 5
"""

def test_yamlargs_filterargs():
    with wrap() as wrapper:
        doc = Doc("example.txt|yamlargs|filterargs",
                wrapper,
                [],
                contents = "%s\n---\r\nThis is the content." % YAML,
                )

        wrapper.run_docs(doc)

        output = doc.output_data().as_text()
        assert "abc: xyz" in output
        assert "foo: 5" in output

        wrapper = Wrapper()
        doc = Doc("example.txt|yamlargs|filterargs",
                wrapper,
                [],
                contents = "%s\n---\r\nThis is the content." % YAML,
                )

        wrapper.run_docs(doc)

        output = doc.output_data().as_text()
        assert "abc: xyz" in output
        assert "foo: 5" in output

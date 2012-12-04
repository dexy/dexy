from dexy.tests.utils import wrap
from dexy.doc import Doc

# Add New Files

def test_generated_files_not_added_by_default():
    with wrap() as wrapper:
        doc = Doc("generate-data.py|py",
            contents = """with open("abc.txt", "w") as f: f.write("hello")""",
            wrapper=wrapper)
        wrapper.run_docs(doc)
        assert not "Doc:abc.txt" in wrapper.batch.lookup_table

def test_generated_files_added_when_requested():
    with wrap() as wrapper:
        doc = Doc("generate-data.py|py",
            contents = """with open("abc.txt", "w") as f: f.write("hello")""",
            py={"add-new-files" : True},
            wrapper=wrapper)
        wrapper.run_docs(doc)
        assert "Doc:abc.txt" in wrapper.batch.lookup_table

def test_generated_files_added_when_requested_underscore():
    with wrap() as wrapper:
        doc = Doc("generate-data.py|py",
            contents = """with open("abc.txt", "w") as f: f.write("hello")""",
            py={"add_new_files" : True},
            wrapper=wrapper)
        wrapper.run_docs(doc)
        assert "Doc:abc.txt" in wrapper.batch.lookup_table

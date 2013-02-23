from dexy.tests.utils import wrap
from dexy.node import DocNode

# Add New Files - Basic

def test_generated_files_not_added_by_default():
    with wrap() as wrapper:
        doc = DocNode("generate-data.py|py",
            contents = """with open("abc.txt", "w") as f: f.write("hello")""",
            wrapper=wrapper)
        wrapper.run_docs(doc)
        #assert not "Doc:abc.txt" in wrapper.batch.lookup_table

def test_generated_files_added_when_requested():
    with wrap() as wrapper:
        doc = DocNode("generate-data.py|py",
            contents = """with open("abc.txt", "w") as f: f.write("hello")""",
            py={"add-new-files" : True},
            wrapper=wrapper)
        wrapper.run_docs(doc)
        #assert "DocNode:abc.txt" in wrapper.batch.lookup_table

def test_generated_files_added_when_requested_underscore():
    with wrap() as wrapper:
        doc = DocNode("generate-data.py|py",
            contents = """with open("abc.txt", "w") as f: f.write("hello")""",
            py={"add_new_files" : True},
            wrapper=wrapper)
        wrapper.run_docs(doc)
        #assert "DocNode:abc.txt" in wrapper.batch.lookup_table

# Add New Files - Filter by Extension
LATEX = """\
\documentclass{article}
\\title{Hello, World!}
\\begin{document}
\maketitle
Hello!
\end{document}
"""

def test_generated_files_not_added_by_default_latex():
    with wrap() as wrapper:
        doc = DocNode("example.tex|latex",
            contents = LATEX,
            wrapper=wrapper)
        wrapper.run_docs(doc)
        #assert "DocNode:example.tex|latex" in wrapper.batch.lookup_table
        #assert not "DocNode:example.aux" in wrapper.batch.lookup_table
        #assert not "DocNode:example.log" in wrapper.batch.lookup_table
        #assert not "DocNode:example.pdf" in wrapper.batch.lookup_table

def test_generated_files_added_latex():
    with wrap() as wrapper:
        doc = DocNode("example.tex|latex",
            contents = LATEX,
            latex = {'add-new-files' : True},
            wrapper=wrapper)
        wrapper.run_docs(doc)
        #assert "DocNode:example.tex|latex" in wrapper.batch.lookup_table
        #assert "DocNode:example.aux" in wrapper.batch.lookup_table
        #assert "DocNode:example.log" in wrapper.batch.lookup_table
        #assert "DocNode:example.pdf" in wrapper.batch.lookup_table

def test_generated_files_added_latex_log_ext():
    with wrap() as wrapper:
        doc = DocNode("example.tex|latex",
            contents = LATEX,
            latex = {'add-new-files' : '.log'},
            wrapper=wrapper)
        wrapper.run_docs(doc)
        #assert "DocNode:example.tex|latex" in wrapper.batch.lookup_table
        #assert not "DocNode:example.aux" in wrapper.batch.lookup_table
        #assert "DocNode:example.log" in wrapper.batch.lookup_table
        #assert not "DocNode:example.pdf" in wrapper.batch.lookup_table

def test_generated_files_added_latex_log_ext_array():
    with wrap() as wrapper:
        doc = DocNode("example.tex|latex",
            contents = LATEX,
            latex = {'add-new-files' : ['.log']},
            wrapper=wrapper)
        wrapper.run_docs(doc)
        #assert "DocNode:example.tex|latex" in wrapper.batch.lookup_table
        #assert not "DocNode:example.aux" in wrapper.batch.lookup_table
        #assert "DocNode:example.log" in wrapper.batch.lookup_table
        #assert not "DocNode:example.pdf" in wrapper.batch.lookup_table

def test_generated_files_with_additional_filters():
    with wrap() as wrapper:
        doc = DocNode("example.tex|latex",
            contents = LATEX,
            latex = {'add-new-files' : ['.aux'], 'additional-doc-filters' : { '.aux' : 'wc' } },
            wrapper=wrapper)
        wrapper.run_docs(doc)
        #assert "DocNode:example.tex|latex" in wrapper.batch.lookup_table
        #assert "DocNode:example.aux" in wrapper.batch.lookup_table
        #assert "DocNode:example.aux|wc" in wrapper.batch.lookup_table
        #assert not "DocNode:example.log" in wrapper.batch.lookup_table
        #assert not "DocNode:example.pdf" in wrapper.batch.lookup_table

def test_generated_files_with_additional_filters_not_keeping_originals():
    with wrap() as wrapper:
        doc = DocNode("example.tex|latex",
            contents = LATEX,
            latex = {
                'add-new-files' : ['.aux'],
                'additional-doc-filters' : { '.aux' : 'wc' },
                'keep-originals' : False
                },
            wrapper=wrapper)
        wrapper.run_docs(doc)
        #assert "DocNode:example.tex|latex" in wrapper.batch.lookup_table
        #assert not "DocNode:example.aux" in wrapper.batch.lookup_table
        #assert "DocNode:example.aux|wc" in wrapper.batch.lookup_table
        #assert not "DocNode:example.log" in wrapper.batch.lookup_table
        #assert not "DocNode:example.pdf" in wrapper.batch.lookup_table

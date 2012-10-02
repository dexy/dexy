from dexy.doc import Doc
from dexy.doc import PatternDoc
from dexy.tests.utils import TEST_DATA_DIR
from dexy.tests.utils import wrap
import inspect
import os
import shutil

def test_ragel_state_chart_to_image():
    ragel = inspect.cleandoc("""
        %%{
          machine hello_and_welcome;
          main := ( 'h' @ { puts "hello world!" }
                  | 'w' @ { puts "welcome" }
                  )*;
        }%%
          data = 'whwwwwhw'
          %% write data;
          %% write init;
          %% write exec;
        """)
    with wrap() as wrapper:
        doc = Doc("example.rl|rlrbd|dot",
                contents=ragel,
                wrapper=wrapper)
        wrapper.run_docs(doc)

def test_latex_filter_with_unicode():
    with wrap() as wrapper:
        for f in ["test-unicode-latex-jinja.tex", "test-idio.py"]:
            start = os.path.join(TEST_DATA_DIR, f)
            shutil.copyfile(start, f)

        doc = PatternDoc("*.tex|jinja|latex",
                PatternDoc("*.py|idio|pycon|pyg|l", wrapper=wrapper),
                wrapper=wrapper)
        wrapper.run_docs(doc)

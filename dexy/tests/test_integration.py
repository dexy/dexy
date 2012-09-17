from dexy.doc import Doc
from dexy.doc import PatternDoc
from dexy.tests.utils import wrap
import inspect
import os
import shutil

#def test_ragel_state_chart_to_image():
#    ragel = inspect.cleandoc("""
#        %%{
#          machine hello_and_welcome;
#          main := ( 'h' @ { puts "hello world!" }
#                  | 'w' @ { puts "welcome" }
#                  )*;
#        }%%
#          data = 'whwwwwhw'
#          %% write data;
#          %% write init;
#          %% write exec;
#        """)
#    with wrap() as wrapper:
#        doc = Doc("example.rl|rlrbd|dot",
#                contents=ragel,
#                wrapper=wrapper)
#    wrapper.docs = [doc]
#    wrapper.run()

#def test_latex_filter_with_unicode():
#    project_dir = os.path.abspath(os.getcwd())
#    data_dir = "dexy/tests/data"
#    print "project dir is", project_dir
#
#    with wrap() as wrapper:
#        for f in ["test-unicode-latex-jinja.tex", "test-idio.py"]:
#            start = os.path.join(project_dir, data_dir, f)
#            shutil.copyfile(start, f)
#
#        doc = PatternDoc("*.tex|jinja|latex",
#                PatternDoc("*.py|idio|pycon|pyg|l", wrapper=wrapper),
#                wrapper=wrapper)
#        wrapper.docs = [doc]
#        wrapper.run()

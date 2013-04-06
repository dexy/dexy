from dexy.tests.utils import wrap
from dexy.tests.utils import s
import dexy.doc
import dexy.node

def test_ragel_state_chart_to_image():
    ragel = s("""
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
        node = dexy.doc.Doc("example.rl|rlrbd|dot",
                wrapper,
                [],
                contents=ragel)
        wrapper.run_docs(node)

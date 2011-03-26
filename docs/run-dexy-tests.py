import nose
import inspect
import json

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.agile import PythonLexer

py_lexer = PythonLexer()
fm = HtmlFormatter()

loader = nose.loader.TestLoader()
tests = loader.loadTestsFromDir('../tests/')

test_info = {}


for test in tests:
    test_passed = nose.core.run(suite=test)

    for x in dir(test.context):
        xx = test.context.__dict__[x]
        if xx.__class__.__name__ == 'function':
            source = inspect.getsource(xx.__code__)
            html_source = highlight(source, py_lexer, fm)

            if test_passed:
                result = """
<div class="notification success">
     <h5>Success</h5>
      This test suite passes.
</div> """
            else:
                result = """
<div class="notification error">
      <h5>Error</h5>
      This test suite does not pass.
</div> """

            test_info[xx.__name__] = "%s\n%s" % (html_source, result)

f = open("dexy--nose.json", "w")
json.dump(test_info, f)
f.close()


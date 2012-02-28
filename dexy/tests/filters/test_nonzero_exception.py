from dexy.filters.process_filters import DexyScriptErrorException
from dexy.filters.process_filters import ProcessFilter
from dexy.tests.utils import run_dexy
import dexy.commands

TRIGGER_EXCEPTIONS_CONFIG = {
    "." : {
        "@BreakMe.java|java" : { "contents" : """
            public class BreakMe {
                public static void main(String args[]) throws Exception {
                    throw new Exception("yo!");
                }
          }
        """ },
        "@bash.sh|sh" : { "contents" : "exit 1" },
        "@main.c|cfussy" : { "contents" : "" },
        "@bash.sh|shint" : { "contents" : "exit 1" },
        "@bash.sh|shtmp" : { "contents" : "exit 1" },
        "@bash.sh|shinput" : { "contents" : "exit 1", "inputs" : ["input.txt"] },
        "@dot.dot|dot" : { "contents" : "start" },
        "@erlang.erl|escript" : { "contents" : "abc()."},
        "@input.txt" : { "contents" : "this is some input" },
        "@javascript.js|rhino" : { "contents" : "throw me" },
        "@javascript.js|rhinoint" : { "contents" : "throw me" },
        "@lua.lua|lua" : { "contents" : "error()" },
        "@python.py|jython" : { "contents" : "raise Exception()" },
        "@python.py|py" : { "contents" : "raise Exception()" },
        "@python.py|pyinput" : { "contents" : "raise Exception()", "inputs" : ["input.txt"] },
        "@ragel.rl|rlrbd" : { "contents" : "{" },
        "@rstats.R|rout" : { "contents" : "stop()"},
        "@rstats.R|rintbatch" : { "contents" : "stop()"},
        "@package.txt|man" : { "contents" : "jfjdiso" },
        "@ruby.rb|jruby" : { "contents" : "throw"},
        "@ruby.rb|rbinput" : { "contents" : "throw", "inputs" : ["input.txt"]},
        "@ruby.rb|rb" : { "contents" : "throw"}
        }
}

# TODO Come up with examples for these classes which break them.

DONT_KNOW_HOW_TO_TEST = [
"AsciidocFilter",
"CleanSubprocessStdoutFilter",
"CowsaySubprocessStdoutFilter",
"CowthinkSubprocessStdoutFilter",
"LynxDumpFilter",
"NonexistentFilter", #skip
"PandocFilter",
"PexpectReplFilter", #skip
"ProcessFilter", #skip
"RagelRubySubprocessFilter",
"RdConvFilter",
"RedclothFilter",
"RedclothLatexFilter",
"RegetronSubprocessStdoutInputFileFilter",
"SedSubprocessStdoutInputFilter",
"SloccountFilter",
"SubprocessStdoutFilter", #skip
"SubprocessStdoutInputFileFilter", #skip
"SubprocessStdoutInputFilter" #skip
]

def test_run():
    filters = dexy.introspect.filters()
    tested_filter_classes = []

    for doc in run_dexy(TRIGGER_EXCEPTIONS_CONFIG):
        try:
            doc.run()
            if not doc.key() in ["input.txt"]:
                assert False, "expected exception for %s" % doc.key()
        except DexyScriptErrorException:
            tested_filter_alias = doc.filters[-1]
            tested_filter_classes.append(filters[tested_filter_alias])
            assert True

    for filter_class in filters.values():
        is_text_process_filter = issubclass(filter_class, ProcessFilter) and not filter_class.BINARY
        check_return = is_text_process_filter and filter_class.CHECK_RETURN_CODE
        not_tested = not filter_class in tested_filter_classes
        must_test = not filter_class.__name__ in DONT_KNOW_HOW_TO_TEST

        if is_text_process_filter and check_return and not_tested and must_test:
            raise Exception("class %s not tested! aliases: %s" % (filter_class.__name__, ", ".join(filter_class.ALIASES)))

def test_ignore_errors_controller():
    """
    Ensure we can ignore errors by setting the controller-wide param 'ignore' to true.
    """
    args = { "ignore" : True }
    for doc in run_dexy(TRIGGER_EXCEPTIONS_CONFIG, args):
        doc.run()

def test_ignore_errors_document():
    """
    Ensure we can ignore errors by setting 'ignore-errors' to true for each individual document.
    """
    trigger_ignore_exceptions_config = TRIGGER_EXCEPTIONS_CONFIG.copy()

    for k, v in trigger_ignore_exceptions_config['.'].iteritems():
        v['ignore-errors'] = True

    for doc in run_dexy(trigger_ignore_exceptions_config):
        doc.run()

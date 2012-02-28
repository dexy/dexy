from dexy.tests.utils import run_dexy_without_tempdir
from dexy.tests.utils import tempdir

BASIC_CONFIG = {
    "." : {
        "@example.py|py" : { "contents" : "x = 5" }
    }
}

CONFIG_WITH_INPUT_1 = {
    "." : {
        "@example.py|py" : { "contents" : "6*7" },
        "index.txt|jinja" : { "allinputs" : True, "contents" : "The answer is {{ d['example.py|py'] }}" }
    }
}

CONFIG_WITH_INPUT_2 = {
    "." : {
        "@example.py|py" : { "contents" : "6*9" },
        "index.txt|jinja" : { "allinputs" : True, "contents" : "The answer is {{ d['example.py|py'] }}" }
    }
}

def test_basic():
    with tempdir():
        for doc in run_dexy_without_tempdir(BASIC_CONFIG):
            doc.run()
            assert doc.artifacts[-1].source == 'run'

        for doc in run_dexy_without_tempdir(BASIC_CONFIG):
            doc.run()
            assert doc.artifacts[-1].source == 'cache'

def test_inputs():
    with tempdir():
        for doc in run_dexy_without_tempdir(CONFIG_WITH_INPUT_1):
            doc.run()
            assert doc.artifacts[-1].source == 'run'

        for doc in run_dexy_without_tempdir(CONFIG_WITH_INPUT_1):
            doc.run()
            assert doc.artifacts[-1].source == 'cache'

        for doc in run_dexy_without_tempdir(CONFIG_WITH_INPUT_2):
            doc.run()
            assert doc.artifacts[-1].source == 'run'

        for doc in run_dexy_without_tempdir(CONFIG_WITH_INPUT_2):
            doc.run()
            assert doc.artifacts[-1].source == 'cache'

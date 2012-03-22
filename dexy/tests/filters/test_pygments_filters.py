from dexy.tests.utils import run_dexy

TEST_PYGMENTS_LEXER_OPTION_CONFIG = {
        "." : {
            "@code.php|pygments" : {
                "contents" : "1+1",
                "pygments" : { "lexer-startinline" : True }
            }
        }
    }

TEST_IDIO_LEXER_OPTION_CONFIG = {
        "." : {
            "@code.php|idio" : {
                "contents" : "1+1",
                "idio" : { "lexer-startinline" : True }
            }
        }
    }

def test_pygments_filter_recognizes_startinline_as_lexer_option():
    for doc in run_dexy(TEST_PYGMENTS_LEXER_OPTION_CONFIG):
        doc.run()
        assert doc.key() == "code.php|pygments"
        assert """<span class="mi">""" in doc.output()

    TEST_PYGMENTS_LEXER_OPTION_CONFIG["."]["@code.php|pygments"]["pygments"]["lexer-startinline"] = False

    for doc in run_dexy(TEST_PYGMENTS_LEXER_OPTION_CONFIG):
        doc.run()
        assert doc.key() == "code.php|pygments"
        assert not """<span class="mi">""" in doc.output()
        assert """<span class="x">""" in doc.output()

def test_idio_filter_recognizes_startinline_as_lexer_option():
    for doc in run_dexy(TEST_IDIO_LEXER_OPTION_CONFIG):
        doc.run()
        assert doc.key() == "code.php|idio"
        assert """<span class="mi">""" in doc.output()

    TEST_IDIO_LEXER_OPTION_CONFIG["."]["@code.php|idio"]["idio"]["lexer-startinline"] = False

    for doc in run_dexy(TEST_IDIO_LEXER_OPTION_CONFIG):
        doc.run()
        assert doc.key() == "code.php|idio"
        assert not """<span class="mi">""" in doc.output()
        assert """<span class="x">""" in doc.output()

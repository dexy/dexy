from dexy.tests.utils import run_dexy

CONFIG = {
    "." : {
        "@example1.md|markdown" : { "contents" : "[TOC]" },
        "@example2.md|markdown" : { "contents" : "[TOC]", "markdown" : { "toc" : {} } },
        "@example3.md|markdown" : { "contents" : "[TOC]", "markdown" : { "toc" : { "title" : "My Table of Contents" } } },
        "@example4.md|markdown" : { "contents" : "[[wikime]]", "markdown" : { "toc" : {}, "wikilinks" : {} } }
        }
    }

def test_markdown():
    for doc in run_dexy(CONFIG):
        doc.run()
        if doc.key() == "example1.md|markdown":
            assert doc.output() == "<p>[TOC]</p>"
        elif doc.key() == "example2.md|markdown":
            assert doc.output() == """<div class="toc"></div>"""
        elif doc.key() == "example3.md|markdown":
            assert doc.output() == """<div class="toc"><span class="toctitle">My Table of Contents</span></div>"""
        elif doc.key() == "example4.md|markdown":
            assert doc.output() == """<p><a class="wikilink" href="/wikime/">wikime</a></p>"""
        else:
            assert False, "Should not get here."

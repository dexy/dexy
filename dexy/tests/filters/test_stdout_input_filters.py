from dexy.tests.utils import run_dexy

def test_sed_filter():
    config = {
            "@example.sed|sed" : {
                "contents" : "s/e/E/g",
                "allinputs" : True
                },
            "@input.txt" : { "contents" : "hello" }
        }
    for doc in run_dexy({"." : config}):
        doc.run()
        if doc.key().endswith("sed"):
            assert doc.output() == "hEllo"

def test_used_filter():
    config = {
            "@input.txt|used" : {
                "contents" : "hello",
                "inputs" : ["@example.sed"]
                },
            "@example.sed" : { "contents" : "s/e/E/g" },
        }

    for doc in run_dexy({"." : config}):
        doc.run()
        if doc.key().endswith("used"):
            assert doc.output() == "hEllo"

def test_ruby_input_filter():
    script = """
    while line = gets
        puts "you typed: #{line}"
    end
    """
    config = {
            "@script.rb|rbinput" : {
                "contents" : script,
                "inputs" : ["@input.txt"]
                },
            "@input.txt" : { "contents" : "hello" },
        }

    for doc in run_dexy({"." : config}):
        doc.run()
        if doc.key().endswith("input"):
            assert doc.output() == "you typed: hello\n"

def test_python_input_filter():
    script = """import sys
for line in sys.stdin:
    line = line.strip()
    print "You said '%s', that took '%d' characters!" % (line, len(line))"""
    config = {
            "@script.py|pyinput" : {
                "contents" : script,
                "inputs" : ["@input.txt"]
                },
            "@input.txt" : { "contents" : "hello" },
        }

    for doc in run_dexy({"." : config}):
        doc.run()
        if doc.key().endswith("input"):
            assert doc.output() == "You said 'hello', that took '5' characters!\n"

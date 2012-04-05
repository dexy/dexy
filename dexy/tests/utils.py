from StringIO import StringIO
from dexy.controller import Controller
from dexy.document import Document
from modargs import args as modargs
import dexy.commands
import dexy.introspect
import os
import re
import shutil
import sys
import tempfile

class tempdir():
    def __enter__(self):
        self.tempdir = tempfile.mkdtemp()
        self.location = os.path.abspath(os.curdir)
        os.chdir(self.tempdir)

    def __exit__(self, type, value, traceback):
        os.chdir(self.location)
        shutil.rmtree(self.tempdir)

class divert_stdout():
    def __enter__(self):
        self.old_stdout = sys.stdout
        self.my_stdout = StringIO()
        sys.stdout = self.my_stdout
        return self.my_stdout

    def __exit__(self, type, value, traceback):
        sys.stdout = self.old_stdout
        self.my_stdout.close()

class divert_stderr():
    def __enter__(self):
        self.old_stderr = sys.stderr
        self.my_stderr = StringIO()
        sys.stderr = self.my_stderr
        return self.my_stderr

    def __exit__(self, type, value, traceback):
        sys.stderr = self.old_stderr
        self.my_stderr.close()

def controller_args(additional_args = {}):
    fn = modargs.function_for(dexy.commands, "dexy")
    args = modargs.determine_kwargs(fn)
    args.update(additional_args)

    if not os.path.exists(args['logsdir']):
        os.mkdir(args['logsdir'])
    if not os.path.exists(args['artifactsdir']):
        os.mkdir(args['artifactsdir'])

    return args

def run_dexy_without_tempdir(config_dict, additional_args={}):
    if not hasattr(Document, 'filter_list'):
        Document.filter_list = dexy.introspect.filters()
    
    args = controller_args(additional_args)

    c = Controller(args)
    c.config = config_dict
    c.process_config()

    [doc.setup() for doc in c.docs]

    for doc in c.docs:
        yield(doc)

    c.persist()

def set_filter_list(additional_filters):
    filters = dexy.introspect.filters()
    for filter_class in additional_filters:
        for a in filter_class.ALIASES:
            filters[a] = filter_class
    Document.filter_list = filters

def run_dexy(config_dict, additional_args={}, use_tempdir=True):
    with tempdir():
        for doc in run_dexy_without_tempdir(config_dict, additional_args):
            yield(doc)

def assert_output(key, contents, output, args={}):
    args["contents"] = contents
    config = { "." : { ("@%s" % key) : args } }
    for doc in run_dexy(config):
        doc.run()
        print doc.key() + "======="
        print doc.logstream.getvalue()
        print "'%s'" % doc.output()
        print "'%s'" % output
        assert doc.output() == output

def assert_in_output(key, contents, output, args={}):
    args["contents"] = contents
    config = { "." : { ("@%s" % key) : args } }
    for doc in run_dexy(config):
        doc.run()
        print doc.key() + "======="
        print doc.logstream.getvalue()
        print "'%s'" % doc.output()
        print "'%s'" % output
        assert output in doc.output()

def assert_matches_output(key, contents, output):
    config = { "." : { ("@%s" % key) : { "contents" : contents } } }
    for doc in run_dexy(config):
        doc.run()
        print doc.key() + "======="
        print doc.logstream.getvalue()
        print "'%s'" % doc.output()
        print "'%s'" % output
        assert re.match(output, doc.output())

from StringIO import StringIO
from dexy.controller import Controller
from dexy.document import Document
from modargs import args as modargs
import dexy.introspect
import os
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

def run_dexy_without_tempdir(config_dict, additional_args={}):
    Document.filter_list = dexy.introspect.filters()

    fn = modargs.function_for(dexy.commands, "dexy")
    args = modargs.determine_kwargs(fn)
    args.update(additional_args)

    if not os.path.exists(args['logsdir']):
        os.mkdir(args['logsdir'])
    if not os.path.exists(args['artifactsdir']):
        os.mkdir(args['artifactsdir'])

    c = Controller(args)
    c.config = config_dict
    c.process_config()

    [doc.setup() for doc in c.docs]

    for doc in c.docs:
        yield(doc)

    c.persist()

def run_dexy(config_dict, additional_args={}, use_tempdir=True):
    with tempdir():
        for doc in run_dexy_without_tempdir(config_dict, additional_args):
            yield(doc)

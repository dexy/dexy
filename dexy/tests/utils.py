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

def run_dexy(config_dict, additional_args={}):
    with tempdir():
        Document.filter_list = dexy.introspect.filters()

        fn = modargs.function_for(dexy.commands, "dexy")
        args = modargs.determine_kwargs(fn)
        args.update(additional_args)

        os.mkdir(args['logsdir'])
        os.mkdir(args['artifactsdir'])

        c = Controller(args)
        c.config = config_dict
        c.process_config()

        [doc.setup() for doc in c.docs]

        for doc in c.docs:
            yield(doc)

from StringIO import StringIO
import sys
import os
import shutil
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


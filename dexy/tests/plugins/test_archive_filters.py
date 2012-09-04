from dexy.tests.utils import temprun
import tarfile
import os
from dexy.doc import Doc

def test_unprocessed_directory_archive_filter():
    with temprun() as runner:
        with open("abc.txt", "w") as f:
            f.write('this is abc')

        with open("def.txt", "w") as f:
            f.write('this is def')

        doc = Doc("archive.tgz|tgzdir", contents="ignore", tgzdir={'dir' : '.'}, runner=runner)
        runner.docs = [doc]
        runner.run()
        runner.report()

        assert os.path.exists("output/archive.tgz")
        with tarfile.open("output/archive.tgz", mode="r:gz") as tar:
            names = tar.getnames()
            assert "./abc.txt" in names
            assert "./def.txt" in names

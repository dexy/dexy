from dexy.tests.utils import wrap
import tarfile
import os
from dexy.doc import Doc

def test_unprocessed_directory_archive_filter():
    with wrap() as wrapper:
        with open("abc.txt", "w") as f:
            f.write('this is abc')

        with open("def.txt", "w") as f:
            f.write('this is def')

        doc = Doc("archive.tgz|tgzdir", contents="ignore", tgzdir={'dir' : '.'}, wrapper=wrapper)
        wrapper.docs = [doc]
        wrapper.run()
        wrapper.report()

        assert os.path.exists("output/archive.tgz")
        with tarfile.open("output/archive.tgz", mode="r:gz") as tar:
            names = tar.getnames()
            assert "./abc.txt" in names
            assert "./def.txt" in names

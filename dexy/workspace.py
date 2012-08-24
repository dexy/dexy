import dexy.doc
import shutil
import os

class Local(object):
    """
    Class that handles workspace for where filters can actually run.

    For now, use this to also encapsulate canonical file information for artifacts.
    """
    def __init__(self, artifact):
        self.artifact = artifact
        self.root_dir = "artifacts"

    def tmp_dir(self):
        return os.path.join(self.root_dir, self.artifact.metadata.hashstring)

    def create_working_dir(self, populate=False):
        tmpdir = self.tmp_dir()
        shutil.rmtree(tmpdir, ignore_errors=True)
        os.mkdir(tmpdir)

        if populate:
            for key, doc in self.artifact.runner.completed.iteritems():
                if isinstance(doc, dexy.doc.Doc):
                    filename = os.path.join(tmpdir, doc.name)
                    doc.output().output_to_file(filename)

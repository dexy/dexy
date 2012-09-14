from dexy.filter import DexyFilter
import tarfile
import zipfile
import os

class UnprocessedDirectoryArchiveFilter(DexyFilter):
    """
    Create a tgz archive containing the original (unprocessed) files in a directory.
    """
    OUTPUT_EXTENSIONS = [".tgz"]
    ALIASES = ['tgzdir']

    def process(self):
        parent_dir = self.result().parent_dir()
        subdir = self.args()['dir']
        dir_to_archive = os.path.join(parent_dir, subdir)
        af = self.output_filepath()
        with tarfile.open(af, mode="w:gz") as tar:
            for fn in os.listdir(dir_to_archive):
                fp = os.path.join(dir_to_archive, fn)
                self.log.debug("Adding file %s to archive %s" % (fp, af))
                tar.add(fp, arcname=os.path.join(subdir, fn))

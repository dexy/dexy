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
    FRAGMENT = False

    def process(self):
        parent_dir = self.output().parent_dir()
        subdir = self.args()['dir']
        dir_to_archive = os.path.join(parent_dir, subdir)
        af = self.output_filepath()
        tar = tarfile.open(af, mode="w:gz")
        for fn in os.listdir(dir_to_archive):
            fp = os.path.join(dir_to_archive, fn)
            self.log.debug("Adding file %s to archive %s" % (fp, af))
            tar.add(fp, arcname=os.path.join(subdir, fn))
        tar.close()

class ArchiveFilter(DexyFilter):
    """
    Creates a .tgz archive of all input documents.

    The use-short-names option will store documents under their short
    (canonical) filenames.
    """
    OUTPUT_EXTENSIONS = [".tgz"]
    ALIASES = ['archive', 'tgz']
    FRAGMENT = False

    def open_archive(self):
        self.archive = tarfile.open(self.output_filepath(), mode="w:gz")

    def add_to_archive(self, filepath, archivename):
        self.archive.add(filepath, arcname=archivename)

    def process(self):
        self.open_archive()

        # Place files in the archive within a directory with the same name as the archive.
        dirname = self.output().baserootname()

        # Figure out whether to use short names or longer, unambiguous names.
        use_short_names = self.args().get('use-short-names', False)

        for doc in self.processed():
            if not doc.output().is_cached():
                raise Exception("File not on disk.")

            # Determine what this file's name within the archive should be.
            if use_short_names:
                arcname = doc.output().name
            else:
                arcname = doc.output().long_name()
            arcname = os.path.join(self.input().relative_path_to(arcname))
            arcname = os.path.join(dirname, arcname)

            # Add file to archive
            self.add_to_archive(doc.output().storage.data_file(), arcname)

        # Save the archive
        self.archive.close()

class ZipArchiveFilter(ArchiveFilter):
    """
    Creates a .zip archive of all input documents.

    The use-short-names option will store documents under their short
    (canonical) filenames.
    """
    OUTPUT_EXTENSIONS = [".zip"]
    ALIASES = ['zip']

    def open_archive(self):
        self.archive = zipfile.ZipFile(self.output_filepath(), mode="w")

    def add_to_archive(self, filepath, archivename):
        self.archive.write(filepath, arcname=archivename)

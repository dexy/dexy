from dexy.filter import DexyFilter
import tarfile
import zipfile
import os

class UnprocessedDirectoryArchiveFilter(DexyFilter):
    """
    Create a .tgz archive containing the unprocessed files in a directory.
    """
    aliases = ['tgzdir']
    _settings = {
            'output' : True,
            'output-extensions' : ['.tgz'],
            'dir' : ("Directory in which to output the archive.", '')
            }

    def process(self):
        parent_dir = self.output_data.parent_dir()
        subdir = self.setting('dir')
        dir_to_archive = os.path.join(parent_dir, subdir)
        af = self.output_filepath()
        tar = tarfile.open(af, mode="w:gz")
        for fn in os.listdir(dir_to_archive):
            fp = os.path.join(dir_to_archive, fn)
            self.log_debug("Adding file %s to archive %s" % (fp, af))
            tar.add(fp, arcname=os.path.join(subdir, fn))
        tar.close()

class ArchiveFilter(DexyFilter):
    """
    Creates a .tgz archive of all input documents.

    The use-short-names option will store documents under their short
    (canonical) filenames.
    """
    aliases = ['archive', 'tgz']
    _settings = {
            'output' : True,
            'output-extensions' : ['.tgz'],
            'use-short-names' : ("Whether to use short, potentially non-unique names within the archive.", False),
            }

    def open_archive(self):
        self.archive = tarfile.open(self.output_filepath(), mode="w:gz")

    def add_to_archive(self, filepath, archivename):
        self.archive.add(filepath, arcname=archivename)

    def process(self):
        self.open_archive()

        # Place files in the archive within a directory with the same name as the archive.
        dirname = self.output_data.baserootname()

        # Figure out whether to use short names or longer, unambiguous names.
        use_short_names = self.setting("use-short-names")

        for doc in self.doc.walk_input_docs():
            if not doc.output_data().is_cached():
                raise Exception("File not on disk.")

            # Determine what this file's name within the archive should be.
            if use_short_names:
                arcname = doc.output_data().name
            else:
                arcname = doc.output_data().long_name()
            arcname = os.path.join(self.input_data.relative_path_to(arcname))
            arcname = os.path.join(dirname, arcname)

            # Add file to archive
            self.add_to_archive(doc.output_data().storage.data_file(), arcname)

        # Save the archive
        self.archive.close()

class ZipArchiveFilter(ArchiveFilter):
    """
    Creates a .zip archive of all input documents.

    The use-short-names option will store documents under their short
    (canonical) filenames.
    """
    aliases = ['zip']
    _settings = {
            'output-extensions' : ['.zip']
            }

    def open_archive(self):
        self.archive = zipfile.ZipFile(self.output_filepath(), mode="w")

    def add_to_archive(self, filepath, archivename):
        self.archive.write(filepath, arcname=archivename)

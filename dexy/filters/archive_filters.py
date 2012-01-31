from dexy.dexy_filter import DexyFilter
import os
import tarfile
import zipfile

class UnprocessedDirectoryArchiveFilter(DexyFilter):
    """
    Create a tgz archive containing the original (unprocessed) files in a directory.
    """
    OUTPUT_EXTENSIONS = [".tgz"]
    ALIASES = ['tgzdir']
    BINARY = True
    FINAL = True

    def process(self):
        dirname = os.path.dirname(self.artifact.name)
        tgz_dir = os.path.join(dirname, self.artifact.args['dir'])

        af = self.artifact.filepath()
        tar = tarfile.open(af, mode="w:gz")

        for fn in os.listdir(tgz_dir):
            fp = os.path.join(tgz_dir, fn)
            self.artifact.log.debug("Adding file %s to archive %s." % (fp, af))
            tar.add(fp, arcname=os.path.join(self.artifact.args['dir'], fn))

        tar.close()

class ArchiveFilter(DexyFilter):
    """
    Creates a .tgz archive of all input documents.

    The use-short-names option will store documents under their short
    (canonical) filenames.
    """
    OUTPUT_EXTENSIONS = [".tgz"]
    ALIASES = ['archive', 'tgz']
    BINARY = True
    FINAL = True

    def process(self):
        if self.artifact.args.has_key('use-short-names'):
            use_short_names = self.artifact.args['use-short-names']
        else:
            use_short_names = False

        af = self.artifact.filepath()
        tar = tarfile.open(af, mode="w:gz")

        # Place files in the archive within a directory with the same name as the archive
        dirname = os.path.splitext(os.path.basename(self.artifact.name))[0]

        for k, a in self.artifact.inputs().items():
            fn = a.filepath()
            if not os.path.exists(fn):
                raise Exception("File %s does not exist!" % fn)
            if use_short_names:
                arcname = a.canonical_filename()
            else:
                arcname = a.long_canonical_filename()

            arcname = os.path.join(self.artifact.relative_path_to_input(a), os.path.basename(arcname))
            arcname = os.path.join(dirname, arcname)

            self.artifact.log.debug("Adding file %s to archive %s as %s" % (fn, af, arcname))
            tar.add(fn, arcname=arcname)
        tar.close()

class ZipArchiveFilter(DexyFilter):
    """
    Creates a .zip archive of all input documents.

    The use-short-names option will store documents under their short
    (canonical) filenames.
    """
    OUTPUT_EXTENSIONS = [".zip"]
    ALIASES = ['zip']
    BINARY = True
    FINAL = True

    def process(self):
        if self.artifact.args.has_key('use-short-names'):
            use_short_names = self.artifact.args['use-short-names']
        else:
            use_short_names = False
        af = self.artifact.filepath()
        zf = zipfile.ZipFile(af, mode="w")
        for k, a in self.artifact.inputs().items():
            fn = a.filepath()
            if not os.path.exists(fn):
                raise Exception("File %s does not exist!" % fn)
            if use_short_names:
                arcname = a.canonical_filename()
            else:
                arcname = a.long_canonical_filename()
            self.artifact.log.debug("Adding file %s to archive %s." % (fn, af))
            zf.write(fn, arcname=arcname)
        zf.close()


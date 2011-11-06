from dexy.reporter import Reporter
import datetime
import os
import shutil
import tarfile

class TarzipOutputReporter(Reporter):
    """
    Reporter which creates a .tgz of all output files. Follows same naming
    conventions as OutputReporter.
    """
    SUBDIR_NAME = "dexy-output"

    def run(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        report_filename = os.path.join(self.logsdir, "output-%s.tgz" % timestamp)
        tar = tarfile.open(report_filename, mode="w:gz")

        self.load_batch_artifacts()
        for artifact in self.artifacts.values():
            if (artifact.is_last and artifact.final) or artifact.additional:
                arcname = os.path.join(self.SUBDIR_NAME, artifact.canonical_filename())
                tar.add(artifact.filepath(), arcname=arcname)

        tar.close()
        shutil.copyfile(report_filename, os.path.join(self.logsdir, "output-latest.tgz"))

class InSituReporter(Reporter):
    """
    InSitu Reporter creates files directly in your project. Useful for using
    dexy to create files like README files which need to live in a certain
    place in your project. Templates should have a different file extension
    than the final file. InSitu Reporter will not overwrite existing files,
    delete any previously generated files before running this.
    """
    ALLREPORTS = False
    def run(self):
        self.load_batch_artifacts()
        for artifact in self.artifacts.values():
            if (artifact.is_last and artifact.final) or artifact.additional:
                fn = artifact.canonical_filename()
                if os.path.exists(fn):
                    print "InSituReporter not overwriting existing file", fn, "please delete this file before running InSitu reporter"
                else:
                    artifact.write_to_file(fn)

class OutputReporter(Reporter):
    """
    Saves dexy-processed files in a directory under their canonical filenames.
    Tries to be smart about which files you actually care about and want to
    see. See LongOutputReporter if you want to see everything (with uglier names).
    """
    REPORTS_DIR = 'output'

    def run(self):
        self.create_reports_dir(self.REPORTS_DIR)
        self.load_batch_artifacts()
        for artifact in self.artifacts.values():
            if (artifact.is_last and artifact.final) or artifact.additional:
                fn = artifact.canonical_filename()
                fp = os.path.join(self.REPORTS_DIR, fn)
                if os.path.exists(fp):
                    self.log.warn("two or more final artifacts have canonical path %s" % fp)
                    self.log.warn("most recent is %s" % artifact.key)
                else:
                    self.log.debug("saving %s to %s" % (artifact.key, fn))
                artifact.write_to_file(fp)

class LongOutputReporter(Reporter):
    """
    Saves all dexy-processed files in a directory using unique filenames.
    """
    REPORTS_DIR = 'output-long'
    def run(self):
        self.create_reports_dir(self.REPORTS_DIR)
        self.load_batch_artifacts()
        for artifact in self.artifacts.values():
            if artifact.is_last:
                fn = artifact.long_canonical_filename()
                fp = os.path.join(self.REPORTS_DIR, fn)
                artifact.write_to_file(fp)

from dexy.reporter import Reporter
import datetime
import os
import shutil
import tarfile

class SourceReporter(Reporter):
    """
    Saves dexy-processed files in a directory under their canonical filenames.
    Tries to be smart about which files you actually care about and want to
    see. See LongOutputReporter if you want to see everything (with uglier names).
    """

    def run(self):
        reports_dir = os.path.join(self.logsdir, "batch-source-%05d" % self.batch_id)
        self.create_reports_dir(reports_dir)

        self.load_batch_artifacts()
        for artifact in self.artifacts.values():
            if artifact.initial:
                fp = os.path.join(reports_dir, artifact.name)
                artifact.write_to_file(fp)

        print "source files saved in", reports_dir

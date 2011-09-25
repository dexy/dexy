from dexy.reporter import Reporter
import datetime
import os
import shutil
import tarfile

class TarzipOutputReporter(Reporter):
    """Reporter which creates a .tgz of all output files."""
    OUTPUT_DIR = "logs"
    DEFAULT = False

    def run(self):
        # TODO craete output dir if it doesn't exist
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        report_filename = os.path.join(self.OUTPUT_DIR, "output-%s.tgz" % timestamp)
        tar = tarfile.open(report_filename, mode="w:gz")
        subdir_name = "dexy-output"

        for doc in self.controller.docs:
            artifact = doc.final_artifact()

            if artifact.final:
                arcname = os.path.join(subdir_name, artifact.canonical_filename())
                tar.add(artifact.filepath(), arcname=arcname)

            for k, a in artifact._inputs.items():
                if not a:
                    print "no artifact exists for key", k
                else:
                    if a.additional and a.final:
                        if not a.is_complete():
                            a.state = 'complete'
                            a.save()
                            arcname = os.path.join(subdir_name, a.canonical_filename())
                            tar.add(a.filepath(), arcname=arcname)

        tar.close()
        shutil.copyfile(report_filename, "output-latest.tgz")

class InSituReporter(Reporter):
    """This is the InSitu Reporter"""
    DEFAULT = False

    def run(self):
        for doc in self.controller.docs:
            artifact = doc.final_artifact()

            fn = artifact.canonical_filename()

            if artifact.final:
                if os.path.exists(fn):
                    print "InSituReporter not overwriting existing file", fn
                else:
                    artifact.write_to_file(fn)

            for k, a in artifact._inputs.items():
                if not a:
                    print "no artifact exists for key", k
                else:
                    if a.additional and a.final:
                        if not a.is_complete():
                            a.state = 'complete'
                            a.save()
                        fn = a.canonical_filename()
                        if not os.path.exists(fn):
                            a.write_to_file(fn)

class OutputReporter(Reporter):
    """This is the OutputReporter"""

    REPORTS_DIR = 'output'
    def run(self):
        shutil.rmtree(self.REPORTS_DIR, ignore_errors=True)
        for doc in self.controller.docs:
            artifact = doc.final_artifact()

            fn = artifact.canonical_filename()
            fp = os.path.join(self.REPORTS_DIR, fn)

            if artifact.final:
                artifact.write_to_file(fp)

            for k, a in artifact._inputs.items():
                if not a:
                    print "no artifact exists for key", k
                else:
                    if a.additional and a.final:
                        if not a.is_complete():
                            a.state = 'complete'
                            a.save()
                        fn = a.canonical_filename()
                        fp = os.path.join(self.REPORTS_DIR, fn)
                        a.write_to_file(fp)

class LongOutputReporter(Reporter):
    """This is the LongOutputReporter"""

    REPORTS_DIR = 'output-long'
    def run(self):
        shutil.rmtree(self.REPORTS_DIR, ignore_errors=True)
        for doc in self.controller.docs:
            artifact = doc.final_artifact()

            fn = artifact.long_canonical_filename()
            fp = os.path.join(self.REPORTS_DIR, fn)

            if not artifact.is_complete():
                artifact.state = 'complete'
                artifact.save()

            artifact.write_to_file(fp)

            for k, a in artifact._inputs.items():
                if not a:
                    print "no artifact exists for key", k
                else:
                    fn = a.canonical_filename()
                    fp = os.path.join(self.REPORTS_DIR, fn)
                    a.write_to_file(fp)

from dexy.reporter import Reporter
import shutil
import os

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
                if a.additional and a.final:
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

            artifact.write_to_file(fp)

            for k, a in artifact._inputs.items():
                fn = a.canonical_filename()
                fp = os.path.join(self.REPORTS_DIR, fn)
                a.write_to_file(fp)

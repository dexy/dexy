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

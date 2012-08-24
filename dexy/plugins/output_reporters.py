from dexy.reporter import Reporter
from dexy.doc import Doc
import os

class OutputReporter(Reporter):
    ALIASES = ['output']
    REPORTS_DIR = 'output'

    def run(self, runner):
        self.create_reports_dir(self.REPORTS_DIR)
        for key, task in runner.completed.iteritems():
            if isinstance(task, Doc):
                doc = task
                fp = os.path.join(self.REPORTS_DIR, doc.final_artifact.name)
                doc.output().output_to_file(fp)

class LongOutputReporter(Reporter):
    ALIASES = ['long']
    REPORTS_DIR = 'output-long'

    def run(self, runner):
        self.create_reports_dir(self.REPORTS_DIR)
        for key, task in runner.completed.iteritems():
            if isinstance(task, Doc):
                doc = task
                fp = os.path.join(self.REPORTS_DIR, doc.final_artifact.long_name())
                doc.output().output_to_file(fp)

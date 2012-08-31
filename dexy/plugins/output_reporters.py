from dexy.doc import Doc
from dexy.reporter import Reporter
import os

class OutputReporter(Reporter):
    ALIASES = ['output']
    REPORTS_DIR = 'output'

    def run(self, runner):
        self.create_reports_dir(self.REPORTS_DIR)
        for task in runner.registered:
            if isinstance(task, Doc):
                doc = task
                fp = os.path.join(self.REPORTS_DIR, doc.final_artifact.name)

                parent_dir = os.path.dirname(fp)
                if not os.path.exists(parent_dir):
                    os.makedirs(os.path.dirname(fp))

                doc.output().output_to_file(fp)

class LongOutputReporter(Reporter):
    ALIASES = ['long']
    REPORTS_DIR = 'output-long'

    def run(self, runner):
        self.create_reports_dir(self.REPORTS_DIR)
        for task in runner.registered:
            if isinstance(task, Doc):
                doc = task
                fp = os.path.join(self.REPORTS_DIR, doc.final_artifact.long_name())

                parent_dir = os.path.dirname(fp)
                if not os.path.exists(parent_dir):
                    os.makedirs(os.path.dirname(fp))

                doc.output().output_to_file(fp)

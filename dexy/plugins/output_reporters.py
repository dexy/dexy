from dexy.doc import Doc
from dexy.reporter import Reporter
import os

class OutputReporter(Reporter):
    ALIASES = ['output']
    REPORTS_DIR = 'output'

    def run(self, wrapper):
        self.create_reports_dir(self.REPORTS_DIR)
        for doc in wrapper.registered_docs():
            fp = os.path.join(self.REPORTS_DIR, doc.output().name)

            parent_dir = os.path.dirname(fp)
            if not os.path.exists(parent_dir):
                os.makedirs(os.path.dirname(fp))

            doc.output().output_to_file(fp)

class LongOutputReporter(Reporter):
    ALIASES = ['long']
    REPORTS_DIR = 'output-long'

    def run(self, wrapper):
        self.create_reports_dir(self.REPORTS_DIR)
        for doc in wrapper.registered_docs():
            fp = os.path.join(self.REPORTS_DIR, doc.output().long_name())

            parent_dir = os.path.dirname(fp)
            if not os.path.exists(parent_dir):
                os.makedirs(os.path.dirname(fp))

            doc.output().output_to_file(fp)

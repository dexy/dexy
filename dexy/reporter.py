class Reporter(object):
    REPORTS_DIR = None
    DEFAULT = True # run this reporter by default

    def run(self, controller, log):
        pass

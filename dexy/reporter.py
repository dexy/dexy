class Reporter(object):
    REPORTS_DIR = None
    DEFAULT = True # run this reporter by default

    def __init__(self, controller):
        self.controller = controller
        self.log = self.controller.log

    def run(self):
        pass

from dexy.reporter import Reporter
from ordereddict import OrderedDict
import os

class Runner(object):
    """
    Class that stores run state.
    """
    def __init__(self, **args):
        self.completed = OrderedDict()
        self.args = args
        self.artifacts_dir = args.get('artifacts_dir', 'artifacts')
        self.logs_dir = args.get('logs_dir', 'logs')
        self.reports_dirs = ['output', 'output-long']

    def run(self, *tasks):
        """
        Convenience method to run one or more tasks/docs.
        """
        for task in tasks:
            print "running task", task.key
            for t in task:
                if hasattr(t, 'key'):
                    print "running t", t.key
                else:
                    print "running t", t
                t(self)
                if hasattr(t, 'logstream'):
                    print t.logstream.getvalue()

    def setup(self):
        """
        Create any necessary directories. Do other admin before we run filters.
        """
        if not os.path.exists(self.artifacts_dir):
            os.mkdir(self.artifacts_dir)

    def append(self, doc):
        """
        Appends a new doc to the ordered dict of already completed docs.
        """
        self.completed[doc.key] = doc

    def report(self, *reporters):
        """
        Runs reporters. Either runs reporters which have been passed in or, if
        none, then runs all available reporters which have ALLREPORTS set to
        true.
        """
        if len(reporters) == 0:
            reporters = [c() for c in Reporter.plugins if c.ALLREPORTS]

        for reporter in reporters:
            reporter.run(self)

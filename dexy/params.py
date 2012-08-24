import os

class RunParams(object):
    """
    Class containing parameter values for a Dexy run.
    """
    def __init__(self, **kwargs):
        # Default Values
        self.artifacts_dir = 'artifacts'
        self.log_dir = 'logs'
        self.log_file = 'dexy.log'
        self.reports = ['output']
        self.log_level = 'DEBUG'
        self.config_file = '.dexy'
        self.db_file = os.path.join(self.log_dir, 'dexy.sqlite3')

        for key, value in kwargs.iteritems():
            if not hasattr(self, key):
                raise Exception("no default for %s" % key)

            setattr(self, key, value)

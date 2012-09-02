import os

class RunParams(object):
    """
    Class containing parameter values for a Dexy run.
    """
    def __init__(self, **kwargs):
        # Default Values
        self.artifacts_dir = 'artifacts'
        self.config_file = '.dexy'
        self.db_alias = 'sqlite3'
        self.db_file = os.path.join(self.artifacts_dir, 'dexy.sqlite3')
        self.log_dir = 'logs'
        self.log_file = 'dexy.log'
        self.log_path = os.path.join(self.log_dir, self.log_file)
        self.log_level = 'DEBUG'
        self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.reports = ['output']

        for key, value in kwargs.iteritems():
            if not hasattr(self, key):
                raise Exception("no default for %s" % key)

            setattr(self, key, value)

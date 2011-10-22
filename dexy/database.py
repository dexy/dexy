class Database(object):
    """
    The Database class stores metadata around dexy batches/runs. This metadata
    is used for reporting and can be used as a version history of the documents
    you process with dexy.
    The database can also be used to parallelize/distribute the processing of
    dexy runs and to store ctime/mtime/inode data to speed up cache detection.
    """

    def __init__(self, **kwargs):
        raise Exception("not implemented")

    def append_artifact(self, artifact):
        self.append_artifacts([artifact])

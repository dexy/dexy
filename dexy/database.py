import csv
import os
from dexy.constants import Constants

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

    def persist(self):
        raise Exception("not implemented")

    def next_batch_id(self):
        raise Exception("not implemented")

    def next_batch_order(self, batch_id):
        raise Exception("not implemented")

    def append(self, artifact):
        raise Exception("not implemented")

    def update_artifact(self, artifact):
        raise Exception("not implemented")

    def references_for_batch_id(self, batch_id=None):
        raise Exception("not implemented")


import csv
import os
from dexy.constants import Constants
import dexy.database

class CsvDatabase(dexy.database.Database):
    """
    The Database class stores metadata around dexy batches/runs. This metadata
    is used for reporting and can be used as a version history of the documents
    you process with dexy.
    The database can also be used to parallelize/distribute the processing of
    dexy runs and to store ctime/mtime/inode data to speed up cache detection.
    """
    FIELD_NAMES = ['id', 'batch_id', 'batch_order', 'hashstring'] + Constants.ARTIFACT_HASH_WHITELIST

    def __init__(self, logsdir=Constants.DEFAULT_LDIR, dbfile=Constants.DEFAULT_DBFILE):
        if not logsdir:
            logsdir = ""
        filename = os.path.join(logsdir, dbfile)
        self.filename = filename
        self.max_batch_orders = {}
        self.max_batch_id = 0
        self.db = []

        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                data = csv.DictReader(f, self.FIELD_NAMES)
                firstrow = True
                for row in data:
                    if firstrow:
                        # skip header row
                        firstrow = False
                    else:
                        # load data into memory
                        self.db.append(row)

                        # Calculate max batch id
                        row_batch_id = row['batch_id']
                        if row_batch_id == '':
                            row_batch_id = 0
                        else:
                            row_batch_id = int(row_batch_id)

                        if row_batch_id > self.max_batch_id:
                            self.max_batch_id = row_batch_id

    def persist(self):
        with open(self.filename, 'wb') as f:
            writer = csv.DictWriter(f, self.FIELD_NAMES, lineterminator="\n")
            writer.writerow(dict(zip(self.FIELD_NAMES, self.FIELD_NAMES))) # writeheader not in python 2.6
            writer.writerows(self.db)

    def next_batch_id(self):
        self.max_batch_id += 1
        return self.max_batch_id

    def next_batch_order(self, batch_id):
        if self.max_batch_orders.has_key(batch_id):
            self.max_batch_orders[batch_id] += 1
        else:
            self.max_batch_orders[batch_id] = 1
        return self.max_batch_orders[batch_id]

    def append(self, artifact):
        data = artifact.hash_dict()
        data.update({
            'id' : artifact.unique_key(),
            'batch_id' : artifact.batch_id,
            'batch_order' : self.next_batch_order(artifact.batch_id),
            'hashstring' : artifact.hashstring
        })

        self.db.append(data)

    def update_artifact(self, artifact):
        # find artifact, update any info
        raise Exception("not implemented")

    def references_for_batch_id(self, batch_id=None):
        """
        Return information for a given batch.
        """
        if not batch_id:
            # use most recent batch
            batch_id = self.max_batch_id
        return [r for r in self.db if r['batch_id'] == str(batch_id)]

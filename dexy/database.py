import json
import os

class Database(object):
    """
    The Database class stores metadata around dexy batches/runs. Later, there
    will be multiple implementations available, such as using sqlite for the
    database backend. The batch id and batch ordering information could be used
    to parallelize a dexy run. For now, this information is only used in
    reporting and to check ctime/mtime/inode info between runs.

    """
    def __init__(self, file_name):
        self.file_name = file_name

        if os.path.exists(self.file_name):
            with open(self.file_name, 'r') as f:
                stored_data = json.load(f)
                self.db = stored_data['db']
                self.max_batch_orders = stored_data['max-batch-orders']
                self.max_batch_id = stored_data['max-batch-id']
        else:
            self.db = {}
            self.max_batch_orders = {}
            self.max_batch_id = 0

    def persist(self):
        with open(self.file_name, 'w') as f:
            data_to_store = {
                'db' : self.db,
                'max-batch-orders' : self.max_batch_orders,
                'max-batch-id' : self.max_batch_id
            }
            json.dump(data_to_store, f)

    def validate(self):
        """Validate the max_batch_orders and max_batch_id against the db."""
        raise Exception("not implemented!")

    def next_batch_id(self):
        self.max_batch_id += 1
        return self.max_batch_id

    def next_batch_order(self, batch_id):
        if self.max_batch_orders.has_key(batch_id):
            self.max_batch_orders[batch_id] += 1
        else:
            self.max_batch_orders[batch_id] = 1
        return self.max_batch_orders[batch_id]

    def insert_artifact(self, artifact):
        self.db[artifact.unique_key()] = {
            'batch_id' : artifact.batch_id,
            'batch_order' : self.next_batch_order(artifact.batch_id),
            'document_key' : artifact.document_key,
            'artifact_key' : artifact.key,
            'ctime' : artifact.ctime,
            'mtime' : artifact.mtime,
            'inode' : artifact.inode,
            'hashstring' : artifact.hashstring
        }

    def find_prior_matches(self, artifact):
        return [a for a in self.db.values()
                    if a['document_key'] == artifact.document_key
                    and a['artifact_key'] == artifact.key
                    and a['ctime'] == artifact.ctime
                    and a['mtime'] == artifact.mtime
                    and a['inode'] == artifact.inode]

    def find_last_prior_match(self, artifact):
        matches = self.find_prior_matches(artifact)
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            # more than 1 match
            return matches[0] # TODO actually sort this

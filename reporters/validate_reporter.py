from dexy.reporter import Reporter
import os

class ValidateReporter(Reporter):
    """
    A debugging reporter for checking that all elements in the
    database are also in the cache.
    """
    ALLREPORTS = False # TODO this breaks when repositories have multiple artifact types

    def run(self):
        for row in self.db.all():
            a = self.artifact_class.retrieve(row['hashstring'])
            if not os.path.exists(a.filepath()):
                raise Exception(a.key)
            else:
                print "%5d %s - ok" % (row['batch_id'], a.key)

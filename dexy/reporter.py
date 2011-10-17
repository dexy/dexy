from dexy.constants import Constants
import dexy.artifact
import dexy.database
import dexy.utils
import dexy.introspect

class Reporter(object):
    REPORTS_DIR = None
    LDIR = Constants.DEFAULT_LDIR
    LFILE = Constants.DEFAULT_LFILE
    ACLASS = Constants.DEFAULT_ACLASS
    DBFILE = Constants.DEFAULT_DBFILE
    DBCLASS = Constants.DEFAULT_DBCLASS

    def __init__(self, logsdir=LDIR, logfile=LFILE, artifact_class=ACLASS, batch_id=None,
            dbfile=DBFILE, controller=None, dbclass=DBCLASS):

        self.db = dexy.utils.get_db(dbclass, logsdir=logsdir, dbfile=dbfile)

        if batch_id:
            self.batch_id = batch_id
        else:
            self.batch_id = self.db.max_batch_id

        self.dbfile = dbfile
        self.log = dexy.utils.get_log(self.__class__.__name__, logsdir, logfile)
        self.logfile = logfile
        self.logsdir = logsdir

        if isinstance(artifact_class, str):
            artifact_classes = dexy.introspect.artifact_classes()
            self.artifact_class = artifact_classes[artifact_class]
        elif issubclass(artifact_class, dexy.artifact.Artifact):
            self.artifact_class = artifact_class
        else:
            raise Exception("expected artifact_class to be class name or class, got %s"  % type(artifact_class))

        if controller:
            self.batch_info = controller.batch_info()
        elif self.batch_id:
            self.batch_info = dexy.utils.load_batch_info(self.batch_id, logsdir)
        else:
            print "warning, no batch id could be detected"
            self.batch_info = None

    def load_batch_artifacts(self):
        db = dexy.utils.get_db(logsdir=self.logsdir, dbfile=self.dbfile)
        refs = db.references_for_batch_id(self.batch_id)
        self.batch_refs = refs
        self.artifacts = dict((r['hashstring'], self.artifact_class.retrieve(r['hashstring'])) for r in refs)

    def run(self):
        pass

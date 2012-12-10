from dexy.reporter import Reporter
import os

class OutputReporter(Reporter):
    """
    Creates canonical dexy output with files given short filenames.
    """
    ALIASES = ['output']
    REPORTS_DIR = 'output'

    def write_canonical_doc(self, doc):
        fp = os.path.join(self.REPORTS_DIR, doc.output().name)

        parent_dir = os.path.dirname(fp)
        if not os.path.exists(parent_dir):
            os.makedirs(os.path.dirname(fp))

        self.log.debug("  writing %s to %s" % (doc.key, fp))
        if os.path.exists(fp):
            print "WARNING %s is overwriting file %s. Already written to by:" % (doc.key, fp)
            for tup in self.keys_to_outfiles:
                k, v = tup
                if v == fp:
                    print "    %s" % k
        self.keys_to_outfiles.append((doc.key, fp))

        doc.output().output_to_file(fp)

    def run(self, wrapper):
        self.wrapper=wrapper
        self.set_log()
        self.keys_to_outfiles = []

        self.create_reports_dir()
        for doc in wrapper.batch.docs():
            if doc.canon:
                self.write_canonical_doc(doc)

class LongOutputReporter(Reporter):
    """
    Creates complete dexy output with files given long, unique filenames.
    """
    ALIASES = ['long']
    REPORTS_DIR = 'output-long'

    def run(self, wrapper):
        self.wrapper=wrapper
        self.set_log()
        self.create_reports_dir()
        for doc in wrapper.batch.docs():
            fp = os.path.join(self.REPORTS_DIR, doc.output().long_name())

            parent_dir = os.path.dirname(fp)
            if not os.path.exists(parent_dir):
                os.makedirs(os.path.dirname(fp))

            self.log.debug("  writing %s to %s" % (doc.key, fp))
            doc.output().output_to_file(fp)

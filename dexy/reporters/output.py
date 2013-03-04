from dexy.reporter import Reporter
import os

class OutputReporter(Reporter):
    """
    Creates canonical dexy output with files given short filenames.
    """
    ALIASES = ['output']
    _SETTINGS = {
            'dir' : 'output'
            }

    def write_canonical_doc(self, doc):
        fp = os.path.join(self.setting('dir'), doc.output().name)

        if fp in self.locations:
            print "WARNING overwriting file", fp
        else:
            self.locations[fp] = []
        self.locations[fp].append(doc.key)

        parent_dir = os.path.dirname(fp)
        try:
            os.makedirs(parent_dir)
        except os.error:
            pass

        self.log.debug("  writing %s to %s" % (doc.key, fp))

        doc.output().output_to_file(fp)

    def run(self, wrapper):
        self.wrapper=wrapper
        self.set_log()
        self.locations = {}

        self.create_reports_dir()
        for doc in wrapper.batch.docs():
            if doc.is_canonical_output():
                self.write_canonical_doc(doc)

class LongOutputReporter(Reporter):
    """
    Creates complete dexy output with files given long, unique filenames.
    """
    ALIASES = ['long']
    _SETTINGS = {
            'dir' : 'output-long'
            }

    def run(self, wrapper):
        self.wrapper=wrapper
        self.set_log()
        self.create_reports_dir()
        for doc in wrapper.batch.docs():
            fp = os.path.join(self.setting('dir'), doc.output().long_name())

            try:
                os.makedirs(os.path.dirname(fp))
            except os.error:
                pass

            self.log.debug("  writing %s to %s" % (doc.key, fp))
            doc.output().output_to_file(fp)

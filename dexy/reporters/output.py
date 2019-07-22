from dexy.reporter import Reporter
import os

class Output(Reporter):
    """
    Creates canonical dexy output with files given short filenames.
    """
    aliases = ['output']
    _settings = {
            'dir' : 'output'
            }

    def write_canonical_data(self, doc):
        output_name = doc.output_data().output_name()

        if output_name:
            fp = os.path.join(self.setting('dir'), output_name)

            if fp in self.locations:
                self.log_warn("WARNING overwriting file %s" % fp)
            else:
                self.locations[fp] = []
            self.locations[fp].append(doc.key)

            parent_dir = os.path.dirname(fp)
            try:
                os.makedirs(parent_dir)
            except os.error:
                pass

            self.log_debug("  writing %s to %s" % (doc.key, fp))

            doc.output_data().output_to_file(fp)

    def run(self, wrapper):
        self.wrapper=wrapper
        self.locations = {}

        self.remove_reports_dir(self.wrapper, keep_empty_dir=True)
        self.create_reports_dir()
        for doc in list(wrapper.nodes.values()):
            if not doc.key_with_class() in wrapper.batch.docs:
                continue
            if not doc.state in ('ran', 'consolidated'):
                continue
            if not hasattr(doc, 'output_data'):
                continue

            if doc.output_data().is_canonical_output():
                self.write_canonical_data(doc)

class LongOutput(Reporter):
    """
    Creates complete dexy output with files given long, unique filenames.
    """
    aliases = ['long']
    _settings = {
            'default' : False,
            'dir' : 'output-long'
            }

    def run(self, wrapper):
        self.wrapper=wrapper
        self.create_reports_dir()
        for doc in list(wrapper.nodes.values()):
            if not doc.key_with_class() in wrapper.batch.docs:
                continue
            if not doc.state in ('ran', 'consolidated'):
                continue
            if not hasattr(doc, 'output_data'):
                continue

            fp = os.path.join(self.setting('dir'), doc.output_data().long_name())

            try:
                os.makedirs(os.path.dirname(fp))
            except os.error:
                pass

            self.log_debug("  writing %s to %s" % (doc.key, fp))
            doc.output_data().output_to_file(fp)

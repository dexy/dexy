from dexy.plugins.output_reporters import OutputReporter
from jinja2 import Environment
from jinja2 import FileSystemLoader
import os

class WebsiteReporter(OutputReporter):
    ALIASES = ['ws']
    REPORTS_DIR = 'output-site'
    ALLREPORTS = False

    def apply_and_render_template(self, doc, template_doc):
        env = Environment()
        env.loader = FileSystemLoader(template_doc.output().parent_dir())
        template = env.get_template(template_doc.name)

        env_data = {}
        env_data['wrapper'] = self.wrapper
        env_data['page_title'] = doc.args.get('title', doc.name)
        env_data['contents'] = doc.output()
        env_data['navigation'] = {}
        env_data['navigation']['breadcrumbs'] = "..."

        fp = os.path.join(self.REPORTS_DIR, doc.output().name)

        parent_dir = os.path.dirname(fp)
        if not os.path.exists(parent_dir):
            os.makedirs(os.path.dirname(fp))

        template.stream(env_data).dump(fp, encoding="utf-8")

    def run(self, wrapper):
        self.wrapper=wrapper
        self.set_log()
        self.keys_to_outfiles = []

        self.create_reports_dir()

        template_doc = wrapper.tasks['Doc:_template.html']

        for doc in wrapper.registered_docs():
            if doc.canon:
                if doc.final_artifact.ext == ".html":
                    self.apply_and_render_template(doc, template_doc)
                else:
                    self.write_canonical_doc(doc)

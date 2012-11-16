from dexy.plugins.output_reporters import OutputReporter
from jinja2 import Environment
from jinja2 import FileSystemLoader
import dexy.exceptions
import jinja2
import os

class WebsiteReporter(OutputReporter):
    """
    Applies a template to create a website from your dexy output.

    Templates are applied to all files with .html extension which don't already
    contain "<head" or "<body" tags.

    Templates must be named _template.html with no dexy filters applied (TODO relax this)
    """
    ALIASES = ['ws']
    REPORTS_DIR = 'output-site'
    ALLREPORTS = False

    def is_index_page(self, doc):
        fn = doc.output().name
        # TODO index.json only if htmlsections in doc key..
        return fn.endswith("index.html") or fn.endswith("index.json")

    def nav_directories(self):
        directories = {}
        for doc in self.wrapper.registered_docs():
            if self.is_index_page(doc):
                directories[doc.output().parent_dir()] = doc.title()
        return directories

    def apply_and_render_template(self, doc):
        if doc.args.get('ws_template'):
            template_file = doc.args.get('ws_template')
        else:
            template_file = "_template.html"
        template_path = None

        path_elements = doc.output().parent_dir().split(os.sep)
        for i in range(len(path_elements), -1, -1):
            template_path = os.path.join(*(path_elements[0:i] + [template_file]))
            if os.path.exists(template_path):
                self.log.debug("using template %s for %s" % (template_path, doc.key))
                break

        if not template_path:
            raise dexy.exceptions.UserFeedback("no template path for %s" % doc.key)

        env = Environment(undefined=jinja2.StrictUndefined)
        env.loader = FileSystemLoader([".", os.path.dirname(template_path)])
        self.log.debug("loading template at %s" % template_path)
        template = env.get_template(template_path)

        env_data = {}
        env_data['locals'] = locals
        env_data['dict'] = dict
        env_data['isinstance'] = isinstance
        env_data['wrapper'] = self.wrapper
        env_data['page_title'] = doc.title()
        env_data['source'] = doc.name
        env_data['template_source'] = template_path

        env_data['navigation'] = {}

        if self.is_index_page(doc):
            env_data['navigation']['current_index'] = doc.output().parent_dir()
        else:
            env_data['navigation']['current_index'] = None

        env_data['navigation']['directories'] = self.nav_directories()
        env_data['navigation']['pages'] = "..."

        if doc.final_artifact.ext == '.html':
            env_data['content'] = doc.output().as_text()
        else:
            env_data['content'] = doc.output()

        fp = os.path.join(self.REPORTS_DIR, doc.output().name).replace(".json", ".html")

        parent_dir = os.path.dirname(fp)
        if not os.path.exists(parent_dir):
            os.makedirs(os.path.dirname(fp))

        template.stream(env_data).dump(fp, encoding="utf-8")

    def run(self, wrapper):
        self.wrapper=wrapper
        self.set_log()
        self.keys_to_outfiles = []

        self.create_reports_dir()

        for doc in wrapper.registered_docs():
            self.log.debug("Processing doc %s" % doc.key)
            if doc.canon:
                if doc.final_artifact.ext == ".html":
                    has_html_header = any(html_fragment in doc.output().as_text() for html_fragment in ('<html', '<body', '<head'))

                    if has_html_header or not doc.args.get('ws_template', True):
                        self.log.debug("found html tag in output of %s" % doc.key)
                        self.write_canonical_doc(doc)
                    else:
                        self.apply_and_render_template(doc)
                elif doc.final_artifact.ext == '.json' and 'htmlsections' in doc.filters:
                    self.apply_and_render_template(doc)
                else:
                    self.write_canonical_doc(doc)

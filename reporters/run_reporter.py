from dexy.reporter import Reporter
from dexy.utils import ansi_output_to_html
from jinja2 import Environment
from jinja2 import FileSystemLoader
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.web import JavascriptLexer
import datetime
import json
import os
import shutil

class RunReporter(Reporter):
    def run(self):
        report_dir = os.path.join(self.controller.logs_dir, "run-%s" %
                                  datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S"))
        latest_report_dir = os.path.join(self.controller.logs_dir, "run-latest")
        report_filename = os.path.join(report_dir, 'index.html')
        shutil.rmtree(report_dir, ignore_errors=True)

        template_dir = os.path.join(os.path.dirname(__file__), 'run_reporter')
        shutil.copytree(template_dir, report_dir)

        formatter = HtmlFormatter()
        js_lexer = JavascriptLexer()

        for doc in self.controller.docs:
            if len(doc.args) > 0:
                doc.args_html = highlight(json.dumps(doc.args, sort_keys=True, indent=4), js_lexer, formatter)
            for a in doc.artifacts:
                if hasattr(a, 'stdout'):
                    a.stdout_html = ansi_output_to_html(a.stdout)

        env_data = {}
        j = json.dumps(self.controller.config, sort_keys = True, indent=4)
        html = highlight(j, js_lexer, formatter)

        env_data['dexy_config'] = html
        env_data['docs'] = self.controller.docs
        env_data['docs_sorted'] = sorted([d.key() for d in self.controller.docs])
        env_data['controller'] = self.controller

        env = Environment()
        env.loader = FileSystemLoader(os.path.dirname(__file__))
        template = env.get_template('run_reporter_template.html')
        template.stream(env_data).dump(report_filename)

        shutil.rmtree(latest_report_dir, ignore_errors=True)
        shutil.copytree(report_dir, latest_report_dir)

from dexy.reporter import Reporter
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
        self.load_batch_artifacts()

        # Create a directory to hold the report.
        report_dir = os.path.join(self.logsdir, "run-%s" %
                                  datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S"))
        latest_report_dir = os.path.join(self.logsdir, "run-latest")
        report_filename = os.path.join(report_dir, 'index.html')
        shutil.rmtree(report_dir, ignore_errors=True)

        template_dir = os.path.join(os.path.dirname(__file__), 'run_reporter')
        shutil.copytree(template_dir, report_dir)

        formatter = HtmlFormatter()
        js_lexer = JavascriptLexer()

        env_data = {}

        # highlight config
        j = json.dumps(self.batch_info['config'], sort_keys = True, indent=4)
        dexy_config = highlight(j, js_lexer, formatter)

        def highlight_json(d):
            j = json.dumps(d, sort_keys=True, indent=4)
            return highlight(j, js_lexer, formatter)

        env_data['artifacts'] = self.artifacts
        env_data['batch_info'] = self.batch_info
        env_data['dexy_config'] = dexy_config
        env_data['docs'] = self.batch_info['docs']
        env_data['sorted'] = sorted
        env_data['highlight_json'] = highlight_json

        env = Environment()
        env.loader = FileSystemLoader(os.path.dirname(__file__))
        template = env.get_template('run_reporter_template.html')
        template.stream(env_data).dump(report_filename)

        shutil.rmtree(latest_report_dir, ignore_errors=True)
        shutil.copytree(report_dir, latest_report_dir)

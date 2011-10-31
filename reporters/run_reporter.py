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

        def highlight_json(d):
            j = json.dumps(d, sort_keys=True, indent=4)
            return highlight(j, js_lexer, formatter)

        total_artifacts = 0
        base_artifacts = 0
        cached_artifacts = 0
        run_artifacts = 0

        total_elapsed = 0
        total_run_elapsed = 0
        run_time_by_key = {}
        for key, doc in self.batch_info['docs'].iteritems():
            for hashstring, source, elapsed in doc['artifacts']:

                artifact = self.artifacts[hashstring]

                if hasattr(artifact, 'filter_name'):
                    filter_class = artifact.filter_name
                    if not run_time_by_key.has_key(filter_class):
                        run_time_by_key[filter_class] = []

                    elapsed_array = run_time_by_key[filter_class]
                    elapsed_array.append(elapsed)
                    run_time_by_key[filter_class] = elapsed_array

                total_artifacts += 1
                total_elapsed += elapsed

                if not source:
                    base_artifacts += 1
                elif source == 'run':
                    run_artifacts += 1
                    total_run_elapsed += elapsed
                elif source =='cache':
                    cached_artifacts += 1
                else:
                    raise Exception("unknown source %s" % source)

        env_data['total_artifacts'] = total_artifacts
        env_data['base_artifacts'] = base_artifacts
        env_data['cached_artifacts'] = cached_artifacts
        env_data['run_artifacts'] = run_artifacts
        env_data['total_elapsed'] = total_elapsed
        env_data['total_run_elapsed'] = total_run_elapsed
        env_data['run_time_by_key'] = run_time_by_key

        env_data['artifacts'] = self.artifacts
        env_data['batch_id'] = self.batch_id
        env_data['batch_info'] = self.batch_info
        env_data['dexy_config'] = highlight_json(self.batch_info['config'])
        env_data['docs'] = self.batch_info['docs']
        env_data['highlight_json'] = highlight_json

        env_data['sorted'] = sorted
        env_data['float'] = float
        env_data['min'] = min
        env_data['max'] = max
        env_data['len'] = len
        env_data['sum'] = sum

        env = Environment()
        env.loader = FileSystemLoader(os.path.dirname(__file__))
        template = env.get_template('run_reporter_template.html')
        template.stream(env_data).dump(report_filename)

        shutil.rmtree(latest_report_dir, ignore_errors=True)
        shutil.copytree(report_dir, latest_report_dir)

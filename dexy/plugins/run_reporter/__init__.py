from dexy.reporter import Reporter
from jinja2 import Environment
from jinja2 import FileSystemLoader
import datetime
import operator
import os
import shutil

class RunReporter(Reporter):
    """
    Returns info about a dexy run.
    """
    ALLREPORTS = True
    ALIASES = ['run']

    def run(self, wrapper):
        latest_report_dir = os.path.join(wrapper.log_dir, 'run-latest')

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        report_dir = os.path.join(wrapper.log_dir, "run-%s" % timestamp)
        report_filename = os.path.join(report_dir, 'index.html')

        # Remove any existing directory (unlikely)
        shutil.rmtree(report_dir, ignore_errors=True)

        # Copy template files (e.g. .css files)
        template_dir = os.path.join(os.path.dirname(__file__), 'files')
        shutil.copytree(template_dir, report_dir)

        env_data = {}

        env_data['float'] = float
        env_data['len'] = len
        env_data['sorted'] = sorted
        env_data['hasattr'] = hasattr
        env_data['dict'] = dict
        env_data['isinstance'] = isinstance
        env_data['attrgetter'] = operator.attrgetter

        env_data['batch'] = wrapper.batch

        env_data['docs'] = wrapper.batch.docs()
        env_data['wrapper'] = wrapper

        env = Environment()
        env.loader = FileSystemLoader(os.path.dirname(__file__))
        template = env.get_template('template.html')

        template.stream(env_data).dump(report_filename, encoding="utf-8")

        # Copy this to run-latest
        # TODO symlink instead?
        shutil.rmtree(latest_report_dir, ignore_errors=True)
        shutil.copytree(report_dir, latest_report_dir)

from dexy.reporter import Reporter
from jinja2 import Environment
from jinja2 import FileSystemLoader
import json
import os

class D3Graph(Reporter):
    """
    Generates a tree graph using d3.js
    """
    aliases = ['d3tree']
    _settings = {
            'dir' : 'd3tree',
            'in-cache-dir' : True,
            'filename' : 'd3tree.js',
            "run-for-wrapper-states" : ["ran", "checked", "error"]
            }

    def node_info(self, node):
        inputs_and_children = node.inputs + node.children
        return {
                'name' : node.key,
                'contents': [self.node_info(n) for n in inputs_and_children]
                }

    def run(self, wrapper):
        self.wrapper = wrapper
        self.remove_reports_dir(wrapper)
        self.copy_template_files()

        env_data = self.run_plugins()

        graphs = {
                "name" : "",
                "contents" : [self.node_info(node) for node in wrapper.roots]
                }

        env_data['graph_json'] = json.dumps(graphs)

        env = Environment()
        env.loader = FileSystemLoader(os.path.dirname(__file__))
        template = env.get_template('template.js')

        template.stream(env_data).dump(self.report_file(), encoding="utf-8")


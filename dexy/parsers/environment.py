from dexy.parser import Parser
from dexy.utils import parse_json
#from dexy.utils import parse_yaml
#import dexy.exceptions
#import re

class JsonEnvironment(Parser):
    """
    Loads environment variables from a JSON file.
    """
    ALIASES = ['dexy-env.json']

    def build_ast(self, parent_dir, config_text):
        config = parse_json(config_text)
        if not self.wrapper.environment.has_key(parent_dir):
            self.wrapper.environment[parent_dir] = {}
        self.wrapper.environment[parent_dir].update(config)

class PythonEnvironment(Parser):
    """
    Loads environment variables from a python script.
    """
    ALIASES = ['dexy-env.py']

    def build_ast(self, parent_dir, config_text):
        exec config_text
        config = {}
        skip = ('config', 'skip', 'self', 'parent_dir', 'config_text')
        for k, v in locals().iteritems():
            if not k in skip:
                config[k] = v
        if not self.wrapper.environment.has_key(parent_dir):
            self.wrapper.environment[parent_dir] = {}
        self.wrapper.environment[parent_dir].update(config)

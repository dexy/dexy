from dexy.parser import Parser
from dexy.utils import parse_json

class Environment(Parser):
    """
    Parent class for environment parsers.
    """
    @classmethod
    def parse_environment_from_text(klass, text):
        pass

    def parse(self, parent_dir, config_text):
        config = self.parse_environment_from_text(config_text)
        self.ast.environment_for_directory.append((parent_dir, config,))

class JsonEnvironment(Environment):
    """
    Loads environment variables from a JSON file.
    """
    aliases = ['dexy-env.json']

    @classmethod
    def parse_environment_from_text(klass, text):
        return parse_json(text)

class PythonEnvironment(Environment):
    """
    Loads environment variables from a python script.
    """
    aliases = ['dexy-env.py']

    @classmethod
    def parse_environment_from_text(klass, text):
        env = {}
        skip = ('env', 'skip', 'self', 'parent_dir', 'env_text')

        exec(text)

        for k, v in locals().items():
            if not k in skip:
                env[k] = v
        return env

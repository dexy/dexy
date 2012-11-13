from dexy.reporter import Reporter
from jinja2 import FileSystemLoader
from jinja2 import Environment

class WebsiteReporter(Reporter):
    ALLREPORTS = False
    ALIASES = ['ws']

    def run(self, wrapper):
        pass

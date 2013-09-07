from dexy.filter import DexyFilter
from dexy.utils import parse_yaml
import re

class YamlargsFilter(DexyFilter):
    """
    Strips YAML metadata from top of file and adds this to args for every artifact in current doc.
    """
    aliases = ['yamlargs']

    def process_text(self, input_text):
        regex = "\r?\n---\r?\n"
        if re.search(regex, input_text):
            self.log_debug("Found yaml content.")
            raw_yamlargs, content = re.split(regex, input_text)
            yamlargs = parse_yaml(raw_yamlargs)
            self.log_debug("Adding yaml: %s" % yamlargs)
            self.add_runtime_args(yamlargs)
            return content
        else:
            self.log_debug("No yaml content found.")
            return input_text

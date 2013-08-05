from dexy.reporter import Reporter
from dexy.doc import Doc
from jinja2 import Environment
from jinja2 import FileSystemLoader
import operator
import os
import random
import shutil

def link_to_doc(node):
    return """&nbsp;<a href="#%s">&darr; doc info</a>""" % node.output_data().websafe_key()

def link_to_doc_if_doc(node):
    if isinstance(node, Doc):
        return link_to_doc(node)
    else:
        return ""

class RunReporter(Reporter):
    """
    Returns info about a dexy run.
    """
    aliases = ['run']
    _settings = {
            'in-cache-dir' : True,
            'dir' : 'run',
            'filename' : 'index.html',
            'default' : True,
            "run-for-wrapper-states" : ["ran", "error"]
            }

    def run(self, wrapper):
        self.wrapper = wrapper
        self.remove_reports_dir(wrapper)

        # Copy template files (e.g. .css files)
        # TODO don't need to copy this each time - can just overwrite index.html
        template_dir = os.path.join(os.path.dirname(__file__), 'files')
        shutil.copytree(template_dir, self.report_dir())
        self.write_safety_file()

        # If not too large, copy the log so it can be viewed in HTML
        self.wrapper.flush_logs()
        if os.path.getsize(self.wrapper.log_path()) < 500000:
            with open(self.wrapper.log_path(), 'r') as f:
                log_contents = f.read()
        else:
            log_contents = "Log file is too large to include in HTML. Look in %s" % self.wrapper.log_path()

        env_data = {}

        env_data['attrgetter'] = operator.attrgetter
        env_data['dict'] = dict
        env_data['float'] = float
        env_data['hasattr'] = hasattr
        env_data['isinstance'] = isinstance
        env_data['len'] = len
        env_data['sorted'] = sorted
        env_data['dir'] = dir

        env_data['wrapper'] = wrapper
        env_data['batch'] = wrapper.batch
        env_data['log_contents'] = log_contents

        env_data['enumerate'] = enumerate

        def printable_args(args):
            return dict((k, v) for k, v in args.iteritems() if not k in ('contents', 'wrapper'))

        def print_children(node, indent=0, extra=""):
            rand_id = random.randint(10000000,99999999)
            spaces = " " * 4 * indent
            nbspaces = "&nbsp;" * 4 * indent
            content = ""

            node_div = """%s<div data-toggle="collapse" data-target="#%s">%s%s%s%s</div>"""
            node_div_args = (spaces, rand_id, nbspaces, extra,
                    node.key_with_class(), link_to_doc_if_doc(node),)

            content += node_div % node_div_args
            content += """  %s<div id="%s" class="collapse">""" % (spaces, rand_id)

            for child in list(node.inputs):
                if not "Artifact" in child.__class__.__name__:
                    content += print_children(child, indent+1, "&rarr;")

            for child in node.children:
                if not "Artifact" in child.__class__.__name__:
                    content += print_children(child, indent+1)

            content += "  %s</div>" % spaces
            return content 

        env_data['print_children'] = print_children
        env_data['printable_args'] = printable_args

        env = Environment()
        env.loader = FileSystemLoader(os.path.dirname(__file__))
        template = env.get_template('template.html')

        template.stream(env_data).dump(self.report_file(), encoding="utf-8")

from dexy.parser import AbstractSyntaxTree
from dexy.parser import Parser
from dexy.utils import parse_json
from dexy.utils import parse_yaml
import dexy.exceptions
import re

class YamlFileParser(Parser):
    ALIASES = ["docs.yaml"]

    def build_ast(self, input_text):
        def parse_key_mapping(mapping):
            for task_key, v in mapping.iteritems():
                # v is a sequence whose members may be children or kwargs
                if not v:
                    raise dexy.exceptions.UserFeedback("Empty doc config for %s" % task_key)

                if hasattr(v, 'keys'):
                    raise dexy.exceptions.UserFeedback("You passed a dict to %s, please pass a sequence" % task_key)

                for element in v:
                    if hasattr(element, 'keys'):
                        # This is a dict of length 1
                        kk = element.keys()[0]
                        vv = element[kk]

                        if isinstance(vv, list):
                            # This is a sequence. It probably represents a
                            # child task but if starts with 'args' or if it
                            # matches a filter alias for the parent doc, then
                            # it is nested complex kwargs.
                            if kk == "args" or (kk in task_key.split("|")):
                                # nested complex kwargs
                                for vvv in vv:
                                    ast.add_task_info(task_key, **vvv)

                            else:
                                # child task. we note the dependency and
                                # recurse to process the child.
                                ast.add_dependency(task_key, kk)
                                parse_key_mapping(element)

                        else:
                            # This is a key:value argument for this task
                            ast.add_task_info(task_key, **element)

                    else:
                        # This is a child task with no args, we only have to
                        # note the dependency.
                        ast.add_dependency(task_key, element)

        def parse_keys(data):
            if hasattr(data, 'keys'):
                parse_key_mapping(data)
            elif isinstance(data, basestring):
                ast.add_task_info(data)
            elif isinstance(data, list):
                for element in data:
                    parse_keys(element)
            else:
                raise Exception("invalid input %s" % data)

        ast = AbstractSyntaxTree()
        config = parse_yaml(input_text)
        parse_keys(config)
        return ast

class TextFileParser(Parser):
    ALIASES = ["docs.txt"]

    def build_ast(self, input_text):
        ast = AbstractSyntaxTree()
        for line in input_text.splitlines():
            line = line.strip()

            # Throw away comments.
            if "#" in line:
                if line.startswith("#"):
                    line = ''
                else:
                    line = line.split("#", 0)

            if not re.match("^\s*$", line):
                if "{" in line:
                    # We have a task + some JSON arguments
                    key, raw_args = line.split("{", 1)
                    key = key.strip()
                    kwargs = parse_json("{" + raw_args)
                else:
                    key = line
                    kwargs = {}

                ast.add_task_info(key, **kwargs)

                # all tasks already in the ast are children
                for child_key in ast.lookup_table.keys():
                    ast.add_dependency(key, child_key)

        return ast

class OriginalDexyParser(Parser):
    ALIASES = ["docs.json", ".dexy"]

    def build_ast(self, input_text):
        data = parse_json(input_text)

        ast = AbstractSyntaxTree()
        for task_key, v in data.iteritems():
            ast.add_task_info(task_key)

            for kk, vv in v.iteritems():
                if kk == 'depends':
                    for child_key in vv:
                        ast.add_dependency(task_key, child_key)
                else:
                    task_kwargs = {kk : vv}
                    ast.add_task_info(task_key, **task_kwargs)

        def children_for_allinputs(priority=None):
            children = []
            for k, v in ast.lookup_table.iteritems():
                if 'allinputs' in v:
                    if priority:
                        k_priority = v.get('priority', 10)
                        if k_priority < priority:
                            children.append(k)
                else:
                    children.append(k)
            return children

        # Make another pass to implement 'allinputs'
        for task_key, kwargs in ast.lookup_table.iteritems():
            if kwargs.get('allinputs', False):
                priority = kwargs.get('priority')
                for child_key in children_for_allinputs(priority):
                    ast.add_dependency(task_key, child_key)

        return ast

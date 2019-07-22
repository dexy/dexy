from dexy.parser import Parser
from dexy.utils import parse_json
from dexy.utils import parse_yaml
import dexy.exceptions
import re

class Yaml(Parser):
    """
    Parses YAML configs.
    """
    aliases = ["dexy.yaml", "docs.yaml"]

    def parse(self, directory, input_text):
        def parse_key_mapping(mapping):
            for original_node_key, v in mapping.items():
                # handle things which aren't nodes
                if original_node_key == 'defaults':
                    self.ast.default_args_for_directory.append((directory, v,))
                    continue

                # handle nodes
                original_file = original_node_key.split("|")[0]

                orig_exists = self.file_exists(directory, original_file) 
                star_in_key = "*" in original_node_key
                dot_in_key = "." in original_node_key
                pipe_in_key = "|" in original_node_key

                treat_key_as_bundle_name = not orig_exists and not star_in_key and not dot_in_key and not pipe_in_key

                if treat_key_as_bundle_name:
                    node_key = original_node_key
                else:
                    node_key = self.wrapper.join_dir(directory, original_node_key)

                # v is a sequence whose members may be children or kwargs
                if not v:
                    raise dexy.exceptions.UserFeedback("Empty doc config for %s" % node_key)

                if hasattr(v, 'keys'):
                    raise dexy.exceptions.UserFeedback("You passed a dict to %s, please pass a sequence" % node_key)

                siblings = []
                for element in v:
                    if hasattr(element, 'keys'):
                        # This is a dict of length 1
                        kk = list(element.keys())[0]
                        vv = element[kk]

                        if isinstance(vv, list):
                            # This is a sequence. It probably represents a
                            # child task but if starts with 'args' or if it
                            # matches a filter alias for the parent doc, then
                            # it is nested complex kwargs.
                            if kk == "args" or (kk in node_key.split("|")):
                                # nested complex kwargs
                                for vvv in vv:
                                    self.ast.add_node(node_key, **vvv)

                            else:
                                # child task. we note the dependency, add
                                # dependencies on prior siblings, and recurse
                                # to process the child.
                                self.ast.add_dependency(node_key, self.wrapper.join_dir(directory, kk))

                                if self.wrapper.siblings:
                                    for s in siblings:
                                        self.ast.add_dependency(self.wrapper.join_dir(directory, kk), s)
                                    siblings.append(self.wrapper.join_dir(directory, kk))

                                parse_key_mapping(element)

                        else:
                            # This is a key:value argument for this task
                            self.ast.add_node(node_key, **element)

                    else:
                        # This is a child task with no args, we only have to
                        # note the dependencies
                        self.ast.add_dependency(node_key, self.wrapper.join_dir(directory, element))
                        if self.wrapper.siblings:
                            for s in siblings:
                                self.ast.add_dependency(self.wrapper.join_dir(directory, element), s)
                            siblings.append(self.wrapper.join_dir(directory, element))

        def parse_keys(data, top=False):
            if hasattr(data, 'keys'):
                parse_key_mapping(data)
            elif isinstance(data, str):
                self.ast.add_node(self.wrapper.join_dir(directory, data))
            elif isinstance(data, list):
                if top:
                    self.ast.root_nodes_ordered = True
                for element in data:
                    parse_keys(element)
            else:
                raise Exception("invalid input %s" % data)

        config = parse_yaml(input_text)
        parse_keys(config, top=True)

class TextFile(Parser):
    """
    parses plain text configs
    """
    aliases = ["dexy.txt", "docs.txt"]

    def parse(self, directory, input_text):
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

                node_key = self.wrapper.join_dir(directory, key)
                self.ast.add_node(node_key, **kwargs)
                # all tasks already in the ast are children
                for child_key in list(self.ast.lookup_table.keys()):
                    child_node_key = self.wrapper.join_dir(directory, child_key)
                    self.ast.add_dependency(node_key, child_node_key)

class Original(Parser):
    """
    parses JSON config files like .dexy
    """
    aliases = ["dexy.json", "docs.json", ".dexy"]

    def parse(self, directory, input_text):
        data = parse_json(input_text)

        for task_key, v in data.items():
            self.ast.add_node(self.wrapper.join_dir(directory, task_key))

            for kk, vv in v.items():
                if kk == 'depends':
                    for child_key in vv:
                        self.ast.add_dependency(self.wrapper.join_dir(directory, task_key), self.wrapper.join_dir(directory, child_key))
                else:
                    task_kwargs = {kk : vv}
                    self.ast.add_node(self.wrapper.join_dir(directory, task_key), **task_kwargs)

        def children_for_allinputs(priority=None):
            children = []
            for k, v in self.ast.lookup_table.items():
                if 'allinputs' in v:
                    if priority:
                        k_priority = v.get('priority', 10)
                        if k_priority < priority:
                            children.append(k)
                else:
                    children.append(k)
            return children

        # Make another pass to implement 'allinputs'
        for task_key, kwargs in self.ast.lookup_table.items():
            if kwargs.get('allinputs', False):
                priority = kwargs.get('priority')
                for child_key in children_for_allinputs(priority):
                    # These keys are already adjusted for directory.
                    self.ast.add_dependency(task_key, child_key)

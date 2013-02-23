from dexy.parser import Parser
from dexy.utils import parse_json
from dexy.utils import parse_yaml
import dexy.exceptions
import os
import re

class YamlFileParser(Parser):
    """
    Parses YAML configs.
    """
    ALIASES = ["dexy.yaml", "docs.yaml"]

    def build_ast(self, directory, input_text):
        def parse_key_mapping(mapping):
            for original_task_key, v in mapping.iteritems():
                if original_task_key == 'defaults':
                    self.ast.default_args.append((directory, v,))
                    continue

                original_file = original_task_key.split("|")[0]
                if not os.path.exists(self.join_dir(directory, original_file)) and not "*" in original_task_key and not "." in original_task_key and not "|" in original_task_key:
                    self.wrapper.log.debug("treating %s as a bundle name, not prepending directory %s" % (original_task_key, directory))
                    task_key = original_task_key
                else:
                    task_key = self.join_dir(directory, original_task_key)

                # v is a sequence whose members may be children or kwargs
                if not v:
                    raise dexy.exceptions.UserFeedback("Empty doc config for %s" % task_key)

                if hasattr(v, 'keys'):
                    raise dexy.exceptions.UserFeedback("You passed a dict to %s, please pass a sequence" % task_key)

                siblings = []
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
                                    self.ast.add_task_info(task_key, **vvv)

                            else:
                                # child task. we note the dependency, add
                                # dependencies on prior siblings, and recurse
                                # to process the child.
                                self.ast.add_dependency(task_key, self.join_dir(directory, kk))

                                if self.wrapper.siblings:
                                    for s in siblings:
                                        self.ast.add_dependency(self.join_dir(directory, kk), s)
                                    siblings.append(self.join_dir(directory, kk))

                                parse_key_mapping(element)

                        else:
                            # This is a key:value argument for this task
                            self.ast.add_task_info(task_key, **element)

                    else:
                        # This is a child task with no args, we only have to
                        # note the dependencies
                        self.ast.add_dependency(task_key, self.join_dir(directory, element))
                        if self.wrapper.siblings:
                            for s in siblings:
                                self.ast.add_dependency(self.join_dir(directory, element), s)
                            siblings.append(self.join_dir(directory, element))

        def parse_keys(data, top=False):
            if hasattr(data, 'keys'):
                parse_key_mapping(data)
            elif isinstance(data, basestring):
                self.ast.add_task_info(self.join_dir(directory, data))
            elif isinstance(data, list):
                if top:
                    self.ast.root_nodes_ordered = True
                for element in data:
                    parse_keys(element)
            else:
                raise Exception("invalid input %s" % data)

        config = parse_yaml(input_text)
        parse_keys(config, top=True)

class TextFileParser(Parser):
    """
    parses plain text configs
    """
    ALIASES = ["dexy.txt", "docs.txt"]

    def build_ast(self, directory, input_text):
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

                self.ast.add_task_info(self.join_dir(directory, key), **kwargs)
                # all tasks already in the ast are children
                for child_key in self.ast.lookup_table.keys():
                    self.ast.add_dependency(self.join_dir(directory, key), self.join_dir(directory, child_key))

class OriginalDexyParser(Parser):
    """
    parses JSON config files like .dexy
    """
    ALIASES = ["dexy.json", "docs.json", ".dexy"]

    def build_ast(self, directory, input_text):
        data = parse_json(input_text)

        for task_key, v in data.iteritems():
            self.ast.add_task_info(self.join_dir(directory, task_key))

            for kk, vv in v.iteritems():
                if kk == 'depends':
                    for child_key in vv:
                        self.ast.add_dependency(self.join_dir(directory, task_key), self.join_dir(directory, child_key))
                else:
                    task_kwargs = {kk : vv}
                    self.ast.add_task_info(self.join_dir(directory, task_key), **task_kwargs)

        def children_for_allinputs(priority=None):
            children = []
            for k, v in self.ast.lookup_table.iteritems():
                if 'allinputs' in v:
                    if priority:
                        k_priority = v.get('priority', 10)
                        if k_priority < priority:
                            children.append(k)
                else:
                    children.append(k)
            return children

        # Make another pass to implement 'allinputs'
        for task_key, kwargs in self.ast.lookup_table.iteritems():
            if kwargs.get('allinputs', False):
                priority = kwargs.get('priority')
                for child_key in children_for_allinputs(priority):
                    # These keys are already adjusted for directory.
                    self.ast.add_dependency(task_key, child_key)

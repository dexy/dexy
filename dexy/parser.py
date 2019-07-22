import copy
import dexy.doc
import dexy.exceptions
import dexy.plugin
import posixpath

class AbstractSyntaxTree():
    def __init__(self, wrapper):
        self.wrapper = wrapper

        self.root_nodes_ordered = False

        self.lookup_table = {}
        self.tree = []

        # Lists of (directory, settings) tuples
        self.default_args_for_directory = []
        self.environment_for_directory = []

    def all_inputs(self):
        """
        Returns a set of all node keys identified as inputs of some other
        element.
        """
        all_inputs = set()
        for kwargs in list(self.lookup_table.values()):
            inputs = kwargs['inputs']
            all_inputs.update(inputs)
        return all_inputs

    def clean_tree(self):
        """
        Removes tasks which are already represented as inputs (tree should
        only contain root nodes).
        """
        treecopy = copy.deepcopy(self.tree)
        all_inputs = self.all_inputs()
        for task in treecopy:
            if task in all_inputs:
                self.tree.remove(task)

    def add_node(self, node_key, **kwargs):
        """
        Adds the node and its kwargs to the tree and lookup table
        """
        node_key = self.wrapper.standardize_key(node_key)

        if not node_key in self.tree:
            self.tree.append(node_key)

        if not node_key in self.lookup_table:
            self.lookup_table[node_key] = {}

        self.lookup_table[node_key].update(kwargs)

        if not 'inputs' in self.lookup_table[node_key]:
            self.lookup_table[node_key]['inputs'] = []

        self.clean_tree()
        return node_key

    def add_dependency(self, node_key, input_node_key):
        """
        Adds input_node_key to list of inputs for node_key (both nodes are
        also added to tree).
        """
        node_key = self.add_node(node_key)
        input_node_key = self.add_node(input_node_key)

        if not node_key == input_node_key:
            self.lookup_table[node_key]['inputs'].append(input_node_key)

        self.clean_tree()

    def args_for_node(self, node_key):
        """
        Returns the dict of kw args for a node
        """
        node_key = self.wrapper.standardize_key(node_key)
        args = copy.deepcopy(self.lookup_table[node_key])
        del args['inputs']
        return args

    def inputs_for_node(self, node_key):
        """
        Returns the list of inputs for a node
        """
        node_key = self.wrapper.standardize_key(node_key)
        return self.lookup_table[node_key]['inputs']

    def calculate_default_args_for_directory(self, path):
        dir_path = posixpath.dirname(posixpath.abspath(path))
        default_kwargs = {}

        for d, args in self.default_args_for_directory:
            if posixpath.abspath(d) in dir_path:
                default_kwargs.update(args)

        return default_kwargs

    def calculate_environment_for_directory(self, path):
        dir_path = posixpath.dirname(posixpath.abspath(path))
        env = {}

        for d, args in self.environment_for_directory:
            if posixpath.abspath(d) in dir_path:
                env.update(args)

        return env

    def walk(self):
        """
        Creates Node objects for all elements in tree. Returns a list of root
        nodes and a dict of all nodes referenced by qualified keys.
        """
        if self.wrapper.nodes:
            self.log_warn("nodes are not empty: %s" % ", ".join(self.wrapper.nodes))
        if self.wrapper.roots:
            self.log_warn("roots are not empty: %s" % ", ".join(self.wrapper.roots))

        def create_dexy_node(key, *inputs, **kwargs):
            """
            Stores already created nodes in nodes dict, if called more than
            once for the same key, returns already created node.
            """
            if not key in self.wrapper.nodes:
                alias, pattern = self.wrapper.qualify_key(key)
                node_environment = self.calculate_environment_for_directory(pattern)
                
                kwargs_with_defaults = self.calculate_default_args_for_directory(pattern)
                kwargs_with_defaults.update(kwargs)
                kwargs_with_defaults.update({'environment' : node_environment })

                self.wrapper.log.debug("creating node %s" % alias)
                node = dexy.node.Node.create_instance(
                        alias,
                        pattern,
                        self.wrapper,
                        inputs,
                        **kwargs_with_defaults)

                if node.inputs:
                    self.wrapper.log.debug("inputs are %s" % ", ".join(i.key for i in node.inputs))

                self.wrapper.nodes[key] = node

                for child in node.children:
                    self.wrapper.nodes[child.key_with_class()] = child

            return self.wrapper.nodes[key]

        def parse_item(key):
            inputs = self.inputs_for_node(key)
            kwargs = self.args_for_node(key)
            self.wrapper.log.debug("parsing item %s" % key)
            self.wrapper.log.debug("  inputs: %s" % ", ".join("%r" % inpt for inpt in inputs))
            self.wrapper.log.debug("  kwargs: %s" % ", ".join("%s: %r" % (k, v) for k, v in kwargs.items()))

            if kwargs.get('inactive') or kwargs.get('disabled'):
                return

            matches_target = self.wrapper.target and key.startswith(self.wrapper.target)
            if not kwargs.get('default', True) and not self.wrapper.full and not matches_target:
                return

            input_nodes = [parse_item(i) for i in inputs if i]
            input_nodes = [i for i in input_nodes if i]
    
            return create_dexy_node(key, *input_nodes, **kwargs)

        for node_key in self.tree:
            root_node = parse_item(node_key)
            if root_node:
                self.wrapper.roots.append(root_node)

class Parser(dexy.plugin.Plugin, metaclass=dexy.plugin.PluginMeta):
    """
    Parse various types of config file.
    """
    aliases = []
    _settings = {}

    def __init__(self, wrapper, ast):
        self.wrapper = wrapper
        self.ast = ast

    def file_exists(self, directory, filename):
        filepath = self.wrapper.join_dir(directory, filename)
        return self.wrapper.file_available(filepath)

    def parse(self, directory, input_text):
        pass

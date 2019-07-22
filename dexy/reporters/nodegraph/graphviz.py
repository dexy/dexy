from dexy.reporter import Reporter

class Graphviz(Reporter):
    """
    Emits a graphviz graph of the network structure.
    """
    aliases = ['graphviz', 'nodegraph']
    _settings = {
            'in-cache-dir' : True,
            'filename' : 'graph.dot',
            "run-for-wrapper-states" : ["ran", "checked", "error"]
            }

    def run(self, wrapper):
        self.wrapper = wrapper
        def print_children(node, indent=0):
            content = []
            content.append(node.key)
            for child in node.children:
                for line in print_children(child, indent+1):
                    content.append(line)
            return content

        def print_inputs(node):
            content = []
            for child in node.inputs:
                content.extend(print_inputs(child))
                content.append("\"%s\" -> \"%s\";" % (node, child))
            return content

        graph = []
        graph.append("digraph G {")
        for node in list(wrapper.nodes.values()):
            graph.extend(print_inputs(node))
        graph.append("}")

        self.create_cache_reports_dir()
        with open(self.report_file(), "w") as f:
            f.write("\n".join(graph))


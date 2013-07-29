from dexy.reporter import Reporter

class NodeGraph(Reporter):
    """
    Emits a graphviz graph of the network structure.
    """
    aliases = ['nodegraph']
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
        for node in wrapper.nodes.values():
            graph.extend(print_inputs(node))
        graph.append("}")

        self.create_cache_reports_dir()
        with open(self.report_file(), "w") as f:
            f.write("\n".join(graph))

class PlainTextGraph(Reporter):
    """
    Emits a plain text graph of the network structure.
    """
    aliases = ['graph']
    _settings = {
            'in-cache-dir' : True,
            'filename' : 'graph.txt',
            "run-for-wrapper-states" : ["ran", "checked"]
            }

    def run(self, wrapper):
        self.wrapper = wrapper

        def print_inputs(node, indent=0):
            content = []

            s = " " * indent * 4
            content.append("%s%s (%s)" % (s, node, node.state))

            for child in list(node.inputs) + node.children:
                content.extend(print_inputs(child, indent+1))
            return content

        graph = []
        for node in wrapper.roots:
            graph.extend(print_inputs(node))

        self.create_cache_reports_dir()
        with open(self.report_file(), "w") as f:
            f.write("\n".join(graph) + "\n")

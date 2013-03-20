from dexy.reporter import Reporter
import os

class NodeGraph(Reporter):
    """
    Emits a graphviz graph of the network structure.
    """
    aliases = ['nodegraph']
    _settings = {
            'filename' : ("Name of file to write output to.", 'graph.txt'),
            'run-on-failed-batch' : True
            }

    def run(self, wrapper):
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
            print node
            graph.extend(print_inputs(node))
        graph.append("}")

        filename = os.path.join(wrapper.log_dir, self.setting('filename'))
        with open(filename, "w") as f:
            f.write("\n".join(graph))

class PlainTextGraph(Reporter):
    """
    Emits a plain text graph of the network structure.
    """
    aliases = ['plaintextgraph']
    _settings = {
            'filename' : ("Name of file to write output to.", 'graph.txt'),
            'run-on-failed-batch' : True
            }

    def run(self, wrapper):
        def print_inputs(node, indent=0):
            content = []
            s = " " * indent * 4
            content.append("%s%s" % (s, node))
            for child in node.inputs:
                content.extend(print_inputs(child, indent+1))
            return content

        graph = []
        for node in wrapper.nodes.values():
            print node
            graph.extend(print_inputs(node))

        filename = os.path.join(wrapper.log_dir, self.setting('filename'))

        with open(filename, "w") as f:
            f.write("\n".join(graph))

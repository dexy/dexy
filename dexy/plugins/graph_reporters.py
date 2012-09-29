from dexy.reporter import Reporter
from dexy.doc import Doc
import subprocess

class GraphReporter(Reporter):
    ALIASES = ['graph', 'dot']

    def run(self, wrapper):
        dotfile = 'dexygraph.dot'

        graph = ["digraph G {"]
        for task in wrapper.registered:
            if isinstance(task, Doc):
                for child in task.children:
                    if isinstance(child, Doc):
                        graph.append("""   "%s" -> "%s";""" % (task.key, child.key))

        graph.append("}")

        with open(dotfile, "w") as f:
            f.write("\n".join(graph))

        command = "dot %s -Tpng -odexygraph.png" % dotfile
        proc = subprocess.Popen(
                   command,
                   shell=True,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT
               )
        proc.communicate()

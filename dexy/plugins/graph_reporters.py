from dexy.reporter import Reporter
from dexy.doc import Doc
import subprocess

class GraphReporter(Reporter):
    ALIASES = ['graph', 'dot']

    def run(self, wrapper):
        dotfile = 'dexygraph.dot'

        graph = ["digraph G {"]
        print wrapper.registered
        for task in wrapper.registered:
            if task.is_doc():
                for child in task.children:
                    if child.is_doc():
                        graph.append("""   "%s" -> "%s";""" % (task.key_with_class(), child.key_with_class()))

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

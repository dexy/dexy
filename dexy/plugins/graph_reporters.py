from dexy.reporter import Reporter
import subprocess
import os

class GraphReporter(Reporter):
    """
    Reporter which prints a graph representation of tree.
    """
    ALIASES = ['graph', 'dot']
    ALLREPORTS = False

    @classmethod
    def write_graph_to_dotfile(klass, wrapper, dotfile):
        with open(dotfile, "w") as f:
            f.write(wrapper.batch.graph)

    @classmethod
    def render_dotfile_to_png(klass, dotfile, pngfile):
        command = "dot %s -Tpng -o%s" % (dotfile, pngfile)
        proc = subprocess.Popen(
                   command,
                   shell=True,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT
               )
        proc.communicate()

    def run(self, wrapper):
        dotfile = os.path.join(wrapper.log_dir, 'dexygraph.dot')
        pngfile = os.path.join(wrapper.log_dir, 'dexygraph.png')

        self.write_graph_to_dotfile(wrapper, dotfile)
        self.render_dotfile_to_png(dotfile, pngfile)
